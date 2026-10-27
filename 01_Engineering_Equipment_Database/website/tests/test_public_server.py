"""Real HTTP checks of the public engineering-only file boundary."""
import http.client
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'tools' / 'serve.py'
server_module = None
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('catalog_public_server', MODULE)
    server_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server_module)


class PublicServerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(server_module, 'Engineering-only server is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'public'
        self.root.mkdir()
        (self.root/'index.html').write_text('<!doctype html><title>Catalog</title>')
        (self.root/'data').mkdir()
        (self.root/'data/catalog.js').write_text('window.DB_CATALOG={};')
        (self.root/'spreadsheets').mkdir()
        (self.root/'spreadsheets/example.xlsx').write_bytes(b'original spreadsheet bytes')
        (self.root/'.env').write_text('must not be served')
        (self.root/'unused').mkdir()
        (self.root.parent/'private.txt').write_text('private document')
        (self.root/'escape.txt').symlink_to(self.root.parent/'private.txt')
        self.server = server_module.make_server('127.0.0.1', 0, self.root)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, method='GET'):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        c.request(method, path)
        response = c.getresponse()
        result = response.status, response.headers, response.read()
        c.close()
        return result

    def test_html_and_source_javascript_are_served(self):
        status, headers, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'<title>Catalog</title>', body)
        status, headers, body = self.request('/data/catalog.js?v=1')
        self.assertEqual(status, 200)
        self.assertIn('javascript', headers['Content-Type'])
        self.assertEqual(body, b'window.DB_CATALOG={};')

    def test_original_excel_download_has_correct_type_and_bytes(self):
        status, headers, body = self.request('/spreadsheets/example.xlsx')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertEqual(body, b'original spreadsheet bytes')

    def test_hidden_files_and_directory_listing_are_denied(self):
        for path in ['/.env', '/.git/config', '/unused/']:
            self.assertIn(self.request(path)[0], [403,404], path)

    def test_parent_traversal_and_symlink_escape_are_denied(self):
        for path in ['/../private.txt', '/%2e%2e/private.txt', '/escape.txt']:
            status, headers, body = self.request(path)
            self.assertIn(status, [403,404], path)
            self.assertNotIn(b'private document', body)

    def test_root_index_symlink_cannot_escape_public_directory(self):
        (self.root/'index.html').unlink()
        (self.root/'index.html').symlink_to(self.root.parent/'private.txt')
        status, headers, body = self.request('/')
        self.assertEqual(status, 403)
        self.assertNotIn(b'private document', body)

    def test_public_responses_have_browser_security_headers(self):
        for path in ['/', '/missing.js']:
            status, headers, body = self.request(path)
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(headers['X-Frame-Options'], 'DENY')
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_head_has_no_body_and_mutation_requests_are_unsupported(self):
        self.assertEqual(self.request('/', 'HEAD')[2], b'')
        self.assertEqual(self.request('/', 'POST')[0], 501)


if __name__ == '__main__':
    unittest.main()
