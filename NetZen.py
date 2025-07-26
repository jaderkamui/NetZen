import os
import subprocess
import time
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import sys
import json
import paramiko

# Rutas y archivos
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

logo_path = os.path.join(base_path, "sonda_logo.png")
plink_path = os.path.join(base_path, "plink.exe")
ruta_base = r"C:\\reportes cisco"
sesion_file = os.path.join(base_path, "usuario_cache.json")

# Comandos y sus nombres para archivos
comandos = {
    "show int transceiver detail": "ATENUACIONES",
    "show int counters errors": "COUNTER ERROR",
    "show log": "LOG",
    "show run": "RUNNING CONFIG"
}

# Variables globales para usuario y contraseña
usuario = ""
contrasena = ""
checkbox_comandos = {}
conexion_cache = {}

# Funciones para guardar y cargar usuario en cache local (json)
def guardar_usuario_cache():
    with open(sesion_file, "w") as f:
        json.dump({"usuario": usuario}, f)

def cargar_usuario_cache():
    if os.path.exists(sesion_file):
        with open(sesion_file) as f:
            data = json.load(f)
            return data.get("usuario", "")
    return ""

# Ventana emergente para ingresar credenciales
def pedir_credenciales_popup():
    global usuario, contrasena
    popup = ctk.CTkToplevel(app)
    popup.title("Credenciales de acceso")
    popup.geometry("350x300")
    popup.grab_set()
    popup.configure(fg_color="#1a1a1a")

    ctk.CTkLabel(popup, text="Usuario:").pack(pady=5)
    entry_user = ctk.CTkEntry(popup)
    entry_user.pack()
    entry_user.insert(0, cargar_usuario_cache())

    ctk.CTkLabel(popup, text="Contraseña:").pack(pady=5)
    entry_pass = ctk.CTkEntry(popup, show="*")
    entry_pass.pack()

    def toggle_pass():
        entry_pass.configure(show="" if mostrar_pass_var.get() else "*")

    mostrar_pass_var = ctk.BooleanVar()
    ctk.CTkCheckBox(popup, text="Mostrar contraseña", variable=mostrar_pass_var, command=toggle_pass).pack(pady=5)

    def guardar_y_cerrar():
        global usuario, contrasena
        usuario = entry_user.get().strip()
        contrasena = entry_pass.get()
        if not usuario or not contrasena:
            messagebox.showwarning("Datos incompletos", "Debe ingresar usuario y contraseña.")
            return
        guardar_usuario_cache()
        popup.destroy()
        actualizar_botones_estado()

    ctk.CTkButton(popup, text="Aceptar", command=guardar_y_cerrar).pack(pady=10)

# Actualizar estado de botones según si hay credenciales
def actualizar_botones_estado():
    if usuario and contrasena:
        btn_probar.configure(state="normal")
        btn_generar.configure(state="normal")
    else:
        btn_probar.configure(state="disabled")
        btn_generar.configure(state="disabled")

# Función para agregar líneas en el log
def log(mensaje):
    log_output.configure(state="normal")
    log_output.insert("end", mensaje + "\n")
    log_output.see("end")
    log_output.configure(state="disabled")
    app.update()

# Abrir carpeta raíz de reportes
def abrir_carpeta():
    os.makedirs(ruta_base, exist_ok=True)
    os.startfile(ruta_base)

# Cargar IPs desde archivo txt
def cargar_ips_txt():
    archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
    if archivo:
        with open(archivo, "r") as f:
            contenido = f.read()
            entry_ips.delete("1.0", "end")
            entry_ips.insert("1.0", contenido)

# Ejecutar comando via SSH con Paramiko
def ejecutar_comando_ssh(ip, comando):
    salida = ""
    try:
        cliente = paramiko.SSHClient()
        cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente.connect(ip, username=usuario, password=contrasena, timeout=10, look_for_keys=False, allow_agent=False)
        canal = cliente.invoke_shell()
        canal.send("terminal length 0\n")
        time.sleep(1)
        canal.send(f"{comando}\n")
        time.sleep(3)
        output = canal.recv(65535).decode("utf-8", errors="ignore")
        cliente.close()
        salida = output
    except Exception as e:
        log(f"❌ Error SSH con {ip}: {str(e)}")
    return salida

# Obtener hostname del dispositivo (Telnet o SSH)
def obtener_hostname(ip):
    global conexion_cache
    comandos_hostname = f"{usuario}\n{contrasena}\nterminal length 0\nshow run | include hostname\nexit\n"

    # Intento Telnet con Plink
    try:
        result = subprocess.run([
            plink_path, "-telnet", ip, "-P", "23", "-batch"
        ], input=comandos_hostname.encode(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        salida = result.stdout.decode("utf-8", errors="ignore")
        if "hostname" in salida.lower():
            conexion_cache[ip] = "telnet"
            for linea in salida.splitlines():
                if linea.lower().strip().startswith("hostname"):
                    partes = linea.split()
                    if len(partes) >= 2:
                        return partes[1].strip()
    except Exception as e:
        log(f"⚠️ Error TELNET con {ip}: {str(e)}")

    # Intento SSH
    try:
        salida_ssh = ejecutar_comando_ssh(ip, "show run | include hostname")
        if "hostname" in salida_ssh.lower():
            conexion_cache[ip] = "ssh"
            for linea in salida_ssh.splitlines():
                if linea.lower().strip().startswith("hostname"):
                    partes = linea.split()
                    if len(partes) >= 2:
                        return partes[1].strip()
    except Exception as e:
        log(f"⚠️ Error SSH con {ip}: {str(e)}")

    log(f"❌ No se pudo obtener el hostname de {ip}")
    return f"{ip.replace('.', '_')}_SIN_HOSTNAME"

# Probar conexión para cada IP
def probar_conexion():
    if not usuario or not contrasena:
        messagebox.showwarning("Faltan Credenciales", "Debe ingresar usuario y contraseña antes de probar conexión.")
        return

    ips = entry_ips.get("1.0", "end").strip().split("\n")
    for ip in ips:
        ip = ip.strip()
        if not ip:
            continue

        log(f"🔍 Probando conexión con {ip}...")
        try:
            resultado = subprocess.run([
                plink_path, "-telnet", ip, "-P", "23", "-batch"
            ], input=f"{usuario}\n{contrasena}\nexit\n".encode(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            if "login" in resultado.stdout.decode("utf-8", errors="ignore").lower() or resultado.returncode != 0:
                raise Exception("Fallo Telnet")
            log(f"✅ Telnet exitoso con {ip}")
            conexion_cache[ip] = "telnet"
            continue
        except:
            log(f"⚠️ Telnet no disponible para {ip}, intentando SSH...")

        try:
            cliente = paramiko.SSHClient()
            cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cliente.connect(ip, username=usuario, password=contrasena, timeout=10, look_for_keys=False, allow_agent=False)
            cliente.close()
            log(f"✅ SSH exitoso con {ip}")
            conexion_cache[ip] = "ssh"
        except Exception as e:
            log(f"❌ Fallo conexión con {ip}: {str(e)}")

# Generar reportes para las IPs y comandos seleccionados
def generar_reportes():
    if not usuario or not contrasena:
        messagebox.showwarning("Faltan Credenciales", "Debe ingresar usuario y contraseña antes de generar reportes.")
        return

    ips = entry_ips.get("1.0", "end").strip().split("\n")
    comandos_seleccionados = [cmd for cmd, cb in checkbox_comandos.items() if cb.get() == 1]

    if not comandos_seleccionados:
        messagebox.showwarning("Sin Comandos", "Debe seleccionar al menos un reporte a generar.")
        return

    for ip in ips:
        ip = ip.strip()
        if not ip:
            continue

        log(f"📡 Generando reportes para {ip}...")
        hostname = obtener_hostname(ip)
        carpeta_host = os.path.join(ruta_base, hostname)
        os.makedirs(carpeta_host, exist_ok=True)

        for cmd in comandos_seleccionados:
            log(f"➡️ Ejecutando: {comandos[cmd]} en {hostname}")
            salida = ""

            if conexion_cache.get(ip) == "telnet":
                try:
                    entrada = f"{usuario}\n{contrasena}\nterminal length 0\n{cmd}\nexit\n"
                    resultado = subprocess.run([
                        plink_path, "-telnet", ip, "-P", "23", "-batch"
                    ], input=entrada.encode(), stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
                    salida = resultado.stdout.decode("utf-8", errors="ignore")
                except Exception as e:
                    log(f"❌ Error TELNET al ejecutar comando: {str(e)}")

            elif conexion_cache.get(ip) == "ssh":
                salida = ejecutar_comando_ssh(ip, cmd)

            if salida:
                nombre_archivo = f"{hostname} {comandos[cmd]}.txt"
                ruta_archivo = os.path.join(carpeta_host, nombre_archivo)
                with open(ruta_archivo, "w", encoding="utf-8") as f:
                    f.write(salida)
                log(f"✅ Guardado: {nombre_archivo}")
            else:
                log(f"⚠️ No se obtuvo salida para: {comandos[cmd]} en {hostname}")

    log("✔️ Proceso finalizado.")

# Ventana de ayuda con información y comandos
def mostrar_ayuda():
    ayuda = ctk.CTkToplevel(app)
    ayuda.title("Información y Ayuda")
    ayuda.geometry("500x400")
    ayuda.grab_set()
    ayuda.configure(fg_color="#1e1e1e")

    texto_ayuda = """
Netzen - Reportes Automáticos Cisco
Versión: 2.7
Desarrollado por: Jader Muñoz
Contacto: jmunozra@sonda.com

Ayuda memoria de comandos:

- show run  ➜  [HOSTNAME] RUNNING CONFIG.txt
- show log  ➜  [HOSTNAME] LOG.txt
- show int transceiver detail  ➜  [HOSTNAME] ATENUACIONES.txt
- show int counters errors     ➜  [HOSTNAME] COUNTER ERROR.txt

Ubicación de reportes:
C:\\reportes cisco\\[HOSTNAME]\\

Este programa conecta vía Telnet o SSH a dispositivos Cisco
y guarda automáticamente los reportes solicitados.
"""
    texto_box = ctk.CTkTextbox(ayuda, wrap="word")
    texto_box.insert("1.0", texto_ayuda.strip())
    texto_box.configure(state="disabled")
    texto_box.pack(padx=20, pady=20, expand=True, fill="both")

# --------------------- Inicio interfaz gráfica ----------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Netzen - Reportes Automáticos - Desarrollado por Jader Muñoz")
app.geometry("900x750")
app.configure(fg_color="#121212")

frame_main = ctk.CTkFrame(app)
frame_main.pack(padx=20, pady=20, fill="both", expand=True)

# Logo y título
try:
    logo_img = Image.open(logo_path)
    logo = ctk.CTkImage(logo_img, size=(220, 180))  # tamaño ajustado para buena visualización
except Exception:
    logo = None

frame_logo = ctk.CTkFrame(frame_main, fg_color="transparent")
frame_logo.pack(pady=(10, 0), fill="x")

if logo:
    logo_label = ctk.CTkLabel(frame_logo, image=logo, text="")
    logo_label.pack(side="right", padx=20)

titulo_label = ctk.CTkLabel(frame_logo, text="Netzen - Reportes Automáticos Cisco", font=ctk.CTkFont(size=24, weight="bold"))
titulo_label.pack(side="left", padx=20)

# Textbox para ingresar IPs
entry_ips = ctk.CTkTextbox(frame_main, height=100)
entry_ips.pack(pady=10, fill="x", padx=40)
entry_ips.insert("1.0", "192.168.1.1\n192.168.1.2")

# Botón para cargar IPs desde archivo
btn_cargar_ips = ctk.CTkButton(frame_main, text="📂 Cargar IPs desde archivo .txt", command=cargar_ips_txt)
btn_cargar_ips.pack(pady=5)

# Checkbox para comandos
frame_comandos = ctk.CTkFrame(frame_main)
frame_comandos.pack(pady=5)
for cmd, nombre in comandos.items():
    checkbox_comandos[cmd] = ctk.CTkCheckBox(frame_comandos, text=nombre)
    checkbox_comandos[cmd].pack(side="left", padx=10)

# Botones de acciones
btn_frame = ctk.CTkFrame(frame_main)
btn_frame.pack(pady=10)

btn_credenciales = ctk.CTkButton(btn_frame, text="🔐 Ingresar Credenciales", command=pedir_credenciales_popup)
btn_credenciales.pack(side="left", padx=5)

btn_carpeta = ctk.CTkButton(btn_frame, text="📁 Abrir Carpeta de Reportes", command=abrir_carpeta)
btn_carpeta.pack(side="left", padx=5)

btn_probar = ctk.CTkButton(btn_frame, text="🔎 Probar Conexión", command=probar_conexion)
btn_probar.pack(side="left", padx=5)

btn_generar = ctk.CTkButton(btn_frame, text="📝 Generar Reportes", command=generar_reportes)
btn_generar.pack(side="left", padx=5)

btn_ayuda = ctk.CTkButton(btn_frame, text="❓ Ayuda", command=mostrar_ayuda)
btn_ayuda.pack(side="left", padx=5)

# Log de salida
log_output = ctk.CTkTextbox(frame_main, height=250, state="disabled")
log_output.pack(padx=40, pady=(10, 40), fill="both", expand=True)

# Label con créditos al pie
creditos = ctk.CTkLabel(app, text="Desarrollado por Jader Muñoz 2025", font=ctk.CTkFont(size=12, slant="italic"))
creditos.pack(pady=(0, 5))

# Inicializar estado botones según credenciales cargadas
usuario = cargar_usuario_cache()
contrasena = ""  # No guardamos contraseña en cache por seguridad
actualizar_botones_estado()

app.mainloop()
