# snap7zero
snap7-python helper library for raspberry pi inspired by gpiozero.

requires snap7-python, twisted & gpiozero

using the reactor main loop this library is used to poll memory values frequently from the PLC

###- Installation

    git clone https://github.com/SimplyAutomationized/snap7zero.git
    cd snap7zero
    sudo python setup.py install
    
###- Example of connecting to S7-1200/S7-1500 PLC
    from snap7zero import S7PLC
    
    def printValue(value):
        print value


    plc = S7PLC('10.10.55.113')
    # for an example of S7-200 connection use:
    # plc = S7PLC('192.168.1.12',isS7200=True,localtsap=0x1100,remotetsap=0x1100)
    plc.scantime = .01
    
    #gpiozero led/button code for raspberry pi
    pi_led2 = LED(22)
    pi_led = LED(17)
    pi_button = Button(27)
    
    #create an output object for Q0.1 and an input button on I0.6
    plc.output = plc.Output(0, 1)
    plc.button = plc.Input(0, 6)
    #can do this as well:
    # output = plc.Output(0,1)
    # button = plc.Input(0,6)
    
    #toggle plc.output when button on pi is pressed
    pi_button.when_pressed = plc.output.toggle

    #turn on led connected to raspberry pi when plc.output is true
    plc.output.when_on = pi_led.on
    plc.output.when_off = pi_led.off

    #turn on second led on the raspberry pi when button plc.button is pressed
    plc.button.when_on = pi_led2.on
    plc.button.when_off = pi_led2.off

    reactor.run()
    plc.stop_scan()
    print 'stopped'
