#!/bin/bash

# Upewnij się, że Python i Flask są zainstalowane
pip3 install flask RPi.GPIO

# Uruchom serwer Flask w tle
python3 /home/umarly-poeta/vehicle_control_server.py &
