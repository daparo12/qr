class QRNode(object):

    def __init__(self, mac_address: str, ip_address: str, port: str):
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.port = port

    def __repr__(self):
        response = "{0} {1}".format(self.ip_address, self.port)
        return response