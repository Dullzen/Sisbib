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
                    cur.execute(
                        "SELECT id, email, role FROM public.users WHERE email = %s AND password = %s",
                        (email, password)
                    )
                    user_row = cur.fetchone()

                    if not user_row:
                        return jsonify({"ok": False, "error": "Credenciales inválidas o usuario no existe"}), 401

                    # Normaliza el valor del rol a minúsculas para el frontend
                    db_role = user_row.get("role")
                    role = db_role.strip().lower() if db_role else (requested_role or "cliente")

                    result_user = {"id": user_row.get("id"), "email": user_row.get("email")}

                    return jsonify({"ok": True, "role": role, "user": result_user})

        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=True)
