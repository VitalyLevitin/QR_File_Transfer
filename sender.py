import base64
import hashlib
import os
import time
import pyqrcode
from headers import MESSAGE_BEGIN, HEADER_BEGIN, HEADER_END, MESSAGE_END, SET_TIME, DEFAULT_SIZE
from tkinter import Tk
from tkinter.filedialog import askopenfilename


# The class corresponds with the sender side of the application
# The sender chooses a file, converts it into chunks,
# hashes it and displays it via the terminal to the other device (the receiver) to read
class Sender(object):

    def __init__(self, size=DEFAULT_SIZE, data=None):
        self.size = size
        self.data = self.chunks(data, self.size)
        self._headers_list = [MESSAGE_BEGIN, HEADER_BEGIN, f'LEN:{str(len(self.data))}',
                              'HASH:{0}'.format(hashlib.sha1(rb''.join(self.data)).hexdigest()),
                              HEADER_END]

    def chunks(self, chunk_array, size=None):
        n = max(1, size if size else self.size)
        if chunk_array:
            return [chunk_array[i:i + n] for i in range(0, len(chunk_array), n)]

    def headers(self):
        return self._headers_list

    def print_qr_code(self, payload):
        data = pyqrcode.create(payload)
        return self.data, data.terminal(quiet_zone=1)

    # We send the first 4 headers:
    # To begin massage transmit
    # To flag the first header
    # To signal the size in bytes of the file to send
    # The hash code checks the integrity of the massage using the sha1 algorithm
    # Why sha1? because of simplicity, 160 bit long key will be enough for this purpose
    def send_data(self):
        counter = 0
        if not self.data:
            raise Exception('No data was found')

        for header in self.headers():
            print(f'{header}')
            _, data = self.print_qr_code(header)
            print(data)
            time.sleep(SET_TIME)

        for part in self.data:
            print(f'{abs(counter - len(self.data))} left')
            payload = f'{counter:010d}:{base64.b64encode(part)}'
            _, data = self.print_qr_code(payload)
            print(data)
            counter += 1
            time.sleep(SET_TIME)

        _, msg_end = self.print_qr_code(MESSAGE_END)
        print(msg_end)

    def sample_size(self, size=None):
        test_size = size if size else self.size
        data = pyqrcode.create('{0}'.format('A' * (test_size + 10)))
        print(data.terminal())


# The main method which chooses a file via file chooser dialog and sends the data to be processed
if __name__ == "__main__":
    Tk().withdraw()
    filename = askopenfilename(initialdir=os.getcwd())
    print(filename)
    if len(filename) < 1 or filename == '':
        print('No file was selected')
        exit(0)
    print(chr(27) + "[2J")
    time.sleep(1)
    inputData = open(filename, 'rb')
    Sender(data=inputData.read()).send_data()
    inputData.close()
