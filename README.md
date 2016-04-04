# snap7zero
snap7-python helper library for raspberry pi

requires snap7-python, twisted & gpiozero

using the reactor main loop this library is used to poll memory values frequently from the PLC

example of connecting to S7-1200/S7-1500 PLC
    def printValue(value):
        print value


    plc = S7PLC('10.10.55.113')
    # for an example of S7-200 connection use:
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
