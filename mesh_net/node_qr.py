class QRNode(object):
    '''
    This node contains information about the new connections of the mesh net.
    '''

    def __init__(self, mac_address: str, ip_address: str, port: str):
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.port = port


    def __repr__(self):
        '''
        This method allows to represent QRNode object a string.
        '''    
        response = "{0} {1}".format(self.ip_address, self.port)
        return response