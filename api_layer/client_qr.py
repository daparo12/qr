# -*- coding: utf-8 -*-
import os
import select
import sys

sys.path.append("..")
from random import random
from mesh_net.nodes_in_mesh import *
import physical_layer.qr_utils as qr_utils

import time
from config_qrnet import ConfigQRNet
from twisted.python.compat import raw_input

config = ConfigQRNet()


# Start of the interaction
def start_chat():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((config.SERVER_IRC_IP, config.LISTENING_IRC_PORT))
    nick = raw_input("Introduce your nickname > ")
    channel = raw_input("Write the channel > ")
    print("\n")
    # Send the nick to server
    server.send(nick.encode("ascii"))
    server.send(channel.encode("ascii"))
    # Confirmation of the server
    truck = server.recv(1).decode('UTF-8')

    # Validate if the server doesn't accept
    while (truck == "0"):
        nick = raw_input("\nNot available, choose anothe nickname > ")
        server.send(nick.encode("ascii"))
        truck = server.recv(1).decode('UTF-8')

    while True:
        # possible entrys
        sockets_list = [sys.stdin, server]

        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])

        for socks in read_sockets:

            if socks == server:
                message = socks.recv(2048).decode('UTF-8')
                print(message)
            else:
                message = sys.stdin.readline()
                server.send(message.encode("ascii"))
                server.send(channel.encode("ascii"))
                CURSOR_UP = '\033[F'
                ERASE_LINE = '\033[K'
                print(CURSOR_UP + ERASE_LINE)
                sys.stdout.write("<#" + channel + "-" + "Tu>")
                sys.stdout.write(message)
                sys.stdout.flush()
    server.close()


# Socket to sent messages tru tansm disp
def start_remote_qr(mac_destiny, message):
    message_to_send = "MAC " + mac_destiny + " " + message

    socket_qr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print((config.TRANSMISSION_DEVICE_IP, config.TRANSMISSION_PORT))
    socket_qr.connect((config.TRANSMISSION_DEVICE_IP, config.TRANSMISSION_PORT))

    message_to_send = message_to_send.encode('ascii')
    socket_qr.send(message_to_send)

    socket_qr.close()

def receive_transmission_device(my_mac):
    socket_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_send.connect((config.NET_MESH_IP, config.INFO_MESH_PORT))
    socket_send.send(my_mac.encode('ascii'))
    info = socket_send.recv(2048).decode('UTF-8')
    socket_send.close()

    info = info.split(' ')

    ip = info[0]
    port = int(info[1])

    socket_device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_device.bind((ip, port+1))
    socket_device.listen()

    while True:
        conn, address = socket_device.accept()
        reconstruct = Thread(target=reconstruct_message, args=(conn,))
        #reconstruct.daemon = True
        reconstruct.start()
        reconstruct.join()

# Translate the message

def reconstruct_message(conn):
    print("Got here!")
    data_list = []

    number = int(conn.recv(2048).decode('UTF-8'))

    for i in range(number):
        data_list.append(conn.recv(2048).decode('UTF-8'))
    conn.close()

    qr_reconstruction(data_list)


# Decides the recontruction of the type of item

def qr_reconstruction(data_list):
    print("Got here!")

    constructor = qr_utils.qr_reader()
    print('You\'ve recieved a QR text!')
    constructor.qr_to_text(save_in_file=False, info=data_list[0])


# Mac address for each new node on mesh
def macGenerator():
    new_mac = ''
    for m in range(0, 12):
        new_c = random.randint(0, 9)
        new_mac += str(new_c)
    return new_mac


def register_mesh(port):
    my_mac = macGenerator()
    socket_mesh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_mesh.connect((config.NET_MESH_IP, config.REGISTRY_MESH_PORT))

    register = "MAC " + my_mac + " PORT " + port

    socket_mesh.send(register.encode("ascii"))
    received_data = socket_mesh.recv(2048).decode("UTF-8")
    data = received_data.split(' ')

    if data[0] == 'OK/200':
        print("Node has been integrated")

    else:
        if data[0] == 'MACDUP':
            print("Mac address already in mesh")

        elif data[0] == 'PORTDUP':
            print("IP port is alreeady used")

        else:
            print("ERROR")

        sys.exit(2)

    return my_mac


# Verify if the sent messages are for the actual node
def verify_frame(conn):
    new_msj = conn.recv(2048).decode('UTF-8')
    new_msj = new_msj.split(' ')

    # verify if the message is for actual node
    if new_msj[0] == 'MESSAGE':
        print(">> New message: {0}".format(" ".join(str(x) for x in new_msj[1:])))

    elif new_msj[0] == 'RESEND':
        print("Resending message")
        ip_dest = new_msj[1]
        port_dest = int(new_msj[2])
        resend_msj = ""

        if new_msj[3] != 'MESSAGE':
            resend_msj = 'RESEND '

        resend_msj += " ".join(str(x) for x in new_msj[3:])

        socket_resend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_resend.connect((ip_dest, port_dest))
        print("\n Message sent to {0} {1}, {2}".format(ip_dest, port_dest, resend_msj))
        socket_resend.send(resend_msj.encode('ascii'))
        socket_resend.close()

    conn.close()


def prepare_send_in_mesh(origin, destiny, message):
    socket_mesh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_mesh.connect((config.NET_MESH_IP, config.RECEIVING_MESH_PORT))

    path_msj = "FROM " + origin + " TO " + destiny
    socket_mesh.send(path_msj.encode('ascii'))
    path = socket_mesh.recv(2048).decode('UTF-8')
    path = path.split(' ')

    if path[0] == 'NOTFOUND':
        print("Mac doesn't exist")

    elif path[0] == 'PATH':
        message = 'MESSAGE ' + message

        if len(path) > 3:
            message = 'RESEND ' + " ".join(str(x) for x in path[3:]) + " " + message

        socket_resend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_resend.connect((path[1], int(path[2])))
        print("\n Message sent to {0} {1}, {2}".format(path[1], path[2], message))
        socket_resend.send(message.encode('ascii'))
        socket_resend.close()

        print("Sending...")

    socket_mesh.close()


def send_mesh(mac_origin):
    while True:
        print('Format: MSG <mac_to> <message content>')
        message_in_mesh = str(input("#>> "))
        message_in_mesh = message_in_mesh.split(' ')
        if message_in_mesh[0] == 'MSG' and len(message_in_mesh) >= 3:

            if len(message_in_mesh[1]) != 12:
                print("Verify mac address")

            else:
                mac_dst = message_in_mesh[1]
                sending_msj = " ".join(str(x) for x in message_in_mesh[2:])
                prepare_send_in_mesh(mac_origin, mac_dst, sending_msj)
                break
        else:
            print("ERROR \n")


def receive_in_mesh(my_mac):

    socket_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_send.connect((config.NET_MESH_IP, config.INFO_MESH_PORT))
    socket_send.send(my_mac.encode('ascii'))
    info = socket_send.recv(2048).decode('UTF-8')
    socket_send.close()

    info = info.split(' ')

    socket_mesh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_mesh.bind((info[0], int(info[1])))
    socket_mesh.listen()
    while True:
        conn, address = socket_mesh.accept()
        verify = Thread(target=verify_frame, args=(conn,))
        verify.start()
        verify.join()


def delete_from_mesh(my_mac):
    socket_resend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_resend.connect((config.NET_MESH_IP, config.DELETE_PORT))
    socket_resend.send(my_mac.encode('ascii'))
    socket_resend.close()


def main():
    print("Remote-QR")
    print("Enter a port >")
    port = sys.stdin.readline()

    my_mac = register_mesh(port)

    recv_mesh = Thread(target=receive_in_mesh, args=(my_mac,))
    recv_mesh.daemon = True
    recv_mesh.start()

    device = Thread(target=receive_transmission_device, args=(my_mac,))
    device.daemon = True
    device.start()


    while True:
        selection = ''
        os.system('clear')
        print("Your MAC address: "+ my_mac)
        print("Select")
        print("1. Create QR")
        print("2. Enter IRC")
        print("3. Sent message on Mesh")
        print("4. Exit")
        print(">")
        option = int(sys.stdin.readline())

        if option == 1:

            print("Enter the desired message: ")
            message = raw_input()
            print("Enter MAC")
            dest_mac = raw_input()
            start_remote_qr(dest_mac, message)
            print("QR succesfuly created")
            time.sleep(1)

        elif option == 2:
            start_chat()


        elif option == 3:
            send_mesh(my_mac)

        elif option == 4:
            print("Byeeee")
            delete = Thread(target=delete_from_mesh, args=(my_mac,))
            delete.daemon = True
            delete.start()
            sys.exit()

        else:
            print("Select a valid option")
            time.sleep(1)


if __name__ == "__main__":
    main()
