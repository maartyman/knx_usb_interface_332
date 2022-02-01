import usb.core
import usb.util
import sys
from queue import Queue

class Knx():

    def __init__(self):
        # device info
        self.idVendor = 0x0E77
        self.idProduct = 0x0104

        self.InterfaceNumber = 0

        # output interface
        self.outEndpointAddress = 0x01
        self.outMaxPacketSize = 0x0040

        # input interface
        self.inEndpointAddress = 0x81
        self.inMaxPacketSize = 0x0040

        self.dev = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)

        self.readBuffer = Queue(maxsize=300)
        self.writeBuffer = Queue(maxsize=300)

        if self.dev is None:
            raise ValueError('Device not found')

        if self.dev.is_kernel_driver_active(self.InterfaceNumber):
            try:
                self.dev.detach_kernel_driver(self.InterfaceNumber)
                print("kernel driver detached")
            except usb.core.USBError as e:
                sys.exit("could not detach kernel driver: %s" % str(e))
            else:
                print("no driver atached")

        try:
            usb.util.claim_interface(self.dev, self.InterfaceNumber)
            print("claimed device")
        except usb.core.USBError as e:
            sys.exit("could not claim device: %s" % str(e))

        try:
            self.dev.reset()
            self.dev.set_configuration()
            print("configuration set")
        except usb.core.USBError as e:
            sys.exit("configuration could not be set: %s" % str(e))

        self.initUsb()

        self.read()

    def sringToKnxAdress(self, string: str):
        """Converts a string adress to a 2 byte adress"""
        split = string.split("/")
        adress = int(split[2]) | int(split[1]) << 8 | int(split[0]) << 11
        return (adress.to_bytes(2, "little")[1], adress.to_bytes(2, "little")[0])

    def knxToStringAdress(self, adress) -> str:
        """Converts a 2 byte adress to a string adress"""
        adr1 = str(int(adress[0] >> 3))
        adr2 = str(int(adress[0] & 0x07))
        adr3 = str(int(adress[1]))

        return adr1 + "/" + adr2 + "/" + adr3

    def sringToKnxPointAdress(self, string: str):
        """Converts a string adress to a 2 byte adress"""
        split = string.split(".")
        adress = int(split[2]) | int(split[1]) << 8 | int(split[0]) << 12
        return (adress.to_bytes(2, "little")[1], adress.to_bytes(2, "little")[0])

    def knxToStringPointAdress(self, adress) -> str:
        """Converts a 2 byte adress to a string adress"""
        adr1 = str(int(adress[0] >> 4))
        adr2 = str(int(adress[0] & 0x0f))
        adr3 = str(int(adress[1]))

        return adr1 + "." + adr2 + "." + adr3

    def knxFloat2Conversion(self, data):
        v = ((data[0] & 0x80) << 24) | ((data[0] & 0x7) << 28) | (data[1] << 20)
        v >>= 20
        exp = (data[0] & 0x78) >> 3
        return ((1 << exp) * v * 0.01)


    def write(self):
        while not self.writeBuffer.empty():
            data = self.writeBuffer.get_nowait()

            package = [0x00] * self.outMaxPacketSize

            i = 0
            for hex in data:
                package[i] = hex
                i += 1
            
            self.dev.write(0x01, package)


    def writeOn(self, adress_string):
        adress = self.sringToKnxAdress(adress_string)

        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x13, 0x00, 0x08, 0x00, 0x0B, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xBC, 0xE0, 0x00, 0x00, adress[0], adress[1], 0x01, 0x00, 0x81 ]
        )

    def writeOff(self, adress_string):
        adress = self.sringToKnxAdress(adress_string)
        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x13, 0x00, 0x08, 0x00, 0x0B, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xBC, 0xE0, 0x00, 0x00, adress[0], adress[1], 0x01, 0x00, 0x80 ]
        )

    def writeValuePercent(self, adress_string, value):
        adress = self.sringToKnxAdress(adress_string)
        value = int(value * 2.55).to_bytes(2, "little")[0]
        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x14, 0x00, 0x08, 0x00, 0x0c, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xbc, 0xe0, 0x00, 0x00, adress[0], adress[1], 0x02, 0x00, 0x80, value]
        )

    def writeValueByte(self, adress_string, value):
        adress = self.sringToKnxAdress(adress_string)
        value = int(value).to_bytes(2, "little")[0]
        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x14, 0x00, 0x08, 0x00, 0x0c, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xbc, 0xe0, 0x00, 0x00, adress[0], adress[1], 0x02, 0x00, 0x80, value]
        )

    def getState(self, adress_string):
        adress = self.sringToKnxAdress(adress_string)
        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x13, 0x00, 0x08, 0x00, 0x0b, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xbc, 0xe0, 0x00, 0x00, adress[0], adress[1], 0x01]
        )

    def getTemp(self):
        adress_string = "3/1/2"
        adress = self.sringToKnxAdress(adress_string)
        self.writeBuffer.put_nowait(
            [ 0x01, 0x13, 0x13, 0x00, 0x08, 0x00, 0x0b, 0x01, 0x03, 0x00, 0x00, 0x11, 0x00, 0xbc, 0xe0, 0x00, 0x00, adress[0], adress[1], 0x01]
        )
    
    def read(self):
        error = False
        while (not error):
            try:
                data = self.dev.read(self.inEndpointAddress, self.inMaxPacketSize, 1)
                if((data[11] == 41)):
                    dataType = data[2]
                    adress = self.knxToStringAdress((data[17], data[18]))
                    fromAdress = self.knxToStringPointAdress((data[15], data[16]))
                    if (dataType == 0x13):
                        if ((data[21] & 0x0f) == 0x01):
                            self.readBuffer.put_nowait([fromAdress,adress,0,"on"])
                            print("from: %s to: %s : %s"%(fromAdress, adress , "aan"))
                        elif ((data[21] & 0x0f) == 0x00):
                            self.readBuffer.put_nowait([fromAdress,adress,0,"off"])
                            print("from: %s to: %s : %s"%(fromAdress, adress , "uit"))
                    elif (dataType == 0x14):
                        self.readBuffer.put_nowait([fromAdress,adress,1,data[22]])
                        print("%s: %d"%(adress , data[22]))
                    elif (dataType == 0x15):
                        floatValue = self.knxFloat2Conversion((data[22], data[23]))
                        self.readBuffer.put_nowait([fromAdress,adress,2,floatValue])
                        print("temp: %f"% floatValue)

            except usb.core.USBTimeoutError:
                error = True




    def initUsb(self):
        # write the data
        #A
        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x09, 0x00, 0x08, 0x00, 0x01, 0x0f, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0a, 0x00, 0x08, 0x00, 0x02, 0x0f, 0x03, 0x00, 0x00, 0x05, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        #B
        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x09, 0x00, 0x08, 0x00, 0x01, 0x0f, 0x01, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0f, 0x00, 0x08, 0x00, 0x07, 0x01, 0x03, 0x00, 0x00, 0xfc, 0x00, 0x00, 0x01, 0x39, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0f, 0x00, 0x08, 0x00, 0x07, 0x01, 0x03, 0x00, 0x00, 0xfc, 0x00, 0x00, 0x01, 0x3a, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        #A
        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x09, 0x00, 0x08, 0x00, 0x01, 0x0f, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0a, 0x00, 0x08, 0x00, 0x02, 0x0f, 0x03, 0x00, 0x00, 0x05, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        #C
        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x10, 0x00, 0x08, 0x00, 0x08, 0x01, 0x03, 0x00, 0x00, 0xf6, 0x00, 0x08, 0x01, 0x34, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0f, 0x00, 0x08, 0x00, 0x07, 0x01, 0x03, 0x00, 0x00, 0xfc, 0x00, 0x08, 0x01, 0x34, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])

        #B
        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x09, 0x00, 0x08, 0x00, 0x01, 0x0f, 0x01, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0f, 0x00, 0x08, 0x00, 0x07, 0x01, 0x03, 0x00, 0x00, 0xfc, 0x00, 0x00, 0x01, 0x39, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ])

        self.dev.write(
            0x01,
            [
                0x01, 0x13, 0x0f, 0x00, 0x08, 0x00, 0x07, 0x01, 0x03, 0x00, 0x00, 0xfc, 0x00, 0x00, 0x01, 0x3a, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])
