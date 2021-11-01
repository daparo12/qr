import random
import socket
from threading import Thread
import sys
sys.path.append("..")
import mesh_net.node_qr as node_qr
from config_qrnet import ConfigQRNet


mesh_list = [] #New nodes will be added to this list

config = ConfigQRNet()

def add_new_node(ip_address, mac_address, port):
    '''
    After a new user selects port, this method is triggered, creating a new node and adding it to the mesh list
    '''
    new_n = node_qr.QRNode(mac_address, ip_address, port)
    mesh_list.append(new_n)

    print("Node added succesfully! Port: " + port)

# Checks if a node is already in the mesh_list or if the port is used.
# This method is used by register_new_node as a validation.
def already_exist(ip_address, mac_address, port):
    for node in mesh_list:
        if node.mac_address == mac_address:
            return "a"
        elif node.ip_address == ip_address and node.port == port:
            return "b"

    return "c"


# This function receives the msg from client_qr
# This function sends a message with the status of the insertion.
def register_new_node(ip, connection):
    received_data = connection.recv(2048).decode("UTF-8") #Buffer size is 2048.
    data_list = received_data.split(' ')

    if data_list[0] == 'MAC' and data_list[2] == 'PORT':
        mac_node = data_list[1]
        ip_node = ip
        port_node = data_list[3]

        response_exist = already_exist(ip_node, mac_node, port_node)
        if response_exist == 'a':
            connection.send('MACDUP'.encode('ascii'))
        elif response_exist == 'b':
            connection.send('PORTDUP'.encode('ascii'))
        else:
            connection.send('OK/200'.encode('ascii'))
            add_new_node(ip_node, mac_node, port_node) #Add the newly created node


    else:
        connection.send('ERROR'.encode('ascii'))
    connection.close()


def mesh_server():
    #Inits and binds socket to listen for connections. 
    s_mesh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_mesh.bind((config.NET_MESH_IP, config.REGISTRY_MESH_PORT))
    s_mesh.listen()

    # Listens to new connections.
    print('Waiting for connections...')
    while True:
        conn, address = s_mesh.accept()

        print("\n\nNew node added in the mesh net, address: " + address[0])

        # A new thread is created, started and joined.
        start = Thread(target=register_new_node, args=(address[0], conn)) #Run register_new_node on a thread.
        start.start()
        start.join()

# This function receives a MAC address of the receptor client and seeks
# where that receptor is in the mesh net.
def info_mesh(conn):
    mac = conn.recv(2048).decode('UTF-8')
    index = [find_index_by_mac(mac)] # Searches for the index of the client in the mesh_list
    client = find_node_by_index(index) 

    ip = client[0].ip_address #IP of the receiver client
    port = client[0].port     #Port of the receiver client.

    info = ip + ' ' + port
    conn.send(info.encode('ascii'))
    conn.close()

# Receives requests to delete clients.
def del_mesh(conn):
    print(mesh_list)
    mac = conn.recv(2048).decode('UTF-8')
    index = [find_index_by_mac(mac)]
    client = find_node_by_index(index)
    mesh_list.remove(client[0])
    print(mesh_list)
    conn.close()

# This function returns a list of the conectivity data of the CLIENTS asociated with
# the given indexes.
def find_node_by_index(index_list):
    clients = []
    for index in index_list:
        clients.append(mesh_list[index])
    return clients

# This function serves as a "map" to return the index of a client given a mac_address
def find_index_by_mac(mac_address):
    required_index = -1
    size = len(mesh_list)
    for i in range(size):
        check = mesh_list[i].mac_address
        if str(check) == str(mac_address):
            required_index = i
    return required_index


# Decides how to construct the path of sending.
def sending_path(mc_origin, mc_dest):

    if (len(mesh_list) - 1) > 3: #List is long enough to randomize the path
        path = random_path(mc_origin, mc_dest)
    else:   #Theres no point on randomizing the path.
        path = normal_path(mc_origin, mc_dest)
    return path

# Generates a random route to generate anonimity inside the mesh_net
def random_path(origin, destiny):
    index_list = []
    origin_index = find_index_by_mac(origin)
    destiny_index = find_index_by_mac(destiny)
    i = 0
    while i < 3:
        random_index = random.randint(0, len(mesh_list) - 1)

        if random_index != origin_index and random_index != destiny_index:
            if random_index not in index_list:
                index_list.append(random_index)
                i += 1

    nodes_list = find_node_by_index(index_list)
    nodes_list.append(mesh_list[destiny_index])
    return nodes_list


# A falta de nodos se procede a realizar un camino con lo que haya en la red mesh.
def normal_path(origin, dest):
    index_list = []
    origin_index = find_index_by_mac(origin)
    destiny_index = find_index_by_mac(dest)

    for i in range(len(mesh_list) - 1):
        if i != origin_index and i != destiny_index:
            index_list.append(i)
    nodes_list = find_node_by_index(index_list)
    nodes_list.append(mesh_list[destiny_index])
    return nodes_list


# Checks message parameters and sends to sending path.
def find_path(conn):
    message_data = conn.recv(2048).decode('UTF-8')
    message_data = message_data.split(' ')

    if message_data[0] != 'FROM':
        print("Origin MAC Address was not given")

    elif message_data[2] != 'TO':
        print("Receiver MAC address was not given.")

    else:
        mc_origin = message_data[1]
        mc_destiny = message_data[3]
        if find_index_by_mac(mc_destiny) == -1:
            print('Receiver node address ' + mc_destiny+ ' was not found in the mesh net: ')
            message = 'NOTFOUND'
        else:
            #Happy path
            node_list = sending_path(mc_origin, mc_destiny)
            message = 'PATH ' + " ".join(str(x) for x in node_list)
            print(message)

            
        conn.send(message.encode("ascii"))
    conn.close()


# This function servers as a mail, for clients that sends a message through the mesh.
def listening_messages():
    socket_main = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_main.bind((config.NET_MESH_IP, config.RECEIVING_MESH_PORT))
    socket_main.listen()

    while True:
        conn, address = socket_main.accept()
        listening = Thread(target=find_path, args=(conn,))
        listening.start()
        listening.join()

# This mail serves clients that want to send a message via a MAC address.
# It receives the MAC address and then finds where that other client is
# to finaly send a message
def info_box():
    socket_main = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_main.bind((config.NET_MESH_IP, config.INFO_MESH_PORT))
    socket_main.listen()

    while True:
        conn, address = socket_main.accept()
        inf = Thread(target=info_mesh, args=(conn,))
        inf.start()
        inf.join()

# This port listens for clients that want to leave the mesh net.
def delete_request():
    socket_main = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_main.bind((config.NET_MESH_IP, config.DELETE_PORT))
    socket_main.listen()

    while True:
        conn, address = socket_main.accept()
        inf = Thread(target=del_mesh, args=(conn,))
        inf.start()
        inf.join()

def main():
    print('Mesh Server is running!')

    register = Thread(target=mesh_server)
    register.start()

    info = Thread(target=info_box)
    info.start()

    messages_server = Thread(target=listening_messages)
    messages_server.start()

    delete = Thread(target=delete_request)
    delete.start()

    register.join()
    messages_server.join()


if __name__ == '__main__':
    main()
