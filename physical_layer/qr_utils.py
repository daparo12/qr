import qrcode
from pyzbar.pyzbar import decode
import pyzbar.pyzbar as pyzbar
from PIL import Image
import codecs
import cv2
from physical_layer.frame import Frame
import os
import errno
from datetime import datetime


class qr_generator:

    FILE_TYPE = 'f'
    TEXT_TYPE = 't'

    def generate_qr(self, data, qr_name):
        '''
        Function that creates a PNG file that contains the data in a QR form
        :param data: Data to put in a QR
        :param qr_name: Name of the PNG file
        '''
        qr = qrcode.QRCode(
            version = 1,
            error_correction = qrcode.constants.ERROR_CORRECT_L,
            box_size = 10,
            border = 4,
        )

        qr.add_data(data)
        qr.make(fit = True)

        image = qr.make_image(fill_color =  "black", back_color = "white")

        qr_file = open(qr_name + ".png", "wb")
        image.save(qr_file)
        qr_file.close()



    def file_to_qr(self, mac,bytes_to_read, filename):
        '''
        Function that takes a file and p
        :param bytes_to_read: number of bytes to save in each QR image (max 128 bytes)
        :param filename: Name of the source file
        :return: Error128 in case that 128 < bytes_to_read  < 0
        '''
        try:
            os.mkdir(filename+"QRs")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        frame = Frame()

        if bytes_to_read > 103 or bytes_to_read < 0:
            return "Error128"

        buffer = bytearray()
        try:
            file = open(filename, "rb")
            bytes = file.read(1)
        except FileExistsError:
            print("An error with file: "+filename+" has occured")
            return

        i = 1
        j = 0  # Counter of files, used to create a QR name

        while bytes:
            if i == bytes_to_read:
                # Call to generate_qr every bytes_to_read
                data = frame.new_frame(mac,self.FILE_TYPE,buffer.hex())
                self.generate_qr(data, filename+"QRs"+"/"+"QR"+str(j)) #The data is storage in hex values
                i = 0
                buffer = bytearray()
                j += 1
            buffer += bytes
            bytes = file.read(1)
            i += 1

        if i != 0:
            #In case of the remaining data are less than bytes_to_read
            data = frame.new_frame(mac, self.FILE_TYPE, buffer.hex())
            self.generate_qr(data, filename+"QRs"+"/"+"QR"+str(j))



class qr_reader:

    def parse_data(self, qr):
        frame = Frame()
        message_data = {}
        string = str(qr[0].data)
        message_data['data'] = string
        string = string.split(',')
        mac = string[0]
        mac = mac[2:]
        type = string[1]
        protocol_version = string[2]
        checksum = string[3]

        message_data['mac'] = mac
        message_data['type'] = type
        message_data['protocol'] = protocol_version
        message_data['checksum'] = checksum

        if checksum != frame.CHECKSUM:
            return "ERROR1"
        message = string[4]
        message = message[:-1]

        message_data['message'] = message

        return message_data

    def read_from_folder(self, qr_amount, path):
        qr_list = []

        for i in range(qr_amount):
            obj = decode(Image.open(path + "/QR" + str(i) + '.png'))
            qr = self.parse_data(obj)
            qr_list.append(qr)

        #Retorna lista de diccionarios con la info de cada QR leido
        return qr_list

    def reconstruct_file(self, is_list, data = None, qr_amount = None, path = None):
        '''
        Function to reconstruct a file from QRs, the QR filename should be QRi.png where i = [0, quantity of QRs]
        :param qr_amount: Quantity of QRs
        '''
        now = datetime.now()
        name = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
        f = open("Nuevo mensaje. " + name, "ab")  # Opening a file in append bytes

        if not is_list:
            if qr_amount != None:
                if path[len(path)-1] == '/':
                    name = path + "QR"
                else:
                    name = path + "/QR"
                for i in range(0, qr_amount):
                    self.qr_to_file(is_list= False,file=f, file_name= name + str(i) +".png")
            else:
                print("Se necesita la cantidad de QR a leer")
                return "Error01"
        else:

            if data != None:
                for qr in data:
                    self.qr_to_file(is_list=True, file=f, data =qr)
            else:
                print("Se necesita una lista con QRs")
                return "Error02"
        print('Se ha reconstruido el archivo: ' + f.name)
        f.close()

    def qr_to_file(self,is_list, file, file_name=None, data=None):
        '''
        :param file_name: QR file name
        '''


        if not is_list:
            if file_name != None:
                try:
                    file_data = self.parse_data(pyzbar.decode(Image.open(file_name)))
                    file.write(codecs.decode(file_data['message'], 'hex_codec'))  # Docoding in Hex values the string

                except FileNotFoundError:
                    print("An error with QR: " + file_name + " has occurred")
            else:
                print("Debe pasar el nombre del QR a leer")
                return "Error03"

        else:
            if data != None:
                file_data = data.split(',')[4]
                file.write(codecs.decode(file_data, 'hex_codec'))

            else:
                print("Debe pasar los datos del QR")
                return "Error04"


    def qr_to_text(self, save_in_file, file_name = None, info = None):
        '''
        Parsing the text in a QR
        :param file_name: QR file name
        :param save_in_file: True to save the message in a file, False just to print it
        '''
        if file_name != None:
            qr = decode(Image.open(file_name))  # decoding the QR file
            string = str(qr[0].data)
        else:
            string = info.split(',')[4]  # removing the b' and ' characters
            #string = string[:-1]
        if not save_in_file:
            #Just printing the data
            print(string)
        else:
            #Save the data in a file
            try:
                file = open("message.txt", "w")
                file.write(string)
                file.close()
            except SystemError:
                print("Error writing the QR text in a file")


    def scan(self):
        cam = cv2.VideoCapture(0)
        qrs = []
        print("Para cerrar el capturador de QR presione la tecla ESC, para capturar un QR presiones la tecla c, el QR debe estar correctamente enfocado")
        while True:
            _,frame = cam.read()
            obj = pyzbar.decode(frame)
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1)

            if key == 99 or key == 67:
                if obj == []:
                    print("No se ha encontrado ningún QR")
                else:
                    parser = self.parse_data(obj)

                    if parser in qrs:
                        print("Este QR ya fue leido con anterioridad")
                    else:
                        qrs.append(parser)
                        print("Data: ", obj[0].data)
            if key == 27:
                break
        return qrs


