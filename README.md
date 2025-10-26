# Sisbib
Proyecto de sistema bibliotecario | LPWWW | Alergicos a la pala

# Integrantes:
* Tomás González 202273609-7
* Cristóbal Lazcano 202173567-4
* José Manuel Castro 202073550-6
* Ian Rossi A. 202004612-3
* Muryel Constanzo 202173525-9

### Entrega 1: Frontend
* Figma: https://www.figma.com/design/N6ruH9qnwYHWIbdGE6bBdp/Biblioteca-LPWWW?node-id=18-3&t=16dMF6fR6jiwyoJJ-1
* Video Figma: https://youtu.be/hTVCZ4cKQTU?feature=shared

### Entrega 2: Prototipo
Prototipo con frontend y backend básico ya integrado:
- Frontend (React + Vite + TS + React Router) con rutas protegidas por rol.
- Login integrado al backend Flask vía /api/login.
- Páginas de administración con placeholders para Usuarios, Registro de Ficha y Préstamos.
- Vistas placeholder para Bibliotecario y Cliente.

Para más detalles del backend ver `backend/README.txt`.

## Frontend (React + Vite)

- Landing de Biblioteca con navbar.
- Login del sitio integrado al backend (POST /api/login) y redirección por rol.
- Rutas protegidas según rol: admin, bibliotecario, cliente.
- Admin Dashboard con herramientas: Usuarios, Registro de Ficha, Préstamos (placeholders por ahora).
- Vistas placeholder: Bibliotecario/Home, Cliente/Home.

### Correr localmente

Requisitos: Node.js 18+ y npm.

1. Instalar dependencias
   
	PowerShell (desde la carpeta `frontend/`):
   
	```powershell
	cd .\frontend
	npm install
	```

2. Modo desarrollo

	```powershell
	npm run dev
	```

	Abre http://localhost:5173

El servidor de desarrollo del frontend está configurado para hacer proxy de /api hacia http://127.0.0.1:5000 (ver `frontend/vite.config.ts`).


### Estructura principal

```
frontend/
	index.html
	src/
		App.tsx
		main.tsx
		auth.tsx
		Protected.tsx
		styles.css
		components/
			Navbar.tsx
		pages/
			Landing.tsx
			SiteLogin.tsx
			admin/
				AdminDashboard.tsx
				adminTools/
					Usuarios.tsx
					RegistroFicha.tsx
					Prestamos.tsx
			bibliotecario/
				Home.tsx
			cliente/
				Home.tsx
```

## Backend (Flask)

- API Flask con PostgreSQL y CORS habilitado.
- Envío de correo con Flask-Mailman y tarea programada con APScheduler.
- Archivo `.env` para configuración local (no incluir secretos en commits públicos).

### Endpoints principales

- POST `/api/login`: autentica usuario por email y password; retorna `{ ok, role, user }`.
- GET `/api/health`: healthcheck y prueba de conectividad a DB.
- GET `/api/users`: lista usuarios con filtro de búsqueda `q` y `limit`.
- POST `/api/users`: crea un usuario (campos requeridos: nombre, apellido1, apellido2, rut_numero, rut_dv, email, password, role).
- GET `/api/prestamos`: lista préstamos con joins a usuario y libro; filtros `tipo`, `q`, `limit`.
- POST `/api/test-email`: envía correo de prueba (requiere configuración de MAIL_*).
- POST `/api/notify-overdue`: dispara manualmente notificaciones de préstamos vencidos.

Notas:
- El job de notificaciones se ejecuta automáticamente cada lunes a las 20:00 (hora del servidor) mediante APScheduler.
- Variables relevantes en `.env`: `DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, PORT` y `MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS, MAIL_USE_SSL, MAIL_DEFAULT_SENDER, MAIL_TEST_TO`.

### Correr backend localmente

Requisitos: Python 3.11+ (recomendado) y PostgreSQL accesible.

```powershell
cd .\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Configura .env con credenciales de DB y correo
python app.py
```

El backend se levanta por defecto en http://127.0.0.1:5000.
