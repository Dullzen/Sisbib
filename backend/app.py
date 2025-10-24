import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask_mailman import Mail, EmailMessage
from apscheduler.schedulers.background import BackgroundScheduler


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


load_dotenv()

mail = Mail()

def send_overdue_notifications():
    """Send email notifications for overdue loans."""
    
    print("Ejecutando tarea de notificación de préstamos vencidos...")
    
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Seleccionar préstamos que están marcados como vencidos
                cur.execute(
                    """
                    SELECT p.prestamo_id, u.email, u.nombre, l.titulo
                    FROM public.prestamos p
                    JOIN public.users u ON p.user_fk = u.user_id
                    JOIN public.libros l ON p.libro_fk = l.id_libro
                    WHERE p.vencido = TRUE
                    """
                )
                overdue_loans = cur.fetchall()
                print(f"Se encontraron {len(overdue_loans)} préstamos vencidos para notificar.")

                if not overdue_loans:
                    return

                # Enviar correos
                for loan in overdue_loans:
                    subject = "Aviso de Préstamo Vencido"
                    body = f"""
Hola {loan['nombre']},

Te informamos que tu préstamo del libro "{loan['titulo']}" ha vencido.
Por favor, acércate a la biblioteca para regularizar tu situación.

Saludos,
Sistema de Biblioteca
"""
                    try:
                        msg = EmailMessage(subject, body, to=[loan['email']])
                        # Con Flask-Mailman, es más robusto usar msg.send()
                        msg.send()
                        print(f"Email enviado a {loan['email']} por préstamo {loan['prestamo_id']}.")
                    except Exception as e:
                        print(f"Error al enviar email a {loan['email']}: {e}")

                # Marcar los préstamos como notificados (actualizar 'vencido' a TRUE)
                overdue_ids = [loan['prestamo_id'] for loan in overdue_loans]
                cur.execute("UPDATE public.prestamos SET vencido = TRUE WHERE prestamo_id = ANY(%s)", (overdue_ids,))
                conn.commit()
                print(f"Se marcaron {len(overdue_ids)} préstamos como vencidos.")

    except Exception as e:
        print(f"Error en la tarea de notificación: {e}")


def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow all origins for dev; tighten in prod

    # Mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Initialize mail
    mail.init_app(app)

    @app.post("/api/notify-overdue")
    def notify_overdue_manual():
        try:
            with app.app_context():
                send_overdue_notifications()
            return jsonify({"ok": True, "message": "Proceso de notificación iniciado."})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.post("/api/test-email")
    def test_email():
        data = request.get_json(silent=True) or {}
        to = data.get("to") or os.getenv("MAIL_TEST_TO")
        if not to:
            return jsonify({"ok": False, "error": "Debe proporcionar 'to' en el body o MAIL_TEST_TO en .env"}), 400
        subject = data.get("subject", "Prueba de correo - Sisbib")
        body = data.get("body", "Este es un correo de prueba desde Sisbib usando Mailtrap.")
        try:
            msg = EmailMessage(subject, body, to=[to])
            msg.send()
            return jsonify({"ok": True, "message": f"Correo de prueba enviado a {to}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

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
            tipos_list = [t.strip() for t in tipo.split(',') if t.strip()]
            if tipos_list:
                where.append("p.tipo_prestamo = ANY(%s)")
                params.append(tipos_list)
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

    @app.get("/api/libros")
    def list_libros(): 
        q: Optional[str] = request.args.get("q")
        categoria: Optional[str] = request.args.get("categoria")
        try:
            limit = int(request.args.get("limit", "200"))
        except ValueError:
            limit = 200
        
        where = []
        params: list[Any] = []

        if q:
            like = f"%{q.strip()}%"
            where.append("(titulo ILIKE %s OR autor ILIKE %s)")
            params.extend([like, like])
            
        if categoria: 
            like_categoria = f"%{categoria.strip()}%"
            where.append("categoria ILIKE %s")
            params.append(like_categoria)

        sql = (
            "SELECT id_libro, titulo, autor, categoria, ejemplares_disponibles "
            "FROM public.libros"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
            
        sql += " ORDER BY titulo ASC LIMIT %s" 
        params.append(limit)
        
        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, tuple(params)) 
                    rows = cur.fetchall()
                    
                    return jsonify({"ok": True, "count": len(rows), "items": rows})
                    
        except psycopg.OperationalError as e:
            print(f"ERROR OPERACIONAL de DB: {e}")
            return jsonify({"ok": False, "error": "Fallo al conectar con la base de datos PostgreSQL. Verifica que el servicio esté activo."}), 500
        except Exception as e:
            print(f"Error al listar libros: {e}") 
            return jsonify({"ok": False, "error": f"Error interno en la API: {str(e)}"}), 500
        

    return app


if __name__ == "__main__":
    app = create_app()
    
    # Scheduler setup
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule the notification job to run every Monday at 20:00
    def scheduled_task():
        with app.app_context():
            send_overdue_notifications()

    scheduler.add_job(scheduled_task, 'cron', day_of_week='mon', hour=20)
    scheduler.start()
    
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False) # use_reloader=False to avoid running scheduler twice
