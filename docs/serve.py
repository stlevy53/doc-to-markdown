"""Local dev server with COOP/COEP headers for Pyodide SharedArrayBuffer support."""
import http.server
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class COIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request noise


print(f"Serving at http://localhost:{PORT}  (Ctrl+C to stop)")
http.server.HTTPServer(("", PORT), COIHandler).serve_forever()
