Backend (Flask) - Sisbib

Esta es una API mínima en Flask utilizada por el frontend para validar el inicio de sesión de usuarios contra una base de datos PostgreSQL.

Endpoints
- GET /api/health – Verifica el estado del sistema y la conectividad con la base de datos.
- POST /api/login – body: { email, password?, role? }. Busca una fila coincidente en la tabla de usuarios.
  - Devuelve { ok: true, role, user } en caso de éxito, o { ok: false, error } en caso de fallo.

El endpoint de login inspecciona la tabla de usuarios para encontrar los nombres de las columnas:
- Email/usuario: intenta con email, correo, username, user, usuario
- Contraseña (opcional): intenta con password, passwd, clave, hash
- Rol (opcional): intenta con role, rol, tipo, tipo_usuario

Si no existe una columna de contraseña, la verificación se realiza solo por email. Si no existe una columna de rol, se usa el rol solicitado si se proporciona, de lo contrario, se asigna por defecto "cliente".

Configuración
Define las siguientes variables de entorno (crea un archivo .env junto a app.py si lo prefieres) o usa .env.example:

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=sisbib
DB_USER=postgres
DB_PASSWORD=tu_contraseña
PORT=5000

Ejecución local
1. Crea un entorno virtual (opcional pero recomendado)
2. Instala las dependencias: pip install -r requirements.txt
3. Inicia el servidor: python app.py

El servidor de desarrollo del frontend está configurado para redirigir /api a http://127.0.0.1:5000.
