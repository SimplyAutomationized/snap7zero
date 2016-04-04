from snap7.client import Client
from snap7.util import *
from snap7.snap7types import *
from snap7.snap7exceptions import *

try:
    from gpiozero import Button, LED, PWMLED
except:
    pass
from signal import pause
from time import sleep

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred

M = areas['MK']
I = areas['PE']
Q = areas['PA']
DB = areas['DB']


def dsleep(delay):
    d = Deferred()
    reactor.callLater(delay, d.callback, None)
    return d


class MemoryObject(object):
    _value = 0
    offsets = {"Bool": 2, "Int": 2, "Word": 2, "Real": 4, "DInt": 6, "String": 256, "SInt": 1}

    def __init__(self, datatype, area, plc, startbyte, bit=None, dbnum=0):
        self.datalength = self.offsets[datatype]
        self.datatype = datatype
        self.plc = plc
        self.offset = startbyte
        self.area = area
        self.bit = bit
        self._poll = False
        self._poller = None
        self.ondatachange = None
        self._dbnum = dbnum
        self._firstscan = 1
        self.plc.Memory.append(self)
        self._need_write = 0
        self.write_queue = []
        self._latest_data = bytearray
        self.read()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        # print 'setting val', val
        if val != self._value:
            self._write(val)

    def _write(self, value):
        # if self.area is Q or self.area is M or self.area is DB:
        data = self._latest_data
        if self.datatype == 'Real':
            set_real(data, 0, value)
        if self.datatype == 'Bool':
            set_bool(data, 0, self.bit, value)
        if self.datatype == 'Int':
            set_int(data, 0, value)
        if 'String' in self.datatype:
            set_string(data, 0, value)
        self.write_queue.append(data)
        if not reactor.running:
            self.write()
            sleep(.01)
            self.read()

    def write(self):
        data = self.write_queue.pop(0)
        try:
            self.plc.write_area(self.area, self._dbnum, self.offset, data)
        except Exception as e:
            print e.message

    def read(self):
        try:
            val = self.value
            value = None
            data = self.plc.read_area(self.area, self._dbnum, self.offset, self.datalength)
            self._latest_data = data
            if self.datatype.lower() == 'real':
                value = get_real(data, 0)
            if self.datatype.lower() == 'bool':
                value = get_bool(data, self.offset, self.bit)
            if self.datatype.lower() == 'int':
                value = get_int(data, self.offset)
            if self.datatype.lower() == 'word':
                value = get_int(data, self.offset)
            if self.datatype.lower() == 'dword':
                value = get_dword(data, self.offset)

            if 'String' in self.datatype:
                string_length = 256
                if '[' in self.datatype:
                    string_length = int(self.datatype.split('[')[1].remove(']'))
                value = get_string(data, self.offset, string_length)
            if self.ondatachange is not None and not self._firstscan:
                if val != value:
                    self.ondatachange(value)
            self._firstscan = 0
            self._value = value
        except Exception as e:
            print e.message
            pass


class BoolObject(MemoryObject):
    def __init__(self, area, startbyte, bit, plc):
        super(BoolObject, self).__init__('Bool', area, plc, startbyte, bit)
        self.ondatachange = self.__onchange

    def __onchange(self, value):
        if value:
            self.when_on()
        else:
            self.when_off()

        self.when_change(value)

    def when_change(self, value):
        pass

    def when_on(self):
        pass

    def when_off(self):
        pass

    def is_on(self):
        return self.value == 1

    def is_off(self):
        return self.value == 0


class RealObject(MemoryObject):
    def __init__(self, area, startbyte, plc):
        super(RealObject, self).__init__('Real', area, plc, startbyte)
        self.ondatachange = self.__onchange
        self.upper_threshold = 0
        self.lower_threshold = 0
        self._passed_upper_threshold = False
        self._passed_lower_threshold = False

    def __onchange(self, value):

        self.when_change(value)
        if value > self.upper_threshold and not self._passed_upper_threshold:
            self.when_above(value)
            self._passed_upper_threshold = True
        if value < self.upper_threshold and self._passed_upper_threshold:
            self._passed_upper_threshold = False
        if value < self.lower_threshold and not self._passed_lower_threshold:
            self._passed_upper_threshold = True
            self.when_below(value)
        if value > self.lower_threshold and self._passed_lower_threshold:
            self._passed_upper_threshold = False

    def when_change(self, value):
        pass

    def when_above_threshold(self, value):
        pass

    def when_below_threshold(self, value):
        pass


class InputBit(BoolObject):
    def __init__(self, startbyte, bit, plc):
        super(InputBit, self).__init__(I, startbyte, bit, plc)


class HOA_Switch(object):
    def __init__(self, byte, bit, byte2, bit2):
        self._hand = InputBit(byte, bit)
        self._auto = InputBit(byte2, bit2)
        self._hand.when_on = self._when_hand

    def when_hand(self):
        pass

    def when_auto(self):
        pass

    def _when_auto(self):
        pass

    def _when_hand(self):
        self.when_hand()

    def is_hand(self):
        return self._hand.value == 1

    def is_auto(self):
        return self._auto.value == 1


class OutputBit(BoolObject):
    def __init__(self, startbyte, bit, plc):
        super(OutputBit, self).__init__(Q, startbyte, bit, plc)

    def on(self):
        self.value = 1

    def off(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value


class S7PLC(Client):
    def __init__(self, ip, isS7200=False, localtsap=0x00, remotetsap=0x00):
        super(S7PLC, self).__init__()
        self.ip = ip
        if not isS7200:
            self.connect(ip, 0, 0)
        else:
            # s7-200 support
            self.set_connection_params(ip, localtsap, remotetsap)
            self.library.Cli_Connect(self.pointer)
        self.isS7200 = isS7200
        self.Memory = []
        self._scan = 1
        self.scantime = .001
        reactor.callLater(1, self.scan)

    def Button(self, byte, bit):
        return InputBit(byte, bit, self)

    def Input(self, byte, bit):
        return InputBit(byte, bit, self)

    def Output(self, byte, bit):
        return OutputBit(byte, bit, self)

    def AnalogOutput(self, startbyte):
        return MemoryObject('Word', Q, self, startbyte)

    def MemoryReal(self, startbyte):
        return RealObject(M, startbyte, self)

    def MemoryInt(self, startbyte):
        return MemoryObject('Int', M, self, startbyte)

    def MemoryBit(self, byte, bit):
        return BoolObject('Bool', M, byte, bit, self)

    def AnalogInput(self, startbyte):
        return MemoryObject('Word', I, self, startbyte)

    def HOA_switch(self, input1_byte, input1_bit, input2_byte, input2_bit):
        # TODO
        """
        Read status of HOA Switch
        :param input1_byte: input byte for H.O.A Switch when switched to hand
        :param input1_bit: input bit for H.O.A Switch when switched to hand
        :param input2_byte: input byte for H.O.A Switch when switched to auto
        :param input2_bit: input bit for H.O.A Switch when switched to auto
        :return:
        """
        pass

    @inlineCallbacks
    def scan(self):
        while self._scan:
            # try:
            for memory in self.Memory:
                if len(memory.write_queue) > 0:
                    memory.read()
                    memory.write()
                    memory.read()
                else:
                    memory.read()
            yield dsleep(self.scantime)
            # except Snap7Exception as e:
            # self._scan=0
            # self.reconnect()
            # break
            # print e

    def stop_scan(self):
        self._scan = 0
        self.disconnect()

    @inlineCallbacks
    def reconnect(self):
        while True:
            if self.get_connected():
                break
            if not self.isS7200:
                self.connect(self.ip)
            else:
                self.library.Cli_Connect(plc.pointer)
            yield dsleep(1)
        self.scan()


if __name__ == "__main__":
    def printValue(value):
        print value


    plc = S7PLC('10.10.55.113')
    # example of S7-200 connection
    # plc = S7PLC('192.168.1.12',isS7200=True,localtsap=0x1100,remotetsap=0x1100)
    plc.scantime = .01
    pi_led2 = LED(22)
    pi_led = LED(17)
    plc.output = plc.Output(0, 1)
    plc.button = plc.Input(0, 6)
    pi_button = Button(27)

    pi_button.when_pressed = plc.output.toggle

    plc.output.when_on = pi_led.on
    plc.output.when_off = pi_led.off

    plc.button.when_on = pi_led2.on
    plc.button.when_off = pi_led2.off

    reactor.run()
    plc.stop_scan()
    print 'stopped'
