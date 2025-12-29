import subprocess
import os
import time
import Jetson.GPIO as GPIO
import json
import sys
import http.server
import ssl
import base64



# Variablen für Server
system_count = 0
USERNAME = "yusuf"
PASSWORD = "Yusuf6161_"



# HTTPS Server starten (damit man per Handy Videos oder Logs downloaden kann)
class SecureHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTPS-Server mit Passwortschutz"""
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(400)
        self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
        self.end_headers()
        self.wfile.write(b'Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'HTTP 401 - Unauthorized')
    
    def do_GET(self):
        if self.headers.get('Authorization') is None:
            self.do_AUTHHEAD()
            return
        
        auth_header = self.headers.get('Authorization')
        auth_decoded = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
        username, password = auth_decoded.split(':')
        
        if username == USERNAME and password == PASSWORD:
            log("HTTP-Req Zugriff!")
            super().do_GET()
        else:
            log(f"HTTP-Req Zugriff verweigert: {username} {password}")
            self.do_AUTHHEAD()


# Log-System
def log(message):
    global system_count
    try:
        with open('/proc/uptime', 'r') as f:
            TIME = float(f.readline().split()[0])
    except Exception as e:
        with open('log.txt', 'a') as file:
            file.write(f"{system_count} <<MAIN>> ERROR! CANT ACCESS SYSTEM-TIME!\n")
        TIME = 0
    TIME = round(TIME / 60, 1)
    with open('log.txt', 'a') as file:
        file.write(f"{system_count} <<MAIN>> {message}  *** {TIME} min\n")



if __name__ == '__main__':
    # Lese die Werte aus variables.json
    with open('variables.json', 'r') as file:
        variables = json.load(file)
    system_count = variables["system_count"]
    video_count = variables["video_count"]

    # HTTPS Server starten (damit man per Handy Videos oder Logs downloaden kann)
    log("Server gestartet!")
    server_address = ('0.0.0.0', 8443)
    httpd = http.server.HTTPServer(server_address, SecureHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile="server.key", certfile="server.crt", server_side=True)
    httpd.serve_forever()
   





