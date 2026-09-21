"""Unit tests for NumWorks Epsilon storage parser and builder."""

import unittest
from numworks.storage import Storage, Script, Record, StorageError
from numworks.constants import MAGIC_STORAGE_RECORD


class TestStorage(unittest.TestCase):
    """Test suite for storage record manipulation."""

    def test_record_build(self):
        content = b"\x01print('Hello')\x00"
        raw = Storage.build_record("hello.py", content)
        # Size should be 2 + len("hello.py\0") + len(content)
        expected_size = 2 + 9 + len(content)
        self.assertEqual(len(raw), expected_size)
        self.assertEqual(raw[2:11], b"hello.py\x00")

    def test_storage_buffer_roundtrip(self):
        records = [
            Record(name="gp.sys", content=b"\x00sys1\x00", size=13),
            Record(name="test.py", content=b"\x01x = 42\x00", size=17),
        ]
        total_size = 256
        buf = Storage.build_storage_buffer(records, total_size=total_size)

        # Buffer length must be total_size + 8 (start + end magic)
        self.assertEqual(len(buf), total_size + 8)
        self.assertTrue(buf.startswith(MAGIC_STORAGE_RECORD))
        self.assertTrue(buf.endswith(MAGIC_STORAGE_RECORD))

        # Parse buffer back
        storage = Storage(buf)
        self.assertEqual(len(storage.records), 2)
        self.assertEqual(storage.records[0].name, "gp.sys")
        self.assertEqual(storage.records[1].name, "test.py")

        scripts = storage.get_scripts()
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0].name, "test.py")
        self.assertEqual(scripts[0].code, "x = 42\x00")
        self.assertTrue(scripts[0].auto_import)

    def test_storage_buffer_overflow(self):
        records = [
            Record(name="big.py", content=b"A" * 500, size=520),
        ]
        with self.assertRaises(StorageError):
            Storage.build_storage_buffer(records, total_size=100)

    def test_storage_missing_magic(self):
        bad_buf = b"\x00" * 64
        with self.assertRaises(StorageError):
            Storage(bad_buf)


if __name__ == "__main__":
    unittest.main()
