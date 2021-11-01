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
