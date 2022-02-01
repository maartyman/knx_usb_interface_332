## knx usb interface 332

A knx to mqtt interface for the Weinzierl KNX USB Interface 332. I made this to connect my knx bus to home assistant.

Inspiration to reverse engineer the usb came from https://github.com/z64me/harpoon-rgb-mouse. This code might work with other knx to usb interfaces. But you will need to change some lines of code. I'll add an explanation here later on how I did this.

# configuration
Add the data in the <kbd>config-example.py</kbd>.

The doGeneralUpdate is false by default. I'm having problems where this causes some lights to turn on. Maybe others have better luck.