# WINDOWS

Descargar Python
Buscar la versión para el portatil
https://www.python.org/downloads/windows/
versión usada
https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe


Instalar librerías que usa el código fuente en
pip install Flask Pillow pywin32
si no funciona el pip usa este otro comando en windows
py -m pip install Flask Pillow pywin32

Instalar la impresora y configurar como impresora por defecto
https://ftp.epson.com/drivers/pos/APD_610_T20IV_WM.exe



# LINUX


Probar comunicación con la impresora
```
echo "test" | lp -d star
```

Verificar que el puerto 8000 no se este usando
```
lsof -i :8000
```

Crear ssh key para github
```
ssh-keygen -t ed25519 -C "soporte@siberian.com.ec"
cat /root/.ssh/id_ed25519.pub
```

clonar el repositorio
```
cd /opt
clone git@github.com:siberianEC/puntodecanje_printer.git .
```

Generar certificado SSL para HTTPS (Los archivos cert.pem y key.pem deben estar en el mismo directorio que el script.)
```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```


Crear el servicio copie el contenido del archivo servicio en la caperta linux de este repositorio
```
sudo nano /etc/systemd/system/printer_server.service
```

Inicia el servicio
```
sudo systemctl start printer_server.service
sudo systemctl enable printer_server.service
```


