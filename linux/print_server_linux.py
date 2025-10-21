import http.server
import socketserver
import json
import base64
import subprocess
import os
import time
import ssl
from io import BytesIO
from PIL import Image

# --- CONFIGURACIÓN ---
PRINTER_NAME = "star"
TEMP_DIR = "/tmp/"

# Configuración del servidor
HOST = 'localhost'
PORT = 8000
CERTFILE = 'cert.pem'
KEYFILE = 'key.pem'

class PrinterRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps({'message': message}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/print':
            ticket_image_path = None
            try:
                content_length = int(self.headers.get('content-length', 0))
                post_data_bytes = self.rfile.read(content_length)
                data = json.loads(post_data_bytes.decode('utf-8'))

                image_base64 = data.get('image')
                if not image_base64:
                    self._send_response(400, "No se recibió una imagen en base64.")
                    return

                image_data = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data))

                ticket_image_path = os.path.join(TEMP_DIR, "ticket_{}.png".format(int(time.time() * 1000)))
                image.save(ticket_image_path)
                
                # Imprimir el archivo de imagen
                command = ['lp', '-d', PRINTER_NAME, ticket_image_path]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    self._send_response(200, "Ticket de imagen enviado a la impresora.")
                else:
                    self._send_response(500, "Error de CUPS: " + stderr.decode('utf-8'))

            except Exception as e:
                self._send_response(500, "Error al generar la imagen: {}".format(e))
            finally:
                if ticket_image_path and os.path.exists(ticket_image_path):
                    os.remove(ticket_image_path)
        else:
            self._send_response(404, "Endpoint no encontrado.") 
        return

def run_server():
    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, PrinterRequestHandler)

    # Configurar SSL
    if os.path.exists(CERTFILE) and os.path.exists(KEYFILE):
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        except AttributeError:
            # Fallback para versiones antiguas de Python
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(CERTFILE, KEYFILE)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print("Servidor de impresión de imágenes iniciado en https://{}:{}".format(HOST, PORT))
    else:
        print("Archivos de certificado no encontrados. Generando certificado autofirmado...")
        print("Ejecuta: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        print("Servidor de impresión de imágenes iniciado en http://{}:{}".format(HOST, PORT))

    print("Presiona Ctrl+C para detener el servidor.")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        print("\nServidor detenido.")

if __name__ == '__main__':
    run_server()
