Backend (Flask) - Sisbib

This is a minimal Flask API used by the frontend to validate user login against a PostgreSQL database.

Endpoints
- GET /api/health – health check and DB connectivity test
- POST /api/login – body: { email, password?, role? }. Checks users table for a matching row.
  - Returns { ok: true, role, user } on success, or { ok: false, error } on failure.

The login endpoint introspects the users table to find column names:
- Email/username: tries email, correo, username, user, usuario
- Password (optional): tries password, passwd, clave, hash
- Role (optional): tries role, rol, tipo, tipo_usuario

If no password column exists, the check is done only by email. If no role column exists, it uses the requested role if provided, otherwise defaults to cliente.

Configuration
Set the following environment variables (create a .env file next to app.py if convenient) or use .env.example:

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=sisbib
DB_USER=postgres
DB_PASSWORD=your_password
PORT=5000

Run locally
1. Create a virtual environment (optional but recommended)
2. Install dependencies: pip install -r requirements.txt
3. Start the server: python app.py

The frontend dev server is configured to proxy /api to http://127.0.0.1:5000.
