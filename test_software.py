import unittest
import ffpass
import firefox_connector


class TestSoftware(unittest.TestCase):
    def test_key_retrieval(self):
        key = firefox_connector.get_key()
        self.assertEqual(key, ffpass.getKey(firefox_connector.WORKDIR))


if __name__ == '__main__':
    unittest.main()
