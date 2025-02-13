from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import time

PORT = 8025


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add proper live reload injection
        if self.path.endswith('.html'):
            self.send_header('Content-Type', 'text/html')
            # Inject livereload script directly into HTML
            self.send_header('Refresh', '1; url=http://localhost:8023' + self.path)
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        # Add live reload script injection
        if self.path.endswith('.html'):
            super().do_GET()
            return
            
        super().do_GET()

if __name__ == '__main__':
    web_dir = os.path.join(os.path.dirname(__file__), 'webapp')
    os.chdir(web_dir)
    
    print(f"Serving at http://localhost:{PORT}")
    print("Auto-reload enabled - changes will refresh browser")
    HTTPServer(('', PORT), Handler).serve_forever() 