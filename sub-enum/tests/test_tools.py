import unittest

from src.sub_enum.tools import parse_httpx_output


class TestTools(unittest.TestCase):
    def test_parse_httpx_output(self):
        lines = [
            'https://admin.example.com | 200 | text/html',
            'http://test.example.com | 404 | text/html',
            'Some other text https://api.example.com/path?query=1 extra',
            'no-url-here'
        ]

        urls = parse_httpx_output(lines)
        expected = {
            'https://admin.example.com',
            'http://test.example.com',
            'https://api.example.com/path?query=1'
        }
        self.assertEqual(urls, expected)


if __name__ == '__main__':
    unittest.main()
