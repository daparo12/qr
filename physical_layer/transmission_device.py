import socket
import sys
from threading import Thread

sys.path.append("..")
from qr_utils import qr_generator
from frame import Frame
from config_qrnet import ConfigQRNet

config = ConfigQRNet()



class trans_device:

    PROTOCOL_VERSION = '0.1'
    CHECKSUM = '171729'


    def server(self):
        s_qr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_qr.bind((config.TRANSMISSION_DEVICE_IP, config.TRANSMISSION_PORT))
        s_qr.listen()

        while True:
            conn, address = s_qr.accept()

            print("\nQR has been requested!")

            s_trans = Thread(target=self.new_transmition, args=(conn,))
            s_trans.daemon = True
            s_trans.start()
            s_trans.join()

    def new_transmition(self, connection):
        frame = Frame()
        generator = qr_generator()
        recv_message = connection.recv(2048).decode("UTF-8")
        recv_message = recv_message.split(' ')
        print(recv_message)

        mac_dest = recv_message[1]
        data = recv_message[2]
        frame_to_qr = frame.new_frame(mac_dest,data)

        generator.generate_qr(data=frame_to_qr, qr_name='Message to: ' + mac_dest)
        connection.close()


def main():
    service = trans_device()
    service.server()


if __name__ == "__main__":

    try:
        print("Transmission device is now active!")
        print((config.TRANSMISSION_DEVICE_IP, config.TRANSMISSION_PORT))
        main()
    except KeyboardInterrupt as e:
        print('[+] Bye!')
