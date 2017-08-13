#!/bin/bash
# check if sudo is used
if [ "$(id -u)" != 0 ]; then
  echo 'Sorry, you need to run this script with sudo'
  exit 1
fi

# Create a log file for the uninstall as well as displaying the build on the tty as it runs
exec > >(tee build-cywSerialPort.log)
exec 2>&1

systemctl stop cywserialport.service
systemctl disable cywserialport.service

rm /lib/systemd/system/cywserialport.service
rm /etc/cywserialport.ini
rm /usr/sbin/ControlYourWay_p27.py
rm /usr/sbin/PythonCywSerialPort_p27.py

systemctl daemon-reload
systemctl reset-failed
