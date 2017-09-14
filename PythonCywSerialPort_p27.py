import serial, time, sys, signal, ConfigParser
from threading import Thread
import ControlYourWay_p27
import logging
import os
import Queue


class SerialPort:
    def __init__(self, port):
        # configure serial port
        self._rx_callback = None
        self._parity = serial.PARITY_NONE
        self._baudrate=115200
        self._number_of_bits = serial.EIGHTBITS
        self._stop_bits = serial.STOPBITS_ONE
        self._port = port
        self._serial = None
        self._running = False
        self._thread = None

    def set_parity(self, new_parity):
        if new_parity == 'E' or new_parity == 'e':
            self._parity = serial.PARITY_EVEN
        elif new_parity == 'O' or new_parity == 'o':
            self._parity = serial.PARITY_ODD

    def set_baudrate(self, new_baudrate):
        self._baudrate = new_baudrate

    def set_number_of_bits(self, new_number_of_bits):
        if new_number_of_bits == '7':
            self._number_of_bits = serial.SEVENBITS

    def set_stop_bits(self, new_stop_bits):
        if self._stop_bits == '2':
            self._stop_bits = serial.STOPBITS_TWO

    def set_rx_callback(self, rx_callback):
        self._rx_callback = rx_callback

    def open_serial_port(self):
        self._serial = serial.Serial(port=self._port, baudrate=self._baudrate, parity=self._parity,
                                     stopbits=self._stop_bits, bytesize=self._number_of_bits, timeout=0.25)
        # Create thread
        self._running = True
        self._thread = Thread(target=self._update)
        self._thread.start()

    def close_serial_port(self):
        self._running = False
        self._serial.close()

    def _update(self):
        while self._running:
            c = self._serial.read(1)
            if c:
                if self._rx_callback:
                    self._rx_callback(c)
        return False

    def send_data(self, data):
        if self._running:
            if type(data) is list:
                data = bytearray(data)
            self._serial.write(data)


class ControlYourWay:
    def __init__(self, cyw_username, cyw_password, serial_port, encryption, use_websocket, \
                 cyw_network_names, cyw_datatype, log_directory):
        self._log_directory = log_directory
        self._cyw = ControlYourWay_p27.CywInterface()
        self._cyw.set_user_name(cyw_username)
        self._cyw.set_network_password(cyw_password)
        self._cyw.set_network_names(cyw_network_names)
        self._cyw.set_connection_status_callback(self.connection_status_callback)
        self._cyw.set_data_received_callback(self.data_received_callback)
        self._serial_port_rec_queue = Queue.Queue()
        if self._log_directory != '':
            self._cyw.enable_logging(self._log_directory+'log.txt', logging.DEBUG, True)
        self._cyw.name = 'Python Serial Port'
        if encryption:
            self._cyw.set_use_encryption(True)
        if not use_websocket:
            self._cyw.set_use_websocket(False)
            print("Connection type: Long polling")
        else:
            print("Connection type: WebSocket")
        self._cyw.start()
        self._running = True
        self._datatype = cyw_datatype
        self._thread = Thread(target=self._collect_data)
        self._thread.start()
        self._serial_port = serial_port
        self._serial_port.set_rx_callback(self.data_received)
        print("Press Ctrl+C to quit")
        signal.signal(signal.SIGINT, self.signal_handler)
        while self._running:
            time.sleep(0.1)

    def signal_handler(self, signal, frame):
        self._cyw.close_connection(True)
        self._running = False
        self._serial_port.close_serial_port()
        print('Program stopped')
        sys.exit(0)

    def _collect_data(self):
        while self._running:
            if not self._serial_port_rec_queue.empty():
                build_str = ""
                while not self._serial_port_rec_queue.empty():
                    build_str += self._serial_port_rec_queue.get()
                send_data = ControlYourWay_p27.CreateSendData()
                send_data.data = build_str
                send_data.data_type = self._datatype
                self._cyw.send_data(send_data)
            time.sleep(0.01)
        return False

    def connection_status_callback(self, connected):
        if connected:
            print('\nConnection successful\n')
        else:
            print('\nConnection failed\n')

    def data_received_callback(self, data, data_type, from_who):
        self._serial_port.send_data(data)

    # callback which will be called by serial port when data is received
    def data_received(self, c):
        self._serial_port_rec_queue.put(c)

if __name__ == "__main__":
    # see if the user specified a settings file
    if len(sys.argv) == 2:
        settings_filename = sys.argv[1]
    else:
        settings_filename = "settings.ini"
    if not os.path.isfile(settings_filename):
        print('Error: Could not load settings file: ' + settings_filename)
        sys.exit()
    network_names_option = "network"
    config = ConfigParser.ConfigParser()
    config.read(settings_filename)
    connection_list = config.options("ControlYourWayConnectionDetails")
    param_cyw_username = config.get("ControlYourWayConnectionDetails", "username")
    param_cyw_password = config.get("ControlYourWayConnectionDetails", "password")
    param_cyw_datatype = config.get("ControlYourWayConnectionDetails", "datatype")
    param_cyw_encryption = False
    if config.get("ControlYourWayConnectionDetails", "encryption") == "1":
        param_encryption = True
    param_cyw_use_websocket = True
    if config.get("ControlYourWayConnectionDetails", "useWebsocket") == "0":
        param_cyw_use_websocket = False
    param_cyw_log_directory = config.get("ControlYourWayConnectionDetails", "logDirectory")
    param_cyw_network_names = []
    for item in connection_list:  #search for network names
        if item[:len(network_names_option)] == network_names_option:
            param_cyw_network_names.append(config.get("ControlYourWayConnectionDetails", item))
    param_serial_port_name = config.get("SerialPortSettings", "serport")
    param_parity = config.get("SerialPortSettings", "parity")
    param_baudrate = config.get("SerialPortSettings", "baudrate")
    param_number_of_bits = config.get("SerialPortSettings", "numbits")
    param_stop_bits = config.get("SerialPortSettings", "stopbits")
    serial_port = SerialPort(param_serial_port_name)
    serial_port.set_parity(param_parity)
    serial_port.set_baudrate(param_baudrate)
    serial_port.set_number_of_bits(param_number_of_bits)
    serial_port.set_stop_bits(param_stop_bits)
    serial_port.open_serial_port()
    cyw = ControlYourWay(param_cyw_username, param_cyw_password, serial_port, param_cyw_encryption,
                         param_cyw_use_websocket, param_cyw_network_names, param_cyw_datatype, param_cyw_log_directory)
    print("Program finished")
