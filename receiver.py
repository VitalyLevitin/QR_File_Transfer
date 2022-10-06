import base64
import hashlib
import click
import cv2
from pyzbar.pyzbar import decode
import os
from headers import MESSAGE_BEGIN, HEADER_BEGIN, HEADER_END, MESSAGE_END

corrupted_data = False


class Receiver(object):
    window_name = 'QRreader'  # The name of the window
    data = None
    start = False
    header = False
    length = None
    hash = None
    current_iteration = 0  # Iteration for the QR code files
    counterHash = 0  # Iteration counter for the hash check
    counterLength = 0  # Iteration counter for the hash check
    chunks = []

    # Commands for the CV2 functionality
    def __init__(self):
        cv2.namedWindow(self.window_name)
        self.capture = cv2.VideoCapture(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.capture = None

    # End of Commands for the CV2 functionality

    # As the name states this function processes the the data it receives
    def process_frames(self):

        while True:  # The camera keeps recording while it is not interrupted
            result, frame = self.capture.read()
            height, width, channels = frame.shape

            img_array = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            img = decode((img_array.tobytes(), width, height))

            # Process the frames
            for symbol in img:
                if not self.process_header(symbol):
                    return

            # Update the preview window
            cv2.imshow(self.window_name, frame)
            if cv2.waitKey(1) & 0xFF == 27:  # On escape button the program will halt
                break

    # Each frame is processed
    def process_header(self, header):
        global corrupted_data
        content = header.data.decode("iso-8859-1")

        if content == MESSAGE_BEGIN:  # First we should receive the the flag for the beginning of the massage
            self.start = True
            return True

        if content == HEADER_BEGIN:  # Secondly the header file should begin
            self.header = True
            return True

        if 'LEN' in content:  # This header affirms the length of the massage represented in QR codes
            self.length_check(content)
            return True

        if 'HASH' in content:  # This is the header for the SHA1 integrity check
            self.hash_check(content)
            return True

        if content == HEADER_END:  # A check for seeing if anything's missing or corrupted on arrival
            if not self.length or not self.hash:
                corrupted_data = True
                raise Exception('Header read failed.')
            return True

        if not self.start or not self.header:  # A check if for some reason the start of the massage is corrupted
            corrupted_data = True
            raise Exception('Missing message start header.')

        if content == MESSAGE_END:  # A check of the integrity with the original data SHA1 encoding by checking equality
            final_hash = hashlib.sha1(self.data.encode("iso-8859-1")).hexdigest()
            if final_hash != self.hash:
                click.secho(f'False final hash Expected: {self.hash}, Received: {final_hash}'
                            , fg='red', bold=True)
                corrupted_data = True
            cv2.destroyWindow(self.window_name)
            return False

        # Next check is done by checking the iteration counter
        # Also the data from the QR is decoded and added to the current data assembler
        iteration, data = int(content.split(':')[0]), base64.b64decode(content.split(':')[1][2:-1]).decode("iso-8859-1")

        if iteration in self.chunks:
            return True
        else:
            self.chunks.append(iteration)

        if self.current_iteration != iteration:
            click.secho(
                f'Error occurred! Expected {self.current_iteration} but got {iteration}\n'
                f'Deleting received data file', fg='red')
            if self.current_iteration != iteration:
                corrupted_data = True
                return False

            self.current_iteration = iteration

        # If this step is done correctly, we proceed to the next iteration and adding the data we've decoded
        self.current_iteration += 1
        self.data = self.data + data

        click.secho(f'{self.current_iteration} / {self.length}', fg='green', bold=True)
        return True

    # The hash is taken from the code
    def hash_check(self, content):
        self.hash = content.split(':')[1]
        self.counterHash += 1
        click.secho(f'Part number {self.counterHash}, Hash check successful', fg='blue', bold=True)

    # The hash is taken from the code
    def length_check(self, content):
        self.length = content.split(':')[1]
        self.counterLength += 1
        click.secho(f'Part number {self.counterLength},Length check successful', fg='blue', bold=True)


# The main method for the receiver end, which starts the logic and executes the command
if __name__ == '__main__':
    status = True
    filename = "ReceivedFile"
    with open(filename, 'wb') as outputData:
        try:
            click.secho('Camera activated', fg='green')

            with Receiver() as qr:
                qr.process_frames()

            outputData.write(qr.data.encode('iso-8859-1'))

        except Exception as e:
            click.secho(f'Exception occurred: {e}', fg='red')

    with open(filename, 'rb') as f:  # If the file is corrupted, the newly created file is being deleted
        if corrupted_data:
            os.remove(filename)
        elif f.read(1):
            click.secho(f'Success! Data saved into:{filename}')
        else:
            click.secho('Abrupt closing, data not saved', fg='red')
            os.remove(filename)
