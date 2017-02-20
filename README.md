# Python CYW Serial Port

These scripts connects a serial port to our service. This allows data to be sent from another device running one of our
libraries to any serial port that can be accessed by Python. PythonCywSerialPort_p27.py is used for Python 2.7 and
PythonCywSerialPort_p34.py is used for Python 3.4. Configure the settings.ini file before using these scripts.

The latest library uses WebSocket for communication. This means websocket client needs to be installed for it to work. Please use the following command to install websocket client:
pip install websocket-client

Please see our documentation at: https://www.controlyourway.com/Resources/PythonSerialPort