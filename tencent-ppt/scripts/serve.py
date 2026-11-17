#!/usr/bin/env python3
"""
Tencent PPT local dev server.

Drop-in replacement for `python3 -m http.server` that ALSO accepts PUT
requests on *.html files inside the served directory — letting the
in-browser visual editor save changes directly back to the original file
without any permission prompt.

Usage:
    python3 assets/serve.py            # serves cwd on :8080
    python3 assets/serve.py 8765       # custom port
    python3 assets/serve.py 8765 .     # custom port + dir

Safety:
- Bound to 127.0.0.1 only — not reachable from other machines
- CORS scoped to localhost / 127.0.0.1 origins (no wildcard)
- Only paths inside the served root are writable (rejects ../ traversal)
- Only *.html files accept PUT (so you can't overwrite app.js / styles.css
  by mistake; edit those directly with your editor)
- Each PUT auto-backs up the existing file as <name>.YYYYMMDD-HHMMSS.bak.html
  next to the original before overwriting
"""
import os
import re
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# Match http(s)://localhost(:port) and http(s)://127.0.0.1(:port) only
_LOCALHOST_ORIGIN_RE = re.compile(
    r'^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$', re.IGNORECASE
)


class Handler(SimpleHTTPRequestHandler):
    # CORS / cache — only echo localhost origins, never wildcard
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        origin = self.headers.get('Origin', '')
        if origin and _LOCALHOST_ORIGIN_RE.match(origin):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_PUT(self):
        try:
            url_path = urlparse(self.path).path
            target = self.translate_path(url_path)

            root = os.path.realpath(os.getcwd())
            real_target = os.path.realpath(target)

            # 1. Refuse path traversal
            if not (real_target == root or real_target.startswith(root + os.sep)):
                return self._json_error(403, 'outside project root')

            # 2. Only allow *.html
            if not real_target.lower().endswith(('.html', '.htm')):
                return self._json_error(403, 'PUT only allowed on .html files')

            # 3. Read body
            length = int(self.headers.get('Content-Length', 0) or 0)
            if length <= 0:
                return self._json_error(400, 'empty body')
            body = self.rfile.read(length)

            # 4. Backup existing
            backup_name = None
            if os.path.exists(real_target):
                ts = time.strftime('%Y%m%d-%H%M%S')
                base, ext = os.path.splitext(real_target)
                backup_name = f'{base}.{ts}.bak{ext}'
                try:
                    with open(real_target, 'rb') as src, open(backup_name, 'wb') as dst:
                        dst.write(src.read())
                except Exception as e:
                    sys.stderr.write(f'[serve.py] backup failed: {e}\n')
                    backup_name = None

            # 5. Write atomically (write tmp, rename)
            tmp = real_target + '.tmp.' + str(os.getpid())
            with open(tmp, 'wb') as f:
                f.write(body)
            os.replace(tmp, real_target)

            sys.stdout.write(
                f'[serve.py] PUT {url_path}  ({len(body)} bytes)'
                + (f' · backup: {os.path.basename(backup_name)}' if backup_name else '')
                + '\n'
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            payload = b'{"ok":true,"bytes":' + str(len(body)).encode() + b'}'
            self.wfile.write(payload)
        except Exception as e:
            sys.stderr.write(f'[serve.py] PUT error: {e}\n')
            self._json_error(500, str(e))

    def _json_error(self, code, msg):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        body = ('{"ok":false,"error":' + repr(msg).replace("'", '"') + '}').encode()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # quieter access log
        sys.stdout.write('[serve.py] ' + (fmt % args) + '\n')


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    if len(sys.argv) > 2:
        os.chdir(sys.argv[2])
    print(f'Tencent PPT dev server')
    print(f'  → http://localhost:{port}/')
    print(f'  → root: {os.getcwd()}')
    print(f'  → PUT enabled on *.html (auto-backup, in-place save)')
    print(f'  Press Ctrl+C to stop.')
    try:
        ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()
