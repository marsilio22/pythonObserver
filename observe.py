import asyncio
import datetime
from genericpath import exists

from bleak import BleakScanner, BLEDevice, AdvertisementData

timeout_seconds = 60


class MyScanner:
    def temp_hum(self, values: bytearray, battery: int, device: BLEDevice):
        # the H5075 uses three 2-byte values to denote both temp and humidity
        # here we read the whole thing as one number, then divide correctly to read 
        # out the individual values.
        ## TODO: There is something about this that means it doesn't work with negative temperatures. The fix involves something about the following:
        ## https://github.com/theengs/decoder/blob/development/src/devices/H5072_json.h
        ## temp = float(values / 1000) > 0 ? float (values / 10000) : (float(values / 1000) - 8388608) / 10000 * -1
        ## or this
        ## if (values ^ 0x800000) { tempIsNegative = true; values = values ^ 0x800000 }
        
        values = int.from_bytes(values, 'big')
        temp = float(values / 10000)
        hum = float((values % 1000) / 10)

        test = exists("{0}{1}.csv".format(device.name, datetime.datetime.today().strftime('%Y-%m-%d')))
        f = open("{0}{1}.csv".format(device.name, datetime.datetime.today().strftime('%Y-%m-%d')), "a")
        if not test:
            f.write("date,temp,hum,batt\n")
        f.write("{0},{1},{2},{3}\n".format(datetime.datetime.now().isoformat(sep=' '), temp, hum, battery))
        f.close()

        print("{0} {1} Temp: {2} C  Humidity: {3} %  Battery: {4} %".format(datetime.datetime.now().isoformat(), device.name, temp, hum, battery))

    def __init__(self):
        self._scanner = BleakScanner(self.detection_callback)

    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if advertisement_data.local_name is not None and advertisement_data.local_name.startswith('GVH5075'):
            manu = advertisement_data.manufacturer_data

            if manu is not None and manu.__contains__(60552):
                mfg_data = manu[60552] #60552 is the uuid of the bit of data we care about
                self.temp_hum(mfg_data[1:4], mfg_data[4], device)

    async def run(self):
        await self._scanner.start()
        
        while True:
            await asyncio.sleep(60)

        await self._scanner.stop()


if __name__ == '__main__':
    my_scanner = MyScanner()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(my_scanner.run())