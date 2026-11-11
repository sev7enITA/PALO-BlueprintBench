"""Offline acquisition guards, with a mocked HTTPS response (no network calls)."""
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from acquire import acquire


class Response(io.BytesIO):
    url = 'https://public.example/document.pdf'
    headers = {'Content-Type': 'application/pdf'}


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / 'acquired'
        self.body = b'%PDF-1.4\nSynthetic acquisition test, no source document.\n'

    def tearDown(self):
        self.tmp.cleanup()

    def registry(self, **kw):
        return {'families': [{'id': 'synthetic', 'seed_download_url': Response.url, **kw}]}

    def test_expected_hash_checked(self):
        with patch('acquire.urllib.request.urlopen', return_value=Response(self.body)):
            rows = acquire(self.registry(expected_sha256=hashlib.sha256(self.body).hexdigest()), self.output)
        self.assertEqual(rows[0]['status'], 'seed_downloaded')
        self.assertTrue(rows[0]['expected_hash_verified'])
        self.assertFalse(rows[0]['heldout'])

    def test_mismatch_removes_partial(self):
        with patch('acquire.urllib.request.urlopen', return_value=Response(self.body)):
            rows = acquire(self.registry(expected_sha256='0' * 64), self.output)
        self.assertEqual(rows[0]['status'], 'download_failed')
        self.assertEqual(list(self.output.glob('*.part')), [])
        self.assertEqual(list(self.output.glob('*.pdf')), [])

    def test_http_and_credentials_rejected_without_request(self):
        for number, url in enumerate(['http://public.example/x.pdf', 'https://user:secret@public.example/x.pdf']):
            with patch('acquire.urllib.request.urlopen') as network:
                rows = acquire(self.registry(seed_download_url=url), self.output / str(number))
            network.assert_not_called()
            self.assertEqual(rows[0]['status'], 'download_failed')

    def test_html_response_is_not_a_document(self):
        with patch('acquire.urllib.request.urlopen', return_value=Response(b'<html>Access denied</html>')):
            rows = acquire(self.registry(), self.output)
        self.assertEqual(rows[0]['status'], 'download_failed')


if __name__ == '__main__':
    unittest.main()
