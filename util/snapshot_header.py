from enum import Enum


class SnapshotFormat(Enum):
    JPEG = 0
    RAW_GRBG8 = 1
    RAW_BGGR8 = 2


class SnapshotHeader:
    MAGIC = b"\x01\x02\x03\x04\x05\x06"

    def __init__(self, buffer):
        self.buffer = buffer

        self._parse()

    def _parse(self):
        # magic (6 bytes)
        self.magic = self.buffer[0:6]

        # format (1 byte)
        self.format = SnapshotFormat(self.buffer[6])

        # interleaving (1 byte)
        self.interleaving = self.buffer[7]

        # width (2 byte, big endian)
        self.width = int.from_bytes(self.buffer[8:10], "big")

        # height (2 byte, big endian)
        self.height = int.from_bytes(self.buffer[10:12], "big")

        # image size (4 byte, big endian)
        self.image_size = int.from_bytes(self.buffer[12:16], "big")

    def valid(self):
        if self.magic != SnapshotHeader.MAGIC:
            print(f"[ERROR] Invalid magic: {self.magic}, expected: {SnapshotHeader.MAGIC}")
            return False

        return True
