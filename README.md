# 🔧 NetZen – Automatización de Reportes Cisco


## 📌 Descripción

**NetZen** es una aplicación desarrollada en Python que automatiza la obtención de reportes y respaldos desde equipos de red Cisco, reemplazando procesos manuales por una solución rápida, segura y eficiente.

Está diseñada para administradores de red, ingenieros de soporte y personal técnico que necesitan recolectar información crítica de múltiples dispositivos de forma automatizada.

---

## ⚙️ Funcionalidades

- 🔌 Conexión automática por **SSH y Telnet**
- 📡 Detección automática del protocolo disponible
- 📄 Generación de reportes por dispositivo
- 📁 Organización automática de archivos por hostname
- 🔐 Manejo seguro de credenciales (no se almacenan)
- 📊 Logs en tiempo real del proceso
- 📂 Carga masiva de IPs desde archivo `.txt`

---

## 🛠️ Tecnologías utilizadas

- Python
- Paramiko (SSH)
- Plink (Telnet)
- Interfaces de escritorio (GUI)
- Redes Cisco

---

## 🔐 Seguridad

- Las credenciales **no se almacenan en texto plano**
- Solo se utilizan en memoria durante la ejecución
- Requiere conexión mediante **VPN activa**
- El usuario puede guardar solo el nombre de usuario (opcional)

---

## 📋 Requisitos

- Sistema operativo: **Windows**
- Conexión a red con acceso a dispositivos Cisco
- VPN activa
- Conectividad (ping) a los equipos

---

## 📁 Estructura de reportes

Los reportes se generan automáticamente en:


C:\reportes cisco


Cada dispositivo crea una carpeta con su hostname:


C:\reportes cisco\HOSTNAME\


Ejemplo de archivos generados:

- `HOSTNAME RUNNING CONFIG.txt`
- `HOSTNAME LOG.txt`
- `HOSTNAME ATENUACIONES.txt`
- `HOSTNAME COUNTER ERROR.txt`

---

## 🚀 Uso

### 1. Agregar IPs

- Manualmente en la interfaz  
- O cargar desde archivo `.txt` (1 IP por línea)

---

### 2. Ingresar credenciales

- Usuario y contraseña
- Sin esto, las funciones estarán deshabilitadas

---

### 3. Seleccionar comandos

- Running Config  
- Logs  
- Atenuaciones  
- Counter Error  

---

### 4. Probar conexión

Verifica conectividad vía SSH o Telnet

---

### 5. Generar reportes

Ejecuta el respaldo automático y muestra logs en tiempo real

---

### 6. Ver resultados

Acceso directo a la carpeta de reportes

---

## 🧭 Flujo del sistema


Ingresar IPs → Credenciales → Selección comandos → Test conexión → Generar reportes → Guardado automático


---

## ❓ FAQ

**¿Por qué no puedo probar conexión?**  
→ Debes ingresar credenciales primero  

**¿Qué pasa si no tengo VPN?**  
→ No podrás conectarte a los equipos  

**¿Dónde se guardan los reportes?**  
→ En `C:\reportes cisco`  

**¿Es seguro usar mis credenciales?**  
→ Sí, no se almacenan ni se exponen  

---

## 📸 Capturas

*(Agrega aquí screenshots de tu app para mejorar impacto visual)*

---

## 📌 Autor

**Jader Muñoz**  
🔗 https://github.com/jaderkamui  

---

## 💡 Nota

Este proyecto fue desarrollado para automatizar tareas reales en entornos de red, mejorando tiempos de ejecución y reduciendo errores humanos en procesos repetitivos.

---

## ⭐ Valor del proyecto

Este proyecto demuestra:

- Automatización de procesos reales
- Integración con equipos de red
- Uso de protocolos SSH/Telnet
- Desarrollo de herramientas internas
- Resolución de problemas en entornos productivos
