import unittest
from src.sub_enum.utils import validate_domain

class TestUtils(unittest.TestCase):
    def test_validate_domain_valid(self):
        self.assertEqual(validate_domain("example.com"), "example.com")
        self.assertEqual(validate_domain("sub.example.com"), "sub.example.com")
        self.assertEqual(validate_domain("http://example.com"), "example.com")
        self.assertEqual(validate_domain("https://example.com/"), "example.com")

    def test_validate_domain_invalid(self):
        self.assertIsNone(validate_domain("invalid"))
        self.assertIsNone(validate_domain("http://"))
        self.assertIsNone(validate_domain(""))
        
if __name__ == '__main__':
    unittest.main()
