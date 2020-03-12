from http.server import HTTPServer, SimpleHTTPRequestHandler

server_address = ('127.0.0.1', 8999)
httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
httpd.serve_forever()