
class Frame:
    PROTOCOL_VERSION = '0.1'
    CHECKSUM = '161618'

    def new_frame(self, mac_address, message):

        new_frame = mac_address + ','+ self.PROTOCOL_VERSION + ',' + self.CHECKSUM + ',' + str(message)

        return new_frame




