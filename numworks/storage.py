"""Epsilon record storage parser and builder."""

from dataclasses import dataclass
from typing import List, Optional
import struct

from .constants import MAGIC_STORAGE_RECORD


class StorageError(Exception):
    """Exception raised for record storage parsing/building errors."""
    pass


@dataclass
class Script:
    """Represents a Python script on the NumWorks calculator."""
    name: str
    code: str
    auto_import: bool = False
    size: int = 0


@dataclass
class Record:
    """Represents a raw record in NumWorks storage."""
    name: str
    content: bytes
    size: int


class Storage:
    """Parses and manipulates NumWorks Epsilon storage buffer."""

    def __init__(self, raw_buffer: Optional[bytes] = None):
        """Parse raw storage buffer."""
        self.raw_data = raw_buffer
        self.records: List[Record] = []
        if raw_buffer is None:
            return
        self._parse()

    def _parse(self) -> None:
        """Parse raw memory buffer into records."""
        data = self.raw_data

        # Check start and end boundaries
        if len(data) < len(MAGIC_STORAGE_RECORD) * 2:
            raise StorageError("Storage buffer is too small")

        if not data.startswith(MAGIC_STORAGE_RECORD):
            raise StorageError(f"Storage buffer missing start magic: {data[:4].hex()}")

        if not data.endswith(MAGIC_STORAGE_RECORD):
            raise StorageError(f"Storage buffer missing end magic: {data[-4:].hex()}")

        # Content is between the start and end magics
        payload = data[len(MAGIC_STORAGE_RECORD) : -len(MAGIC_STORAGE_RECORD)]

        offset = 0
        while offset + 2 <= len(payload):
            record_size = struct.unpack_from("<H", payload, offset)[0]
            if record_size == 0:
                # 0x0000 marks end of records list
                break

            if offset + record_size > len(payload):
                # Malformed record beyond payload boundary
                break

            record_bytes = payload[offset : offset + record_size]

            # Find null terminator for name starting at offset 2
            name_end = record_bytes.find(b"\x00", 2)
            if name_end == -1:
                break

            name = record_bytes[2:name_end].decode("utf-8", errors="replace")
            content = record_bytes[name_end + 1 :]

            self.records.append(Record(name=name, content=content, size=record_size))
            offset += record_size

    def get_scripts(self) -> List[Script]:
        """Extract all Python scripts (.py) from records."""
        scripts = []
        for rec in self.records:
            if rec.name.endswith(".py"):
                auto_import = False
                code_bytes = rec.content
                if len(rec.content) > 0:
                    auto_import = rec.content[0] == 0x01
                    code_bytes = rec.content[1:]
                code_str = code_bytes.decode("utf-8", errors="replace")
                scripts.append(Script(
                    name=rec.name,
                    code=code_str,
                    auto_import=auto_import,
                    size=rec.size,
                ))
        return scripts

    def get_record(self, name: str) -> Optional[Record]:
        """Find a record by name."""
        for rec in self.records:
            if rec.name == name:
                return rec
        return None

    def total_used_bytes(self) -> int:
        """Calculate total bytes occupied by active records."""
        return sum(rec.size for rec in self.records) + 2  # plus 2 bytes end marker

    @staticmethod
    def build_record(name: str, content: bytes) -> bytes:
        """Build binary representation of a single record."""
        name_bytes = name.encode("utf-8") + b"\x00"
        record_size = 2 + len(name_bytes) + len(content)
        header = struct.pack("<H", record_size)
        return header + name_bytes + content

    @staticmethod
    def build_storage_buffer(records: List[Record], total_size: int = 4096) -> bytes:
        """Construct full storage buffer bounded by MAGIC_STORAGE_RECORD."""
        payload = bytearray()
        for rec in records:
            payload.extend(Storage.build_record(rec.name, rec.content))
        # Add 2-byte zero terminator
        payload.extend(b"\x00\x00")

        # Pad payload to total_size
        if len(payload) < total_size:
            payload.extend(b"\x00" * (total_size - len(payload)))
        elif len(payload) > total_size:
            raise StorageError(f"Records size ({len(payload)}) exceeds storage size ({total_size})")

        return MAGIC_STORAGE_RECORD + bytes(payload[:total_size]) + MAGIC_STORAGE_RECORD
