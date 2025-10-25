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
        
    # -------------------------
    # LIBROS (bibliotecario)
    # -------------------------

    @app.post("/api/libros")
    def create_libro():
        data = request.get_json(silent=True) or {}
        required = ["titulo", "autor"]
        if not all(k in data for k in required):
            return jsonify({"ok": False, "error": "Faltan campos requeridos: titulo, autor"}), 400

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO public.libros (titulo, autor, categoria, editorial, edicion, anio, ubicacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_libro, titulo, autor, categoria, editorial, edicion, anio, ubicacion
                    """,
                    (
                        data.get("titulo"),
                        data.get("autor"),
                        data.get("categoria"),
                        data.get("editorial"),
                        data.get("edicion"),
                        data.get("anio"),
                        data.get("ubicacion"),
                    )
                )
                row = cur.fetchone()
                conn.commit()
                return jsonify({"ok": True, "libro": row})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.put("/api/libros/<int:id_libro>")
    def update_libro(id_libro: int):
        data = request.get_json(silent=True) or {}
        fields = ["titulo", "autor", "categoria", "editorial", "edicion", "anio", "ubicacion"]
        sets, params = [], []
        for f in fields:
            if f in data:
                sets.append(f"{f} = %s")
                params.append(data[f])

        if not sets:
            return jsonify({"ok": False, "error": "No hay campos a actualizar"}), 400

        params.append(id_libro)
        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    UPDATE public.libros
                    SET {", ".join(sets)}
                    WHERE id_libro = %s
                    RETURNING id_libro, titulo, autor, categoria, editorial, edicion, anio, ubicacion
                    """,
                    tuple(params)
                )
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return jsonify({"ok": False, "error": "Libro no encontrado"}), 404
                return jsonify({"ok": True, "libro": row})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.delete("/api/libros/<int:id_libro>")
    def delete_libro(id_libro: int):
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("DELETE FROM public.libros WHERE id_libro = %s RETURNING id_libro", (id_libro,))
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return jsonify({"ok": False, "error": "Libro no encontrado"}), 404
                return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # -------------------------
    # EJEMPLARES (bibliotecario)
    # -------------------------

    @app.post("/api/ejemplares")
    def create_ejemplar():
        data = request.get_json(silent=True) or {}
        required = ["id_libro"]
        if not all(k in data for k in required):
            return jsonify({"ok": False, "error": "Falta id_libro"}), 400

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO public.ejemplares (id_libro, estado, ubicacion)
                    VALUES (%s, %s, %s)
                    RETURNING id_ejemplar, id_libro, estado, ubicacion, created_at
                    """,
                    (
                        data.get("id_libro"),
                        data.get("estado", "disponible"),  # valores típicos: disponible, prestado, en_reparacion
                        data.get("ubicacion"),
                    )
                )
                row = cur.fetchone()
                conn.commit()
                return jsonify({"ok": True, "ejemplar": row})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.put("/api/ejemplares/<int:id_ejemplar>")
    def update_ejemplar(id_ejemplar: int):
        data = request.get_json(silent=True) or {}
        fields = ["estado", "ubicacion", "id_libro"]
        sets, params = [], []
        for f in fields:
            if f in data:
                sets.append(f"{f} = %s")
                params.append(data[f])

        if not sets:
            return jsonify({"ok": False, "error": "No hay campos a actualizar"}), 400

        params.append(id_ejemplar)
        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    UPDATE public.ejemplares
                    SET {", ".join(sets)}
                    WHERE id_ejemplar = %s
                    RETURNING id_ejemplar, id_libro, estado, ubicacion, created_at
                    """,
                    tuple(params)
                )
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return jsonify({"ok": False, "error": "Ejemplar no encontrado"}), 404
                return jsonify({"ok": True, "ejemplar": row})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.delete("/api/ejemplares/<int:id_ejemplar>")
    def delete_ejemplar(id_ejemplar: int):
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("DELETE FROM public.ejemplares WHERE id_ejemplar = %s RETURNING id_ejemplar", (id_ejemplar,))
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return jsonify({"ok": False, "error": "Ejemplar no encontrado"}), 404
                return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # -------------------------
    # SOLICITUDES (tótem / bibliotecario)
    # -------------------------
    # Estados sugeridos: pending -> ready -> served | canceled

    def _valid_estado(estado: str) -> bool:
        return estado in {"pending", "ready", "served", "canceled"}

    @app.post("/api/solicitudes")
    def crear_solicitud():
        """
        Body esperado:
        {
          "user_id": 123,
          "items": [
            {"id_libro": 10, "cantidad": 1},
            {"id_ejemplar": 55}  # opcionalmente por ejemplar específico
          ],
          "observaciones": "opcional"
        }
        """
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        items = data.get("items") or []
        obs = data.get("observaciones")

        if not user_id or not items:
            return jsonify({"ok": False, "error": "Faltan user_id o items"}), 400

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                # Validar usuario existe
                cur.execute("SELECT user_id FROM public.users WHERE user_id = %s", (user_id,))
                if not cur.fetchone():
                    return jsonify({"ok": False, "error": "Usuario no existe"}), 404

                # Crear cabecera
                cur.execute(
                    """
                    INSERT INTO public.solicitudes (user_fk, estado, observaciones)
                    VALUES (%s, 'pending', %s)
                    RETURNING solicitud_id, created_at
                    """,
                    (user_id, obs)
                )
                sol = cur.fetchone()
                solicitud_id = sol["solicitud_id"]

                # Insertar detalle
                for it in items:
                    id_libro = it.get("id_libro")
                    id_ejemplar = it.get("id_ejemplar")
                    cantidad = int(it.get("cantidad", 1))

                    if not id_libro and not id_ejemplar:
                        return jsonify({"ok": False, "error": "Cada item debe incluir id_libro o id_ejemplar"}), 400

                    cur.execute(
                        """
                        INSERT INTO public.solicitudes_detalle (solicitud_fk, id_libro, id_ejemplar, cantidad)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (solicitud_id, id_libro, id_ejemplar, cantidad)
                    )

                conn.commit()

                return jsonify({"ok": True, "solicitud": {
                    "solicitud_id": solicitud_id,
                    "estado": "pending",
                    "created_at": sol["created_at"]
                }})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.get("/api/solicitudes")
    def listar_solicitudes():
        """
        Querystring:
          - estado: pending|ready|served|canceled (opcional, múltiples separados por coma)
          - assigned: user_id bibliotecario asignado (opcional)
          - desde, hasta: ISO date/time (opcional)
          - limit: default 200
        """
        estados = request.args.get("estado")
        assigned = request.args.get("assigned")
        desde = request.args.get("desde")
        hasta = request.args.get("hasta")
        try:
            limit = int(request.args.get("limit", "200"))
        except ValueError:
            limit = 200

        where, params = [], []
        if estados:
            ests = [e.strip() for e in estados.split(",") if e.strip()]
            where.append("s.estado = ANY(%s)")
            params.append(ests)

        if assigned:
            where.append("s.asignado_fk = %s")
            params.append(int(assigned))

        if desde:
            where.append("s.created_at >= %s")
            params.append(desde)
        if hasta:
            where.append("s.created_at <= %s")
            params.append(hasta)

        sql = """
            SELECT
                s.solicitud_id, s.estado, s.created_at, s.observaciones,
                s.asignado_fk,
                u.user_id, u.nombre, u.apellido1, u.apellido2, u.email,
                COALESCE(SUM(sd.cantidad), 0) AS total_items
            FROM public.solicitudes s
            JOIN public.users u ON u.user_id = s.user_fk
            LEFT JOIN public.solicitudes_detalle sd ON sd.solicitud_fk = s.solicitud_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += """
            GROUP BY s.solicitud_id, u.user_id
            ORDER BY s.created_at DESC, s.solicitud_id DESC
            LIMIT %s
        """
        params.append(limit)

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return jsonify({"ok": True, "count": len(rows), "items": rows})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.get("/api/solicitudes/<int:solicitud_id>")
    def detalle_solicitud(solicitud_id: int):
        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        s.solicitud_id, s.estado, s.created_at, s.observaciones,
                        s.asignado_fk,
                        u.user_id, u.nombre, u.apellido1, u.apellido2, u.email
                    FROM public.solicitudes s
                    JOIN public.users u ON u.user_id = s.user_fk
                    WHERE s.solicitud_id = %s
                    """,
                    (solicitud_id,)
                )
                head = cur.fetchone()
                if not head:
                    return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

                cur.execute(
                    """
                    SELECT id, id_libro, id_ejemplar, cantidad
                    FROM public.solicitudes_detalle
                    WHERE solicitud_fk = %s
                    ORDER BY id ASC
                    """,
                    (solicitud_id,)
                )
                items = cur.fetchall()

                return jsonify({"ok": True, "solicitud": head, "items": items})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.patch("/api/solicitudes/<int:solicitud_id>")
    def actualizar_solicitud(solicitud_id: int):
        """
        Body posible:
        {
          "estado": "ready|served|canceled",
          "asignado_fk": 7,           # bibliotecario
          "observaciones": "texto..." # opcional
        }
        Reglas simples de transición:
          pending -> ready -> served
          pending -> canceled
          ready   -> canceled
        """
        data = request.get_json(silent=True) or {}
        new_estado = data.get("estado")
        asignado_fk = data.get("asignado_fk")
        obs = data.get("observaciones")

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT estado FROM public.solicitudes WHERE solicitud_id = %s", (solicitud_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

                old_estado = row["estado"]
                if new_estado:
                    if not _valid_estado(new_estado):
                        return jsonify({"ok": False, "error": "Estado inválido"}), 400
                    # chequeo de transición
                    valid_transitions = {
                        "pending": {"ready", "canceled"},
                        "ready": {"served", "canceled"},
                        "served": set(),
                        "canceled": set(),
                    }
                    if new_estado not in valid_transitions.get(old_estado, set()):
                        return jsonify({"ok": False, "error": f"Transición no permitida: {old_estado} -> {new_estado}"}), 400

                sets, params = [], []
                if new_estado:
                    sets.append("estado = %s")
                    params.append(new_estado)
                if asignado_fk is not None:
                    sets.append("asignado_fk = %s")
                    params.append(asignado_fk)
                if obs is not None:
                    sets.append("observaciones = %s")
                    params.append(obs)

                if not sets:
                    return jsonify({"ok": False, "error": "No hay cambios"}), 400

                params.append(solicitud_id)
                cur.execute(
                    f"UPDATE public.solicitudes SET {', '.join(sets)} WHERE solicitud_id = %s RETURNING solicitud_id, estado, asignado_fk, observaciones",
                    tuple(params)
                )
                updated = cur.fetchone()
                conn.commit()
                return jsonify({"ok": True, "solicitud": updated})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # ===========================================
    # PRESTAMOS (bibliotecario)
    # Reglas por defecto:
    #   - Sala:    ahora + SALA_MINUTES (env, default 120 min)
    #   - Domicilio: ahora + DOMICILIO_DAYS (env, default 7 días)
    #   - Solo presta si el ejemplar está 'disponible'
    #   - Marca ejemplar -> 'prestado'
    #   - Valida sanción vigente (si existe tabla sanciones)
    # ===========================================

    from datetime import timedelta

    def _has_active_sanction(conn, user_id: int) -> bool:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 1
                    FROM public.sanciones
                    WHERE user_fk = %s AND now() < hasta
                    LIMIT 1
                """, (user_id,))
                return cur.fetchone() is not None
        except Exception:
            # Si no existe la tabla, no bloquea (modo compatible)
            return False

    @app.post("/api/prestamos")
    def crear_prestamo():
        """
        Body:
        {
          "user_id": 3,
          "id_ejemplar": 10,
          "tipo": "Sala" | "Domicilio"
        }
        Devuelve: datos del préstamo y fechas calculadas.
        """
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        id_ejemplar = data.get("id_ejemplar")
        tipo = (data.get("tipo") or "Sala").strip().title()  # 'Sala' / 'Domicilio'

        if not user_id or not id_ejemplar:
            return jsonify({"ok": False, "error": "Faltan user_id o id_ejemplar"}), 400
        if tipo not in ("Sala", "Domicilio"):
            return jsonify({"ok": False, "error": "Tipo inválido: use 'Sala' o 'Domicilio'"}), 400

        sala_minutes = int(os.getenv("SALA_MINUTES", "120"))
        domicilio_days = int(os.getenv("DOMICILIO_DAYS", "7"))

        now = datetime.now()
        if tipo == "Sala":
            fecha_venc = now + timedelta(minutes=sala_minutes)
        else:
            fecha_venc = now + timedelta(days=domicilio_days)

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                # Valida usuario
                cur.execute("SELECT user_id FROM public.users WHERE user_id = %s", (user_id,))
                if not cur.fetchone():
                    return jsonify({"ok": False, "error": "Usuario no existe"}), 404

                # Sanción vigente (si existe tabla)
                if _has_active_sanction(conn, user_id):
                    return jsonify({"ok": False, "error": "Usuario con sanción vigente. No puede pedir préstamos."}), 403

                # Valida ejemplar disponible y obtiene libro
                cur.execute("""
                    SELECT e.id_ejemplar, e.id_libro, e.estado, l.titulo, l.autor
                    FROM public.ejemplares e
                    JOIN public.libros l ON l.id_libro = e.id_libro
                    WHERE e.id_ejemplar = %s
                """, (id_ejemplar,))
                ej = cur.fetchone()
                if not ej:
                    return jsonify({"ok": False, "error": "Ejemplar no existe"}), 404
                if ej["estado"] != "disponible":
                    return jsonify({"ok": False, "error": f"Ejemplar no disponible (estado: {ej['estado']})"}), 409

                # Crea préstamo
                cur.execute("""
                    INSERT INTO public.prestamos
                        (user_fk, ejemplar_fk, libro_fk, tipo_prestamo, fecha_reserva, fecha_vencimiento, vencido)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                    RETURNING prestamo_id
                """, (user_id, ej["id_ejemplar"], ej["id_libro"], tipo, now, fecha_venc))
                p = cur.fetchone()

                # Marca ejemplar como prestado
                cur.execute("UPDATE public.ejemplares SET estado = 'prestado' WHERE id_ejemplar = %s", (id_ejemplar,))

                conn.commit()

                return jsonify({
                    "ok": True,
                    "prestamo": {
                        "prestamo_id": p["prestamo_id"],
                        "user_id": user_id,
                        "id_ejemplar": ej["id_ejemplar"],
                        "id_libro": ej["id_libro"],
                        "titulo": ej["titulo"],
                        "autor": ej["autor"],
                        "tipo": tipo,
                        "fecha_reserva": now.isoformat(),
                        "fecha_vencimiento": fecha_venc.isoformat()
                    }
                })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.get("/api/prestamos/<int:prestamo_id>/comprobante")
    def comprobante_prestamo(prestamo_id: int):
        """
        Devuelve un comprobante simple (texto/JSON).
        (Luego podemos servir HTML o PDF si quieres.)
        """
        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT p.prestamo_id, p.tipo_prestamo, p.fecha_reserva, p.fecha_vencimiento,
                           u.user_id, u.nombre, u.apellido1, u.apellido2, u.email,
                           l.id_libro, l.titulo, l.autor
                    FROM public.prestamos p
                    JOIN public.users u ON u.user_id = p.user_fk
                    JOIN public.libros l ON l.id_libro = p.libro_fk
                    WHERE p.prestamo_id = %s
                """, (prestamo_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404

                full_name = " ".join(filter(None, [row["nombre"], row["apellido1"], row["apellido2"]]))
                return jsonify({
                    "ok": True,
                    "comprobante": {
                        "prestamo_id": row["prestamo_id"],
                        "usuario": {"id": row["user_id"], "nombre": full_name, "email": row["email"]},
                        "libro": {"id_libro": row["id_libro"], "titulo": row["titulo"], "autor": row["autor"]},
                        "tipo": row["tipo_prestamo"],
                        "fecha_prestamo": row["fecha_reserva"].isoformat() if row["fecha_reserva"] else None,
                        "fecha_vencimiento": row["fecha_vencimiento"].isoformat() if row["fecha_vencimiento"] else None
                    }
                })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # ===========================================
    # DEVOLUCIONES (bibliotecario)
    # Reglas:
    #  - Se puede devolver por prestamo_id o por id_ejemplar (toma el préstamo activo)
    #  - Marca fecha_devolucion = ahora
    #  - El ejemplar queda en estado 'en_reposicion' y se libera a 'disponible' en 30 min
    #  - Si hay atraso (ahora > fecha_vencimiento) se crea sanción configurable
    # ===========================================

    from datetime import timedelta
    from math import ceil

    def _schedule_make_available(ejemplar_id: int, minutes: int = 30):
        """Agenda cambio de estado a 'disponible' para el ejemplar en N minutos."""
        try:
            run_at = datetime.now() + timedelta(minutes=minutes)
            # usa (o crea si falta) un scheduler singleton para devoluciones
            global _return_scheduler
            try:
                _return_scheduler  # noqa
            except NameError:
                from apscheduler.schedulers.background import BackgroundScheduler
                _return_scheduler = BackgroundScheduler(daemon=True)
                _return_scheduler.start()
            _return_scheduler.add_job(
                func=_make_available_job,
                trigger='date',
                run_date=run_at,
                args=[ejemplar_id],
                id=f"mkavail-{ejemplar_id}-{run_at.timestamp()}",
                misfire_grace_time=300
            )
        except Exception as e:
            print(f"[WARN] No se pudo agendar liberación de ejemplar {ejemplar_id}: {e}")

    def _make_available_job(ejemplar_id: int):
        """Job: set estado = 'disponible' para el ejemplar."""
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("UPDATE public.ejemplares SET estado = 'disponible' WHERE id_ejemplar = %s", (ejemplar_id,))
                conn.commit()
        except Exception as e:
            print(f"[ERROR] Liberando ejemplar {ejemplar_id}: {e}")

    def _insert_sancion(conn, user_id: int, fecha_vencimiento, fecha_devolucion):
        """Crea una sanción simple: 1 día por cada día (ceil) de atraso (mínimo 1 día)."""
        try:
            atraso = (fecha_devolucion - fecha_vencimiento).total_seconds()
            if atraso <= 0:
                return  # sin atraso => sin sanción
            days_late = ceil(atraso / 86400.0)
            min_days = int(os.getenv("SANCTION_MIN_DAYS", "1"))
            days = max(days_late, min_days)
            hasta = datetime.now() + timedelta(days=days)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO public.sanciones (user_fk, motivo, desde, hasta)
                    VALUES (%s, %s, NOW(), %s)
                """, (user_id, f"Atraso de {days_late} día(s)", hasta))
        except Exception as e:
            # si no existe la tabla sanciones, no bloqueamos el flujo
            print(f"[WARN] No se pudo registrar sanción: {e}")

    @app.post("/api/devoluciones")
    def registrar_devolucion():
        """
        Body (al menos uno):
          { "prestamo_id": 10 }  ó  { "id_ejemplar": 55 }
        Efectos:
          - Set p.fecha_devolucion = NOW()
          - e.estado = 'en_reposicion' y agenda a 'disponible' en 30 min
          - Si devolvió con atraso => crea sanción
        """
        data = request.get_json(silent=True) or {}
        prestamo_id = data.get("prestamo_id")
        id_ejemplar = data.get("id_ejemplar")

        if not prestamo_id and not id_ejemplar:
            return jsonify({"ok": False, "error": "Debe enviar prestamo_id o id_ejemplar"}), 400

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                # Encontrar préstamo activo
                if prestamo_id:
                    cur.execute("""
                        SELECT p.prestamo_id, p.user_fk, p.ejemplar_fk, p.fecha_vencimiento, p.fecha_devolucion
                        FROM public.prestamos p
                        WHERE p.prestamo_id = %s
                    """, (prestamo_id,))
                else:
                    cur.execute("""
                        SELECT p.prestamo_id, p.user_fk, p.ejemplar_fk, p.fecha_vencimiento, p.fecha_devolucion
                        FROM public.prestamos p
                        WHERE p.ejemplar_fk = %s
                        ORDER BY p.prestamo_id DESC
                        LIMIT 1
                    """, (id_ejemplar,))
                p = cur.fetchone()
                if not p:
                    return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404
                if p["fecha_devolucion"]:
                    return jsonify({"ok": False, "error": "El préstamo ya está devuelto"}), 409

                now = datetime.now()

                # Marcar devolución
                cur.execute("""
                    UPDATE public.prestamos
                    SET fecha_devolucion = %s
                    WHERE prestamo_id = %s
                    RETURNING prestamo_id
                """, (now, p["prestamo_id"]))

                # Pasar ejemplar a 'en_reposicion'
                cur.execute("UPDATE public.ejemplares SET estado = 'en_reposicion' WHERE id_ejemplar = %s", (p["ejemplar_fk"],))

                # (Opcional) marcar vencido si pasó la fecha
                try:
                    if p["fecha_vencimiento"] and now > p["fecha_vencimiento"]:
                        cur.execute("UPDATE public.prestamos SET vencido = TRUE WHERE prestamo_id = %s", (p["prestamo_id"],))
                except Exception:
                    pass

                # Sanción si hay atraso
                if p["fecha_vencimiento"]:
                    _insert_sancion(conn, p["user_fk"], p["fecha_vencimiento"], now)

                conn.commit()

                # Agenda liberación en 30 minutos (configurable por env DEVOLUCION_LIBERAR_MIN=30)
                liberar_min = int(os.getenv("DEVOLUCION_LIBERAR_MIN", "30"))
                _schedule_make_available(p["ejemplar_fk"], liberar_min)

                return jsonify({
                    "ok": True,
                    "devolucion": {
                        "prestamo_id": p["prestamo_id"],
                        "ejemplar_id": p["ejemplar_fk"],
                        "fecha_devolucion": now.isoformat(),
                        "libera_en_min": liberar_min
                    }
                })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # ===========================================
    # SANCIONES (consulta)
    # Usos típicos del bibliotecario:
    #  - Ver sanciones de un usuario antes de prestar
    #  - Chequear si tiene bloqueo vigente y hasta cuándo
    # ===========================================

    @app.get("/api/sanciones")
    def listar_sanciones():
        """
        Querystring:
          - user_id: filtra por usuario (opcional)
          - activas: true/false (default true) -> solo sanciones con now() < hasta
          - limit: default 200
        """
        user_id = request.args.get("user_id", type=int)
        activas = (request.args.get("activas", "true").lower() in ("true", "1", "t", "yes"))
        try:
            limit = int(request.args.get("limit", "200"))
        except ValueError:
            limit = 200

        where, params = [], []
        if user_id is not None:
            where.append("s.user_fk = %s")
            params.append(user_id)
        if activas:
            where.append("NOW() < s.hasta")

        sql = """
            SELECT s.sancion_id, s.user_fk, s.motivo, s.desde, s.hasta, u.nombre, u.apellido1, u.apellido2, u.email
            FROM public.sanciones s
            JOIN public.users u ON u.user_id = s.user_fk
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY s.hasta DESC, s.sancion_id DESC LIMIT %s"
        params.append(limit)

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return jsonify({"ok": True, "count": len(rows), "items": rows})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


    @app.get("/api/sanciones/estado")
    def estado_sancion():
        """
        Devuelve si el usuario está bloqueado ahora mismo.
        Ej: /api/sanciones/estado?user_id=3
        Respuesta: { ok, user_id, bloqueado, hasta }
        """
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"ok": False, "error": "Debe enviar user_id"}), 400

        try:
            with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT hasta
                    FROM public.sanciones
                    WHERE user_fk = %s AND NOW() < hasta
                    ORDER BY hasta DESC
                    LIMIT 1
                """, (user_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"ok": True, "user_id": user_id, "bloqueado": False, "hasta": None})
                return jsonify({"ok": True, "user_id": user_id, "bloqueado": True, "hasta": row["hasta"].isoformat()})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500


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
