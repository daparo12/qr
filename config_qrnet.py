import configparser
import sys

config_file = 'config.ini'

class ConfigQRNet():

    #Config of transmission device
    TRANSMISSION_DEVICE_IP = ""
    TRANSMISSION_PORT = 0

    #Config of server IRC
    SERVER_IRC_IP = ""
    LISTENING_IRC_PORT = 0

    #Config of net mesh
    REGISTRY_MESH_PORT = 0
    RECEIVING_MESH_PORT = 0
    INFO_MESH_PORT = 0
    NET_MESH_IP = ""
    DELETE_PORT = 0

    def __init__(self):

        self.TRANSMISSION_DEVICE_IP = "127.0.0.1"
        self.TRANSMISSION_PORT = 1698
        self.SERVER_IRC_IP = "127.0.0.1"
        self.LISTENING_IRC_PORT = 6667


        self.REGISTRY_MESH_PORT = 9122
        self.RECEIVING_MESH_PORT = 9129
        self.INFO_MESH_PORT = 9697
        self.NET_MESH_IP = "127.0.0.1"
        self.DELETE_PORT = 9798
