requirements:
	pip install -r requirements.txt

install: requirements
	sudo echo python3 '$(shell pwd)/src/track_leds.py $$@' > /usr/bin/track_leds
	sudo chmod 555 /usr/bin/track_leds
