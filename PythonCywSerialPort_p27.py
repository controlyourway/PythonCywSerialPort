import serial, time, getopt, sys, signal
from threading import Thread
import ControlYourWay_v1_p27


class SerialPort:
    def __init__(self, port):
        # configure serial port
        self._rx_callback = None
        self._buffer = ""
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
    def __init__(self, cyw_username, cyw_password, serial_port, encryption, cyw_network_names=['network 1']):
        self._cyw = ControlYourWay_v1_p27.CywInterface()
        self._cyw.set_user_name(cyw_username)
        self._cyw.set_network_password(cyw_password)
        self._cyw.set_network_names(cyw_network_names)
        self._cyw.set_connection_status_callback(self.connection_status_callback)
        self._cyw.set_data_received_callback(self.data_received_callback)
        self._cyw.name = 'Python Serial Interface'
        if encryption:
            self._cyw.set_use_encryption(True)
        self._send_data_collected = ""
        self._cyw.start()
        self._running = True
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
            if len(self._send_data_collected) > 0:
                send_data = ControlYourWay_v1_p27.CreateSendData()
                send_data.data = self._send_data_collected
                self._cyw.send_data(send_data)
                self._send_data_collected = ""
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
        self._send_data_collected += c

def print_help():
    print('PythonCywSerialPort.py -u <username> -p <password> -s <serialport>\n')
    print('For example:\n')
    print('PythonCywSerialPort.py -u test@controlyourway.com -p 123456789 -s "COM1"\n')
    print('Please register on www.controlyourway.com if you don\'t have these details\n')
    print('Optional parameters:\n')
    print('-r <parity> (E for even, O for odd), default None\n')
    print('-b <baudrate>, default 115200\n')
    print('-n <number of bits> (7 or 8), default 8\n')
    print('-t <stop bits> (1 or 2), default 1\n')
    print('-e <encryption> (0 or 1)default 0\n')

if __name__ == "__main__":
    param_cyw_username = ''
    param_cyw_password = ''
    param_serial_port_name = ''
    param_parity = ''
    param_baudrate=''
    param_number_of_bits = ''
    param_stop_bits = ''
    param_encryption = False
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv,"hu:p:s:r:b:n:t:e:",["username=","password=","serport=","parity=",
                                                         "baudrate=","numbits=","stopbits=","encryption="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-u", "--username"):
            param_cyw_username = arg
        elif opt in ("-p", "--password"):
            param_cyw_password = arg
        elif opt in ("-s", "--serport"):
            param_serial_port_name = arg
        elif opt in ("-r", "--parity"):
            param_parity = arg
        elif opt in ("-b", "--baudrate"):
            param_baudrate = arg
        elif opt in ("-n", "--numbits"):
            param_number_of_bits = arg
        elif opt in ("-t", "--stopbits"):
            param_stop_bits = arg
        elif opt in ("-e", "--encryption"):
            if arg == '1':
                param_encryption = True
    # these three parameters must be present for program to work
    if param_cyw_username == '' or param_cyw_password == '' or param_serial_port_name == '':
        print_help()
        sys.exit(2)
    serial_port = SerialPort(param_serial_port_name)
    if param_parity != '':
        serial_port.set_parity(param_parity)
    if param_baudrate != '':
        serial_port.set_baudrate(param_baudrate)
    if param_number_of_bits != '':
        serial_port.set_number_of_bits(param_number_of_bits)
    if param_stop_bits != '':
        serial_port.set_stop_bits(param_stop_bits)
    serial_port.open_serial_port()
    cyw = ControlYourWay(param_cyw_username, param_cyw_password, serial_port, param_encryption)
    print("Program finished")
