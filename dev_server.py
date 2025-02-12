from livereload import Server, shell
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading

PORT = 8007

class DualServer:
    def __init__(self):
        # Create static file server
        self.httpd = TCPServer(("", PORT), SimpleHTTPRequestHandler)
        
        # Create livereload server
        self.lr_server = Server()
        self.lr_server.watch('webapp/*.*', delay=1)
        self.lr_server.watch('*.py', delay=1)

    def start(self):
        print(f"Starting development server at http://localhost:{PORT}")
        print("Auto-reload is enabled. Save files to trigger reload.")
        
        # Start HTTP server in a separate thread
        server_thread = threading.Thread(target=self.httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Start livereload server
        self.lr_server.serve(port=35729)  # Livereload default port

if __name__ == '__main__':
    server = DualServer()
    server.start() 