import sys
from zlib import crc32

# Python2 CRC is signed, Python3 is unsigned
# This function forces signed because users have exported data with signed CRCs already, so
#  we want to ensure that running in Python3 will not result in different CRCs
def signedCrc32(data):
    crcResult = crc32(data)

    if sys.version_info[0] >= 3:
        # Convert unsigned into signed
        # Yes, this is awful
        # See https://stackoverflow.com/questions/1375897/how-to-get-the-signed-integer-value-of-a-long-in-python
        return ((crcResult & 0xffffffff) ^ 0x80000000) - 0x80000000
    return crcResult
