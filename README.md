# led-tracking

Simple python script that opens an USB camera, tracks LEDs and sends positions to an OSC server.
Made as a replacement for "bonsai part" of [OpenEphys GUI tracking plugin](https://github.com/CINPLA/tracking-plugin) and can easily be used on linux systems.

Users can choose to track up to three LEDs with different color (red, green, blue), while data is being sent to an OSC server run by the [tracking plugin](https://github.com/CINPLA/tracking-plugin). 
Default ports and addresses are set to be the same as shown in [tracking plugin wiki](https://github.com/CINPLA/tracking-plugin/wiki), but are configurable. For detailed help type:

`python src/track_leds.py --help`
