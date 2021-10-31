# -*- coding: utf-8 -*-
# Server chat socket
import socket
import sys
sys.path.append("..")
from _thread import start_new_thread
from config_qrnet import ConfigQRNet

# Conected clients
list_of_clients = []
nicks = {"admin": "admin"}
config = ConfigQRNet()

def clientthread(conn, addr):
    #Welcome message for the new client
    conn.send(("Welcome " + nicks[conn] + "!!!").encode("ascii"))

    while True:
        try:
            message = conn.recv(2048).decode('UTF-8')
            channel = conn.recv(2048).decode('UTF-8')

            if message:
                # Print address and message of user
                if message == '/EXIT\n':
                    print('Byeeee' + nicks[conn])
                    remove([conn, channel])
                    conn.close()
                else:
                    print("<#" + channel + "-" + addr[0] + " " + nicks[conn] + " > " + message)

                    # Calls broadcast function to send message to all users
                    message_to_send = "<#" + channel + "-" + nicks[conn] + "> " + message
                    broadcast(message_to_send, conn, channel)
            else:
                """Deletes connection if the connection is broken """
                # remove connection
                remove([conn, channel])
        except:
            continue


def broadcast(message, connection, channel):
    for clients in list_of_clients:
        if clients[0] != connection:
            try:
                if clients[1] == channel:
                    clients[0].send(message.encode("ascii"))
                else:
                    continue
            except:
                clients[0].close()
                # If broken
                remove(clients)


def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)


def power_up_chat():
    print("Welcome to the chat " + config.SERVER_IRC_IP + "!!!")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((config.SERVER_IRC_IP, config.LISTENING_IRC_PORT))
    server.listen(100)

    while True:
        """Accepts connection request and saves two param, conn is a socket obj
        and addr that has the IP address """
        conn, addr = server.accept()
        # First recieved message is the nickname
        nick = conn.recv(2048).decode('UTF-8')
        channel = conn.recv(2048).decode('UTF-8')
        """Place client in our client list """
        list_of_clients.append([conn, channel])

        """Validates the nick with our dictionary"""
        t = True
        i = 0
        for i in nicks:
            if nicks[i] == nick:
                t = True
            else:
                t = False
        # If available then adds the nick
        if t == False:
            nicks[conn] = nick
            # Send Confirmation to the client
            conn.send("1".encode("ascii"))
        else:
            #If not available we denig access and create a loop until selects one available
            while t:
                conn.send("0".encode("ascii"))
                nick = conn.recv(2048).decode('UTF-8')
                if nicks[i] == nick:
                    t = True
                else:
                    t = False
                    nicks[conn] = nick
                    conn.send("1".encode("ascii"))
        # Print address and name of the just connected client
        print(addr[0] + " " + nick + " conectado")

        # Create new thread for the new client
        start_new_thread(clientthread, (conn, addr))
    conn.close()
    server.close()

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("ERROR: No server_qr.py")
        exit()

    try:

        power_up_chat()
    except KeyboardInterrupt as e:
        print('[+] Bye!')
