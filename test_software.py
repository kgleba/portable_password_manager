import unittest

import ffpass

import firefox_connector
import login_crypt


class TestSoftware(unittest.TestCase):
    def test_key_retrieval(self):
        key = firefox_connector.get_key()
        self.assertEqual(key, ffpass.getKey(firefox_connector.WORKDIR))

    def test_login_encryption(self):
        test_password = 'vsosh2024'
        test_data = {'login': 'password'}

        login_crypt.init_crypto(test_password)
        login_crypt.encrypt_logins(test_data)

        self.assertEqual(login_crypt.decrypt_logins(), test_data)


if __name__ == '__main__':
    unittest.main()
