# -- coding: utf-8 --
import os
import sys
import base64
from io import BytesIO
import win32print
import win32ui
from flask import Flask, request, jsonify
from PIL import Image, ImageWin
import traceback

# --- CONFIGURACIÓN ---
PRINTER_NAME = "EPSON TM-T20IV Receipt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERTFILE = os.path.join(SCRIPT_DIR, 'cert.pem')
KEYFILE = os.path.join(SCRIPT_DIR, 'key.pem')

# --- APLICACIÓN FLASK ---
app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response

def print_image_object(pil_image, printer_name):
    """
    Envía un objeto de imagen de Pillow directamente a la impresora.
    """
    try:
        if printer_name is None:
            printer_name = win32print.GetDefaultPrinter()

        print(f"Enviando a la impresora: '{printer_name}'")

        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)

        printable_width = hDC.GetDeviceCaps(110)

        img_width, img_height = pil_image.size
        if img_width > printable_width:
            ratio = printable_width / img_width
            new_width = printable_width
            new_height = int(img_height * ratio)
            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
            img_width, img_height = pil_image.size

        hDC.StartDoc("Ticket de Compra")
        hDC.StartPage()

        dib = ImageWin.Dib(pil_image)
        dib.draw(hDC.GetSafeHdc(), (0, 0, img_width, img_height))

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()

        return True, f"Ticket enviado a '{printer_name}'."

    except Exception as e:
        print(f"Error al imprimir con pywin32: {e}")
        traceback.print_exc()
        return False, str(e)


@app.route('/print', methods=['POST'])
def handle_print_request():
    """
    Endpoint que recibe una imagen en base64 y la imprime.
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "Falta el campo 'image' en el cuerpo JSON."}), 400

        image_base64 = data['image']

        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

        success, message = print_image_object(image, PRINTER_NAME)
        
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": f"No se pudo imprimir el ticket. Razón: {message}"}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error general del servidor: {e}"}), 500
    finally:
        pass

if __name__ == '__main__':
    # Verificar que pywin32 esté instalado
    try:
        import win32print
        print("pywin32 detectado. La impresión se realizará por nombre de impresora.")
    except ImportError:
        print("ERROR: La librería 'pywin32' no está instalada. Ejecute 'pip install pywin32' para continuar.")
        sys.exit(1)

    # Configurar HTTPS si existen los certificados
    if os.path.exists(CERTFILE) and os.path.exists(KEYFILE):
        print("Servidor de impresión de tickets iniciado en https://localhost:8000")
        print("Esperando peticiones POST en /print con JSON: {'image': 'base64...'}")
        app.run(host='0.0.0.0', port=8000, ssl_context=(CERTFILE, KEYFILE))
    else:
        print("Archivos de certificado no encontrados. Generando certificado autofirmado...")
        print("Ejecuta: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        print("Servidor de impresión de tickets iniciado en http://localhost:8000")
        print("Esperando peticiones POST en /print con JSON: {'image': 'base64...'}")
        app.run(host='0.0.0.0', port=8000)


