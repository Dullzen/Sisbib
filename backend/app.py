import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


@dataclass
class DBConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


def get_db_config() -> DBConfig:
    return DBConfig(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "sisbib"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def get_connection():
    cfg = get_db_config()
    return psycopg.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    )


def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)  # Allow all origins for dev; tighten in prod

    @app.get("/api/health")
    def health():
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return jsonify({"ok": True, "status": "healthy"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.post("/api/login")
    def login():
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        email: Optional[str] = data.get("email")
        password: Optional[str] = data.get("password")
        requested_role: Optional[str] = data.get("role")

        if not email:
            return jsonify({"ok": False, "error": "Email es requerido"}), 400

        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Consulta directa usando los nombres fijos de columna
                    # Incluimos nombre y apellidos para mostrarlos en el navbar del frontend
                    cur.execute(
                        "SELECT user_id, email, role, nombre, apellido1, apellido2 FROM public.users WHERE email = %s AND password = %s",
                        (email, password)
                    )
                    user_row = cur.fetchone()

                    if not user_row:
                        return jsonify({"ok": False, "error": "Credenciales inválidas o usuario no existe"}), 401

                    # Normaliza el valor del rol a minúsculas para el frontend
                    db_role = user_row.get("role")
                    role = db_role.strip().lower() if db_role else (requested_role or "cliente")

                    result_user = {
                        "user_id": user_row.get("user_id"),
                        "email": user_row.get("email"),
                        "nombre": user_row.get("nombre"),
                        "apellido1": user_row.get("apellido1"),
                        "apellido2": user_row.get("apellido2"),
                    }

                    return jsonify({"ok": True, "role": role, "user": result_user})

        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get("/api/users")
    def list_users():
        """Return users with optional basic search filter.

        Query params:
        - q: search text applied to nombre, apellidos, email, rut
        - limit: max rows (default 200)
        """
        q: Optional[str] = request.args.get("q")
        try:
            limit = int(request.args.get("limit", "200"))
        except ValueError:
            limit = 200

        where = []
        params: list[Any] = []
        if q:
            like = f"%{q.strip()}%"
            where.append("(nombre ILIKE %s OR apellido1 ILIKE %s OR apellido2 ILIKE %s OR email ILIKE %s OR CAST(rut_numero AS TEXT) ILIKE %s)")
            params.extend([like, like, like, like, like])

        sql = "SELECT user_id, nombre, apellido1, apellido2, rut_numero, rut_dv, email, role, created_at FROM public.users"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC NULLS LAST, user_id DESC LIMIT %s"
        params.append(limit)

        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    return jsonify({"ok": True, "count": len(rows), "items": rows})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get("/api/prestamos")
    def list_prestamos():
        """Return prestamos joined with user and book data.

        Query params:
        - tipo: 'Sala' | 'Domicilio' (optional; when omitted returns all)
        - q: search text applied to titulo, autor, user name/email, and IDs
        - limit: max rows (default 200)
        """
        tipo: Optional[str] = request.args.get("tipo")
        q: Optional[str] = request.args.get("q")
        try:
            limit = int(request.args.get("limit", "200"))
        except ValueError:
            limit = 200

        where = []
        params: list[Any] = []
        if tipo:
            where.append("p.tipo_prestamo = %s")
            params.append(tipo)
        if q:
            like = f"%{q.strip()}%"
            where.append("(l.titulo ILIKE %s OR l.autor ILIKE %s OR u.email ILIKE %s OR u.nombre ILIKE %s OR u.apellido1 ILIKE %s OR u.apellido2 ILIKE %s OR CAST(p.prestamo_id AS TEXT) ILIKE %s)")
            params.extend([like, like, like, like, like, like, like])

        sql = (
            "SELECT p.prestamo_id, p.fecha_reserva, p.fecha_vencimiento, p.tipo_prestamo, "
            "u.user_id, u.nombre, u.apellido1, u.apellido2, u.email, "
            "l.id_libro, l.titulo, l.autor, l.categoria "
            "FROM public.prestamos p "
            "JOIN public.users u ON u.user_id = p.user_fk "
            "JOIN public.libros l ON l.id_libro = p.libro_fk "
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY p.fecha_reserva DESC, p.prestamo_id DESC LIMIT %s"
        params.append(limit)

        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    return jsonify({"ok": True, "count": len(rows), "items": rows})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.post("/api/users")
    def create_user():
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        
        # Basic validation
        required_fields = ["nombre", "apellido1", "apellido2", "rut_numero", "rut_dv", "email", "password", "role"]
        if not all(field in data for field in required_fields):
            return jsonify({"ok": False, "error": "Faltan campos requeridos"}), 400

        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO public.users (nombre, apellido1, apellido2, rut_numero, rut_dv, email, password, role)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING user_id, email, created_at
                        """,
                        (
                            data["nombre"],
                            data["apellido1"],
                            data["apellido2"],
                            data["rut_numero"],
                            data["rut_dv"].upper(),
                            data["email"],
                            data["password"], # In a real app, hash this password!
                            data["role"],
                        )
                    )
                    new_user = cur.fetchone()
                    conn.commit()
                    
                    return jsonify({"ok": True, "user": new_user})

        except psycopg.errors.UniqueViolation:
            return jsonify({"ok": False, "error": "El email o RUT ya está registrado."}), 409
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=True)
