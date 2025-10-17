# Sisbib
Proyecto de sistema bibliotecario | LPWWW | Alergicos a la pala

# Integrantes:
* Tomás González 202273609-7
* Cristóbal Lazcano 202173567-4
* José Manuel Castro 202073550-6
* Ian Rossi A. 202004612-3
* Integrante 5

### Entrega 1: Frontend
* Figma: https://www.figma.com/design/N6ruH9qnwYHWIbdGE6bBdp/Biblioteca-LPWWW?node-id=18-3&t=16dMF6fR6jiwyoJJ-1
* Video Figma: https://youtu.be/hTVCZ4cKQTU?feature=shared

### Entrega 2: Prototipo
* Prototipo con frontend y backend

## Frontend (React + Vite)

- Landing de Biblioteca con navbar y selector de roles (solo Admin activo).
- Login de Admin (mock, sin backend) y redirección a Dashboard.
- Dashboard con 4 opciones: Usuarios, Registro de ficha, Préstamos domicilio, Préstamos sala (todas con páginas placeholder).

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

3. Build de producción (opcional)

	```powershell
	npm run build
	npm run preview
	```

### Estructura principal

```
frontend/
  index.html
  src/
	 App.tsx
	 main.tsx
	 styles.css
	 components/Navbar.tsx
	 pages/
		Landing.tsx
		AdminLogin.tsx
		AdminDashboard.tsx
		Usuarios.tsx
		RegistroFicha.tsx
		PrestamosDomicilio.tsx
		PrestamosSala.tsx
```
