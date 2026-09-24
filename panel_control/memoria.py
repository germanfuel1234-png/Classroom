"""Capa de datos del panel de control: memoria compartida + cola de tareas.

Esquema pensado para que los futuros agentes (Corrección, Publicaciones,
Consultas) escriban acá su actividad y el dashboard la lea en vivo.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "panel.db"

ESTADOS_TAREA = ("pendiente", "en_curso", "pendiente_aprobacion", "completada", "rechazada", "error")


@contextmanager
def conexion():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with conexion() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agentes (
                id INTEGER PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL,
                area_id INTEGER NOT NULL REFERENCES areas(id),
                estado TEXT NOT NULL DEFAULT 'activo'
            );

            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY,
                agente_id INTEGER NOT NULL REFERENCES agentes(id),
                curso TEXT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS memoria (
                id INTEGER PRIMARY KEY,
                tipo TEXT NOT NULL,
                curso TEXT,
                agente TEXT,
                clave TEXT NOT NULL,
                valor TEXT NOT NULL,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS materias_snapshot (
                id INTEGER PRIMARY KEY,
                curso TEXT UNIQUE NOT NULL,
                trabajos_json TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS aprobaciones (
                id INTEGER PRIMARY KEY,
                tarea_id INTEGER NOT NULL REFERENCES tareas(id),
                tipo TEXT NOT NULL,
                datos_json TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                creado_en TEXT NOT NULL,
                resuelto_en TEXT
            );

            CREATE TABLE IF NOT EXISTS anios_lectivos (
                id INTEGER PRIMARY KEY,
                anio INTEGER UNIQUE NOT NULL,
                activo INTEGER NOT NULL DEFAULT 0,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS actividades (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                numero INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                creado_en TEXT NOT NULL,
                UNIQUE(anio_lectivo_id, materia, numero)
            );

            CREATE TABLE IF NOT EXISTS materiales (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                numero_actividad INTEGER NOT NULL,
                nombre_archivo TEXT NOT NULL,
                tipo_mime TEXT,
                contenido BLOB NOT NULL,
                tamano_bytes INTEGER NOT NULL,
                subido_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                dia TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                materia TEXT NOT NULL,
                curso_grupo TEXT,
                curso_classroom TEXT NOT NULL,
                verificar INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS actividades_classroom (
                id INTEGER PRIMARY KEY,
                work_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                materia TEXT NOT NULL,
                titulo TEXT NOT NULL,
                tipo TEXT,
                materials_json TEXT,
                enunciado TEXT,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS uso_proveedores (
                id INTEGER PRIMARY KEY,
                proveedor TEXT NOT NULL,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recursos_bulk (
                id INTEGER PRIMARY KEY,
                work_id TEXT UNIQUE NOT NULL REFERENCES actividades_classroom(work_id),
                materia TEXT NOT NULL,
                titulo TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                recursos_json TEXT,
                error TEXT,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fechas_patrias_generadas (
                fecha_iso TEXT PRIMARY KEY,
                clave TEXT NOT NULL,
                generado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_director (
                id INTEGER PRIMARY KEY,
                rol TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comunicados (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                alumno_nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                fecha TEXT NOT NULL,
                observacion TEXT NOT NULL,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                alumno_nombre TEXT NOT NULL,
                fecha TEXT NOT NULL,
                presente INTEGER NOT NULL DEFAULT 0,
                UNIQUE(anio_lectivo_id, materia, alumno_nombre, fecha)
            );

            CREATE TABLE IF NOT EXISTS periodos_evaluacion (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                periodo TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                UNIQUE(anio_lectivo_id, periodo)
            );

            CREATE TABLE IF NOT EXISTS planillas_notas (
                id INTEGER PRIMARY KEY,
                anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                materia TEXT NOT NULL,
                alumno_nombre TEXT NOT NULL,
                c1_proc TEXT, c1_nota TEXT, c1_asist TEXT,
                c2_proc TEXT, c2_nota TEXT, c2_asist TEXT,
                dic_nota TEXT, dic_asist TEXT,
                final_proc TEXT, final_nota TEXT, final_asist TEXT,
                actualizado_en TEXT NOT NULL,
                UNIQUE(anio_lectivo_id, materia, alumno_nombre)
            );
            """
        )
        columnas = {r["name"] for r in con.execute("PRAGMA table_info(memoria)").fetchall()}
        if "agente" not in columnas:
            con.execute("ALTER TABLE memoria ADD COLUMN agente TEXT")

        columnas_alumnos = {r["name"] for r in con.execute("PRAGMA table_info(alumnos)").fetchall()}
        if "diagnostico" not in columnas_alumnos:
            con.execute("ALTER TABLE alumnos ADD COLUMN diagnostico TEXT")

        # Sembrado del primer año lectivo (2026): solo la primera vez que corre esta
        # migración, cuando todavía no existe ningún año cargado.
        if not con.execute("SELECT 1 FROM anios_lectivos LIMIT 1").fetchone():
            con.execute(
                "INSERT INTO anios_lectivos (anio, activo, creado_en) VALUES (2026, 1, ?)",
                (datetime.now().isoformat(timespec="seconds"),),
            )

        fila_activo = con.execute("SELECT id FROM anios_lectivos WHERE activo = 1 LIMIT 1").fetchone()
        anio_activo_id_actual = fila_activo["id"] if fila_activo else None

        # Migración: materias_snapshot pasa de UNIQUE(curso) a UNIQUE(curso, anio_lectivo_id)
        # (SQLite no permite DROP/ALTER de constraints, así que se rehace la tabla).
        # Se hace una sola vez: si la columna ya existe, no vuelve a correr.
        columnas_ms = {r["name"] for r in con.execute("PRAGMA table_info(materias_snapshot)").fetchall()}
        if "anio_lectivo_id" not in columnas_ms and anio_activo_id_actual is not None:
            con.executescript(
                """
                CREATE TABLE materias_snapshot_new (
                    id INTEGER PRIMARY KEY,
                    curso TEXT NOT NULL,
                    anio_lectivo_id INTEGER NOT NULL REFERENCES anios_lectivos(id),
                    trabajos_json TEXT NOT NULL,
                    actualizado_en TEXT NOT NULL,
                    UNIQUE(curso, anio_lectivo_id)
                );
                """
            )
            con.execute(
                """INSERT INTO materias_snapshot_new (id, curso, anio_lectivo_id, trabajos_json, actualizado_en)
                   SELECT id, curso, ?, trabajos_json, actualizado_en FROM materias_snapshot""",
                (anio_activo_id_actual,),
            )
            con.executescript(
                """
                DROP TABLE materias_snapshot;
                ALTER TABLE materias_snapshot_new RENAME TO materias_snapshot;
                """
            )

        # Migración: importar Horario_Clases.xlsx una sola vez (si `horarios` está
        # vacía). Después de esta primera vez, el horario se edita desde el panel y
        # el Excel deja de leerse — queda en el repo sin uso.
        hay_horarios = con.execute("SELECT COUNT(*) c FROM horarios").fetchone()["c"]
        ruta_xlsx = Path(__file__).parent.parent / "Horario_Clases.xlsx"
        if hay_horarios == 0 and anio_activo_id_actual is not None and ruta_xlsx.exists():
            from panel_control import horario as _horario_legacy
            for b in _horario_legacy._parsear_xlsx_legacy(ruta_xlsx):
                con.execute(
                    """INSERT INTO horarios
                       (anio_lectivo_id, dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (anio_activo_id_actual, b["dia"], b["hora_inicio"], b["hora_fin"], b["materia"],
                     b["curso_grupo"], b["curso_classroom"], 1 if b["verificar"] else 0),
                )


def agregar_area(nombre: str) -> int:
    with conexion() as con:
        con.execute("INSERT OR IGNORE INTO areas (nombre) VALUES (?)", (nombre,))
        return con.execute("SELECT id FROM areas WHERE nombre = ?", (nombre,)).fetchone()["id"]


def agregar_agente(nombre: str, rol: str, area_nombre: str, estado: str = "activo") -> int:
    area_id = agregar_area(area_nombre)
    with conexion() as con:
        con.execute(
            """INSERT INTO agentes (nombre, rol, area_id, estado) VALUES (?, ?, ?, ?)
               ON CONFLICT(nombre) DO UPDATE SET rol=excluded.rol, area_id=excluded.area_id, estado=excluded.estado""",
            (nombre, rol, area_id, estado),
        )
        return con.execute("SELECT id FROM agentes WHERE nombre = ?", (nombre,)).fetchone()["id"]


def registrar_tarea(agente_nombre: str, descripcion: str, curso: str | None = None,
                     estado: str = "pendiente", creado_en: str | None = None) -> int:
    """Los agentes llaman esta función para dejar constancia de una tarea nueva."""
    if estado not in ESTADOS_TAREA:
        raise ValueError(f"estado inválido: {estado}")
    ahora = creado_en or datetime.now().isoformat(timespec="seconds")
    with conexion() as con:
        agente = con.execute("SELECT id FROM agentes WHERE nombre = ?", (agente_nombre,)).fetchone()
        if agente is None:
            raise ValueError(f"agente desconocido: {agente_nombre}")
        cur = con.execute(
            """INSERT INTO tareas (agente_id, curso, descripcion, estado, creado_en, actualizado_en)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (agente["id"], curso, descripcion, estado, ahora, ahora),
        )
        return cur.lastrowid


def actualizar_estado_tarea(tarea_id: int, estado: str):
    if estado not in ESTADOS_TAREA:
        raise ValueError(f"estado inválido: {estado}")
    with conexion() as con:
        con.execute(
            "UPDATE tareas SET estado = ?, actualizado_en = ? WHERE id = ?",
            (estado, datetime.now().isoformat(timespec="seconds"), tarea_id),
        )


def agregar_memoria(tipo: str, clave: str, valor: str, curso: str | None = None, agente: str | None = None):
    with conexion() as con:
        con.execute(
            "INSERT INTO memoria (tipo, curso, agente, clave, valor, creado_en) VALUES (?, ?, ?, ?, ?, ?)",
            (tipo, curso, agente, clave, valor, datetime.now().isoformat(timespec="seconds")),
        )


def listar_memoria(limite: int = 500):
    with conexion() as con:
        return con.execute(
            "SELECT * FROM memoria ORDER BY creado_en DESC LIMIT ?", (limite,)
        ).fetchall()


def guardar_snapshot_materia(curso: str, trabajos: list, temas: list | None = None, alumnos: list | None = None,
                              anio_lectivo_id: int | None = None):
    """Guarda (reemplazando el anterior) el estado de una materia: actividades
    (entregadas/calificadas/pendientes), temas y nómina de alumnos. Lo llena
    panel_control.sync_materias; el dashboard solo lee (no llama a la API de
    Classroom directamente para no bloquear la carga de la página).

    `anio_lectivo_id=None` (el caso normal, ningún llamador actual lo pasa)
    usa el año lectivo activo — así cada año queda aislado y sincronizar una
    materia con el mismo nombre que tuvo el año anterior no pisa ni mezcla
    sus alumnos/entregas viejos.

    Si viene `alumnos`, además de quedar en el JSON de este snapshot se
    guarda (nombre, email) en la tabla `alumnos`, reemplazando la nómina
    anterior de esa materia/año — así queda consultable aparte, no solo
    embebido dentro del snapshot."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    datos = {"trabajos": trabajos, "temas": temas or [], "alumnos": alumnos or []}
    with conexion() as con:
        existente = con.execute(
            "SELECT id FROM materias_snapshot WHERE curso = ? AND anio_lectivo_id = ?",
            (curso, anio_lectivo_id),
        ).fetchone()
        ahora = datetime.now().isoformat(timespec="seconds")
        if existente:
            con.execute(
                "UPDATE materias_snapshot SET trabajos_json = ?, actualizado_en = ? WHERE id = ?",
                (json.dumps(datos), ahora, existente["id"]),
            )
        else:
            con.execute(
                "INSERT INTO materias_snapshot (curso, anio_lectivo_id, trabajos_json, actualizado_en) VALUES (?, ?, ?, ?)",
                (curso, anio_lectivo_id, json.dumps(datos), ahora),
            )

        if alumnos is not None:
            con.execute("DELETE FROM alumnos WHERE materia = ? AND anio_lectivo_id = ?", (curso, anio_lectivo_id))
            for a in alumnos:
                con.execute(
                    "INSERT INTO alumnos (anio_lectivo_id, materia, nombre, email, actualizado_en) VALUES (?, ?, ?, ?, ?)",
                    (anio_lectivo_id, curso, a.get("nombre", ""), a.get("email", ""), ahora),
                )


def listar_alumnos(materia: str | None = None, anio_lectivo_id: int | None = None):
    """Nómina guardada aparte del snapshot (misma info, tabla propia para
    poder consultarla directo). `anio_lectivo_id=None` usa el año activo."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    condiciones = ["anio_lectivo_id = ?"]
    parametros = [anio_lectivo_id]
    if materia:
        condiciones.append("materia = ?")
        parametros.append(materia)
    where = " AND ".join(condiciones)
    with conexion() as con:
        return con.execute(
            f"SELECT * FROM alumnos WHERE {where} ORDER BY materia, nombre", parametros
        ).fetchall()


def actualizar_diagnostico_alumno(materia: str, nombre: str, diagnostico: str | None, anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        con.execute(
            "UPDATE alumnos SET diagnostico = ? WHERE anio_lectivo_id = ? AND materia = ? AND nombre = ?",
            (diagnostico or None, anio_lectivo_id, materia, nombre),
        )


def agregar_comunicado(materia: str, alumno_nombre: str, tipo: str, fecha: str, observacion: str,
                        anio_lectivo_id: int | None = None) -> int:
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        cur = con.execute(
            """INSERT INTO comunicados (anio_lectivo_id, materia, alumno_nombre, tipo, fecha, observacion, creado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (anio_lectivo_id, materia, alumno_nombre, tipo, fecha, observacion,
             datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def listar_comunicados(materia: str | None = None, alumno_nombre: str | None = None, tipo: str | None = None,
                        anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    condiciones = ["anio_lectivo_id = ?"]
    parametros = [anio_lectivo_id]
    if materia:
        condiciones.append("materia = ?")
        parametros.append(materia)
    if alumno_nombre:
        condiciones.append("alumno_nombre = ?")
        parametros.append(alumno_nombre)
    if tipo:
        condiciones.append("tipo = ?")
        parametros.append(tipo)
    where = " AND ".join(condiciones)
    with conexion() as con:
        return con.execute(
            f"SELECT * FROM comunicados WHERE {where} ORDER BY fecha DESC, creado_en DESC", parametros
        ).fetchall()


def guardar_asistencia(materia: str, alumno_nombre: str, fecha: str, presente: bool,
                        anio_lectivo_id: int | None = None):
    """Upsert: pisa el registro de ese alumno/fecha si ya existía (para
    poder corregir sin duplicar)."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        con.execute(
            """INSERT INTO asistencias (anio_lectivo_id, materia, alumno_nombre, fecha, presente)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(anio_lectivo_id, materia, alumno_nombre, fecha) DO UPDATE SET presente = excluded.presente""",
            (anio_lectivo_id, materia, alumno_nombre, fecha, 1 if presente else 0),
        )


def listar_asistencias(materia: str, fecha: str | None = None, anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    condiciones = ["anio_lectivo_id = ?", "materia = ?"]
    parametros = [anio_lectivo_id, materia]
    if fecha:
        condiciones.append("fecha = ?")
        parametros.append(fecha)
    where = " AND ".join(condiciones)
    with conexion() as con:
        return con.execute(f"SELECT * FROM asistencias WHERE {where}", parametros).fetchall()


def calcular_pct_asistencia(materia: str, alumno_nombre: str, fecha_inicio: str, fecha_fin: str,
                             anio_lectivo_id: int | None = None) -> str:
    """Devuelve el % como texto ("83%") o "" si no hay clases tomadas en el rango."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        filas = con.execute(
            """SELECT presente FROM asistencias
               WHERE anio_lectivo_id = ? AND materia = ? AND alumno_nombre = ? AND fecha BETWEEN ? AND ?""",
            (anio_lectivo_id, materia, alumno_nombre, fecha_inicio, fecha_fin),
        ).fetchall()
    if not filas:
        return ""
    presentes = sum(1 for f in filas if f["presente"])
    return f"{round(100 * presentes / len(filas))}%"


def guardar_periodo(periodo: str, fecha_inicio: str, fecha_fin: str, anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        con.execute(
            """INSERT INTO periodos_evaluacion (anio_lectivo_id, periodo, fecha_inicio, fecha_fin)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(anio_lectivo_id, periodo) DO UPDATE SET fecha_inicio = excluded.fecha_inicio, fecha_fin = excluded.fecha_fin""",
            (anio_lectivo_id, periodo, fecha_inicio, fecha_fin),
        )


def listar_periodos(anio_lectivo_id: int | None = None) -> dict:
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM periodos_evaluacion WHERE anio_lectivo_id = ?", (anio_lectivo_id,)
        ).fetchall()
    return {f["periodo"]: {"fecha_inicio": f["fecha_inicio"], "fecha_fin": f["fecha_fin"]} for f in filas}


def guardar_fila_planilla(materia: str, alumno_nombre: str, valores: dict, anio_lectivo_id: int | None = None):
    """`valores` trae las claves que quiera pisar (c1_proc, c1_nota, c1_asist,
    c2_proc, c2_nota, c2_asist, dic_nota, dic_asist, final_proc, final_nota, final_asist)."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    columnas_validas = ("c1_proc", "c1_nota", "c1_asist", "c2_proc", "c2_nota", "c2_asist",
                         "dic_nota", "dic_asist", "final_proc", "final_nota", "final_asist")
    valores = {k: v for k, v in valores.items() if k in columnas_validas}
    ahora = datetime.now().isoformat(timespec="seconds")
    with conexion() as con:
        existente = con.execute(
            "SELECT id FROM planillas_notas WHERE anio_lectivo_id = ? AND materia = ? AND alumno_nombre = ?",
            (anio_lectivo_id, materia, alumno_nombre),
        ).fetchone()
        if existente:
            sets = ", ".join(f"{k} = ?" for k in valores)
            con.execute(
                f"UPDATE planillas_notas SET {sets}, actualizado_en = ? WHERE id = ?",
                (*valores.values(), ahora, existente["id"]),
            )
        else:
            columnas = ["anio_lectivo_id", "materia", "alumno_nombre", "actualizado_en"] + list(valores.keys())
            placeholders = ", ".join("?" for _ in columnas)
            con.execute(
                f"INSERT INTO planillas_notas ({', '.join(columnas)}) VALUES ({placeholders})",
                (anio_lectivo_id, materia, alumno_nombre, ahora, *valores.values()),
            )


def listar_planilla(materia: str, anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        return con.execute(
            "SELECT * FROM planillas_notas WHERE anio_lectivo_id = ? AND materia = ? ORDER BY alumno_nombre",
            (anio_lectivo_id, materia),
        ).fetchall()


def listar_snapshots_materias(anio_lectivo_id: int | None = None):
    """`anio_lectivo_id=None` usa el año activo — así la pestaña Materias y
    Agente Licencias automáticamente ven solo las materias del año en curso."""
    if anio_lectivo_id is None:
        from panel_control import anios
        anio_lectivo_id = anios.anio_activo_id()
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM materias_snapshot WHERE anio_lectivo_id = ? ORDER BY curso",
            (anio_lectivo_id,),
        ).fetchall()
    resultado = []
    for f in filas:
        datos = json.loads(f["trabajos_json"])
        # Compatibilidad con snapshots viejos (guardados como lista simple de trabajos).
        if isinstance(datos, list):
            datos = {"trabajos": datos, "temas": [], "alumnos": []}
        resultado.append({
            "curso": f["curso"],
            "trabajos": datos.get("trabajos", []),
            "temas": datos.get("temas", []),
            "alumnos": datos.get("alumnos", []),
            "actualizado_en": f["actualizado_en"],
        })
    return resultado


def crear_aprobacion(tarea_id: int, tipo: str, datos: dict) -> int:
    """Deja una acción crítica (ej. mandar un email a un alumno) esperando
    que el profesor la apruebe desde el panel antes de ejecutarse de verdad.
    `datos` debe traer todo lo necesario para ejecutar la acción al aprobar."""
    with conexion() as con:
        cur = con.execute(
            "INSERT INTO aprobaciones (tarea_id, tipo, datos_json, estado, creado_en) VALUES (?, ?, ?, 'pendiente', ?)",
            (tarea_id, tipo, json.dumps(datos), datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def listar_aprobaciones(estado: str | None = "pendiente"):
    with conexion() as con:
        if estado:
            filas = con.execute(
                "SELECT * FROM aprobaciones WHERE estado = ? ORDER BY creado_en", (estado,)
            ).fetchall()
        else:
            filas = con.execute("SELECT * FROM aprobaciones ORDER BY creado_en DESC").fetchall()
    return [dict(f, datos=json.loads(f["datos_json"])) for f in filas]


def obtener_aprobacion(aprobacion_id: int):
    with conexion() as con:
        f = con.execute("SELECT * FROM aprobaciones WHERE id = ?", (aprobacion_id,)).fetchone()
    if not f:
        return None
    return dict(f, datos=json.loads(f["datos_json"]))


def resolver_aprobacion(aprobacion_id: int, estado: str, tarea_estado: str, texto_final: str | None = None):
    """Marca la aprobación como resuelta (aprobada/rechazada) y actualiza la
    tarea asociada. Si `texto_final` viene (el profesor editó el borrador),
    lo guarda también en la aprobación para que quede el registro real de
    lo que se mandó."""
    with conexion() as con:
        ahora = datetime.now().isoformat(timespec="seconds")
        if texto_final is not None:
            fila = con.execute("SELECT datos_json, tarea_id FROM aprobaciones WHERE id = ?", (aprobacion_id,)).fetchone()
            datos = json.loads(fila["datos_json"])
            datos["respuesta"] = texto_final
            con.execute(
                "UPDATE aprobaciones SET estado = ?, datos_json = ?, resuelto_en = ? WHERE id = ?",
                (estado, json.dumps(datos), ahora, aprobacion_id),
            )
            tarea_id = fila["tarea_id"]
        else:
            con.execute(
                "UPDATE aprobaciones SET estado = ?, resuelto_en = ? WHERE id = ?",
                (estado, ahora, aprobacion_id),
            )
            tarea_id = con.execute("SELECT tarea_id FROM aprobaciones WHERE id = ?", (aprobacion_id,)).fetchone()["tarea_id"]
    actualizar_estado_tarea(tarea_id, tarea_estado)


def ya_se_genero_fecha_patria(fecha_iso: str) -> bool:
    with conexion() as con:
        fila = con.execute(
            "SELECT 1 FROM fechas_patrias_generadas WHERE fecha_iso = ?", (fecha_iso,)
        ).fetchone()
    return fila is not None


def marcar_fecha_patria_generada(fecha_iso: str, clave: str):
    with conexion() as con:
        con.execute(
            "INSERT OR IGNORE INTO fechas_patrias_generadas (fecha_iso, clave, generado_en) VALUES (?, ?, ?)",
            (fecha_iso, clave, datetime.now().isoformat(timespec="seconds")),
        )


def agregar_mensaje_chat_director(rol: str, mensaje: str):
    with conexion() as con:
        con.execute(
            "INSERT INTO chat_director (rol, mensaje, creado_en) VALUES (?, ?, ?)",
            (rol, mensaje, datetime.now().isoformat(timespec="seconds")),
        )


def listar_chat_director(limite: int = 50):
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM chat_director ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
    return [dict(f) for f in reversed(filas)]


def set_directiva(texto: str):
    """Guarda la 'prioridad del momento' que se muestra en el Centro de
    Operaciones. Es del profesor, nadie la escribe sola."""
    agregar_memoria("directiva", clave="actual", valor=texto)


def obtener_directiva() -> str:
    with conexion() as con:
        fila = con.execute(
            "SELECT valor FROM memoria WHERE tipo = 'directiva' ORDER BY creado_en DESC LIMIT 1"
        ).fetchone()
    return fila["valor"] if fila else ""


def contexto_curricular(curso: str, anio: str | None = None) -> str:
    """Referencias de diseño curricular cargadas para un curso (tipo='diseno_curricular'),
    si el profesor las agregó. Usado por los agentes que generan contenido pedagógico.

    `anio` (opcional, ej. "4º año") filtra solo las entradas de ESE año —
    útil cuando la misma materia tiene contenidos mínimos cargados para
    varios años (ej. "Laboratorio de Hardware 4º año" / "5º año" / "6º año").
    Si no hay ninguna entrada que matchee ese año (materia con un solo año
    cargado, o año no cargado), cae al comportamiento sin filtrar — nunca se
    queda sin contexto por pedir un año que no está."""
    with conexion() as con:
        if anio:
            filas_anio = con.execute(
                "SELECT valor FROM memoria WHERE tipo = 'diseno_curricular' AND curso = ? AND clave LIKE ?",
                (curso, f"%{anio}%"),
            ).fetchall()
            if filas_anio:
                return "\n".join(f["valor"] for f in filas_anio)
        filas = con.execute(
            "SELECT valor FROM memoria WHERE tipo = 'diseno_curricular' AND curso = ?",
            (curso,),
        ).fetchall()
    return "\n".join(f["valor"] for f in filas)


def guardar_actividad_cache(work_id: str, course_id: str, materia: str, titulo: str,
                             tipo: str | None = None, materials: list | None = None,
                             enunciado: str | None = None):
    """Cachea en la base una actividad de Classroom (título, tipo, adjuntos,
    y opcionalmente el enunciado ya extraído) para no depender de volver a
    pedirlo a la API — así el dashboard puede leer directo de acá sin tocar
    ningún botón. `enunciado=None` no pisa el que ya estuviera guardado (se
    llama primero sin enunciado al sincronizar la lista, y después aparte
    cuando se extrae el enunciado de verdad)."""
    with conexion() as con:
        ahora = datetime.now().isoformat(timespec="seconds")
        existente = con.execute(
            "SELECT enunciado FROM actividades_classroom WHERE work_id = ?", (work_id,)
        ).fetchone()
        enunciado_final = enunciado if enunciado is not None else (existente["enunciado"] if existente else None)
        con.execute(
            """INSERT INTO actividades_classroom
                   (work_id, course_id, materia, titulo, tipo, materials_json, enunciado, actualizado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(work_id) DO UPDATE SET
                   course_id=excluded.course_id, materia=excluded.materia, titulo=excluded.titulo,
                   tipo=excluded.tipo, materials_json=excluded.materials_json,
                   enunciado=excluded.enunciado, actualizado_en=excluded.actualizado_en""",
            (work_id, course_id, materia, titulo, tipo, json.dumps(materials or []), enunciado_final, ahora),
        )


def listar_actividades_cache(materia: str | None = None):
    with conexion() as con:
        if materia:
            filas = con.execute(
                "SELECT * FROM actividades_classroom WHERE materia = ? ORDER BY titulo", (materia,)
            ).fetchall()
        else:
            filas = con.execute("SELECT * FROM actividades_classroom ORDER BY materia, titulo").fetchall()
    resultado = []
    for f in filas:
        d = dict(f)
        d["materials"] = json.loads(d.pop("materials_json") or "[]")
        resultado.append(d)
    return resultado


def encolar_recursos_bulk(work_id: str, materia: str, titulo: str):
    """Anota una actividad para que buscar_recursos_bulk() la procese. Si ya
    está 'completado' o 'error' no la reinicia (para no repetir búsquedas ya
    hechas cuando se vuelve a sincronizar)."""
    with conexion() as con:
        ya_existe = con.execute("SELECT 1 FROM recursos_bulk WHERE work_id = ?", (work_id,)).fetchone()
        if ya_existe:
            return
        con.execute(
            "INSERT INTO recursos_bulk (work_id, materia, titulo, estado, actualizado_en) VALUES (?, ?, ?, 'pendiente', ?)",
            (work_id, materia, titulo, datetime.now().isoformat(timespec="seconds")),
        )


def resolver_recursos_bulk(work_id: str, estado: str, recursos: list | None = None, error: str | None = None):
    with conexion() as con:
        con.execute(
            "UPDATE recursos_bulk SET estado = ?, recursos_json = ?, error = ?, actualizado_en = ? WHERE work_id = ?",
            (estado, json.dumps(recursos) if recursos is not None else None, error,
             datetime.now().isoformat(timespec="seconds"), work_id),
        )


def listar_recursos_bulk(materia: str | None = None, estado: str | None = None):
    condiciones, parametros = [], []
    if materia:
        condiciones.append("materia = ?")
        parametros.append(materia)
    if estado:
        condiciones.append("estado = ?")
        parametros.append(estado)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with conexion() as con:
        filas = con.execute(f"SELECT * FROM recursos_bulk {where} ORDER BY materia, titulo", parametros).fetchall()
    resultado = []
    for f in filas:
        d = dict(f)
        d["recursos"] = json.loads(d.pop("recursos_json")) if d["recursos_json"] else []
        resultado.append(d)
    return resultado


def contar_pendientes_recursos_bulk() -> int:
    with conexion() as con:
        return con.execute("SELECT COUNT(*) c FROM recursos_bulk WHERE estado = 'pendiente'").fetchone()["c"]


def listar_areas():
    with conexion() as con:
        return con.execute("SELECT * FROM areas ORDER BY id").fetchall()


def listar_agentes():
    with conexion() as con:
        return con.execute(
            """SELECT agentes.*, areas.nombre AS area_nombre
               FROM agentes JOIN areas ON agentes.area_id = areas.id
               ORDER BY areas.id, agentes.id"""
        ).fetchall()


def actualizar_estado_agente(nombre: str, estado: str):
    """Prende/apaga un agente (estado 'activo'/'inactivo'). Un agente
    apagado no deja de existir ni pierde su historial — el dashboard es
    quien decide no dejar generar trabajo nuevo mientras esté así."""
    with conexion() as con:
        con.execute("UPDATE agentes SET estado = ? WHERE nombre = ?", (estado, nombre))


def registrar_uso_proveedor(proveedor: str):
    """Se llama cada vez que un proveedor de IA responde de verdad (no cuando
    falla). No mide cuota restante (la mayoría de los proveedores gratuitos
    no lo exponen por API) — mide cuántas veces lo usamos nosotros, que es
    100% exacto porque lo controlamos nosotros."""
    with conexion() as con:
        con.execute(
            "INSERT INTO uso_proveedores (proveedor, creado_en) VALUES (?, ?)",
            (proveedor, datetime.now().isoformat(timespec="seconds")),
        )


def contar_uso_proveedores_hoy() -> dict:
    hoy = datetime.now().date().isoformat()
    with conexion() as con:
        filas = con.execute(
            "SELECT proveedor, COUNT(*) c FROM uso_proveedores WHERE creado_en >= ? GROUP BY proveedor ORDER BY c DESC",
            (hoy,),
        ).fetchall()
    return {f["proveedor"]: f["c"] for f in filas}


def agente_esta_activo(nombre: str) -> bool:
    """True si el agente está activo o todavía no fue registrado (para no
    bloquear por default a un agente que nunca se prendió/apagó)."""
    with conexion() as con:
        fila = con.execute("SELECT estado FROM agentes WHERE nombre = ?", (nombre,)).fetchone()
    return fila is None or fila["estado"] == "activo"


def listar_tareas(estado: str | None = None, agente: str | None = None, curso: str | None = None, limite: int = 200):
    condiciones = []
    parametros = []
    if estado:
        condiciones.append("tareas.estado = ?")
        parametros.append(estado)
    if agente:
        condiciones.append("agentes.nombre = ?")
        parametros.append(agente)
    if curso:
        condiciones.append("tareas.curso = ?")
        parametros.append(curso)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    q = f"""SELECT tareas.*, agentes.nombre AS agente_nombre, areas.nombre AS area_nombre
            FROM tareas
            JOIN agentes ON tareas.agente_id = agentes.id
            JOIN areas ON agentes.area_id = areas.id
            {where}
            ORDER BY tareas.creado_en DESC LIMIT ?"""
    parametros.append(limite)
    with conexion() as con:
        return con.execute(q, parametros).fetchall()


def metricas():
    with conexion() as con:
        total = con.execute("SELECT COUNT(*) c FROM tareas").fetchone()["c"]
        por_estado = {
            r["estado"]: r["c"]
            for r in con.execute("SELECT estado, COUNT(*) c FROM tareas GROUP BY estado").fetchall()
        }
        agentes = con.execute("SELECT COUNT(*) c FROM agentes").fetchone()["c"]
        areas = con.execute("SELECT COUNT(*) c FROM areas").fetchone()["c"]
        return {"total_tareas": total, "por_estado": por_estado, "agentes": agentes, "areas": areas}
