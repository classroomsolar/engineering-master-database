"""Read-only serving for the public engineering deployment directory.

Use a managed HTTPS static host for production TLS and traffic management.
This server never serves the repository or its private finance application.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse


PUBLIC_ROOT = Path(__file__).resolve().parents[1] / 'dist'
CSP = (
    "default-src 'self'; script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
    "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


class CatalogHandler(SimpleHTTPRequestHandler):
    server_version = 'EngineeringCatalog/1.0'
    sys_version = ''
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.js': 'text/javascript',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        try:
            path = unquote(urlsplit(self.path).path, errors='strict')
            parts = Path(path.lstrip('/')).parts
            root = Path(self.directory).resolve()
            candidate = root.joinpath(*parts).resolve()
            if candidate == root:
                candidate = (root / 'index.html').resolve()
            if any(part.startswith('.') for part in parts) or not candidate.is_relative_to(root):
                self.send_error(403, 'This path is outside the public catalog')
                return None
            if candidate.is_dir() and candidate != root:
                self.send_error(404, 'Directory listings are unavailable')
                return None
        except (UnicodeError, ValueError, OSError):
            self.send_error(400, 'Invalid catalog path')
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404, 'Directory listings are unavailable')
        return None


def make_server(bind='127.0.0.1', port=8000, directory=PUBLIC_ROOT):
    directory = Path(directory).resolve()
    if not (directory / 'index.html').is_file() or not (directory / 'data/catalog.js').is_file():
        raise ValueError('Public root must contain index.html and data/catalog.js')
    return ThreadingHTTPServer((bind, port), partial(CatalogHandler, directory=str(directory)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('port must be between 0 and 65535')
    with make_server(args.bind, args.port) as server:
        print(f'Serving the engineering catalog from {PUBLIC_ROOT}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
