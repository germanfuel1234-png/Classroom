"""Archivador de materiales por materia + número de actividad.

Guarda cualquier archivo (consigna original, rúbrica, resolución modelo,
lo que el profesor quiera) directo en la base (panel_control/panel.db),
identificado por materia y un número de actividad que el profesor elige
(no depende de cómo esté numerado en Classroom). Solo guarda y permite
bajar después — ningún agente lo lee todavía.

Cada (materia, número) tiene además un nombre registrado en `actividades`
— así "Actividad 1" de una materia se llama siempre igual aunque tenga
varios archivos adjuntos, o todavía ninguno.

Acotado por año lectivo igual que horarios/materias_snapshot: los
materiales de 2026 no se mezclan con los de 2027.
"""
from datetime import datetime

from panel_control import anios, memoria


def registrar_actividad(materia: str, numero: int, nombre: str, anio_lectivo_id: int | None = None) -> int:
    """Crea o renombra la actividad (materia, número) del año dado. Devuelve su id."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    with memoria.conexion() as con:
        con.execute(
            """INSERT INTO actividades (anio_lectivo_id, materia, numero, nombre, creado_en)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(anio_lectivo_id, materia, numero) DO UPDATE SET nombre = excluded.nombre""",
            (anio_lectivo_id, materia, numero, nombre, datetime.now().isoformat(timespec="seconds")),
        )
        return con.execute(
            "SELECT id FROM actividades WHERE anio_lectivo_id = ? AND materia = ? AND numero = ?",
            (anio_lectivo_id, materia, numero),
        ).fetchone()["id"]


def obtener_nombre_actividad(materia: str, numero: int, anio_lectivo_id: int | None = None) -> str | None:
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    with memoria.conexion() as con:
        fila = con.execute(
            "SELECT nombre FROM actividades WHERE anio_lectivo_id = ? AND materia = ? AND numero = ?",
            (anio_lectivo_id, materia, numero),
        ).fetchone()
    return fila["nombre"] if fila else None


def listar_actividades(materia: str | None = None, anio_lectivo_id: int | None = None):
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    condiciones = ["anio_lectivo_id = ?"]
    parametros = [anio_lectivo_id]
    if materia:
        condiciones.append("materia = ?")
        parametros.append(materia)
    where = " AND ".join(condiciones)
    with memoria.conexion() as con:
        return con.execute(
            f"SELECT * FROM actividades WHERE {where} ORDER BY materia, numero", parametros
        ).fetchall()


def subir_material(materia: str, numero_actividad: int, nombre_actividad: str, nombre_archivo: str,
                    contenido: bytes, tipo_mime: str | None = None, anio_lectivo_id: int | None = None) -> int:
    """Registra/actualiza el nombre de la actividad (materia, numero_actividad)
    y guarda el archivo adjunto a ella."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    if nombre_actividad and nombre_actividad.strip():
        registrar_actividad(materia, numero_actividad, nombre_actividad.strip(), anio_lectivo_id)
    with memoria.conexion() as con:
        cur = con.execute(
            """INSERT INTO materiales
               (anio_lectivo_id, materia, numero_actividad, nombre_archivo, tipo_mime, contenido, tamano_bytes, subido_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (anio_lectivo_id, materia, numero_actividad, nombre_archivo, tipo_mime,
             contenido, len(contenido), datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def listar_materiales(materia: str | None = None, numero_actividad: int | None = None,
                       anio_lectivo_id: int | None = None):
    """No trae `contenido` (el archivo puede pesar) — para eso está obtener_material."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    condiciones = ["anio_lectivo_id = ?"]
    parametros = [anio_lectivo_id]
    if materia:
        condiciones.append("materia = ?")
        parametros.append(materia)
    if numero_actividad is not None:
        condiciones.append("numero_actividad = ?")
        parametros.append(numero_actividad)
    where = " AND ".join(condiciones)
    with memoria.conexion() as con:
        return con.execute(
            f"""SELECT id, materia, numero_actividad, nombre_archivo, tipo_mime, tamano_bytes, subido_en
                FROM materiales WHERE {where}
                ORDER BY materia, numero_actividad, subido_en DESC""",
            parametros,
        ).fetchall()


def resumen_completo(anio_lectivo_id: int | None = None):
    """Une actividades registradas (materia + número + nombre) con sus
    materiales adjuntos, una fila por actividad — para ver de un vistazo,
    tipo planilla, qué materia tiene qué actividades y cuáles ya tienen
    archivo subido y cuáles todavía no."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    archivos_por_actividad = {}
    for m in listar_materiales(anio_lectivo_id=anio_lectivo_id):
        clave = (m["materia"], m["numero_actividad"])
        archivos_por_actividad.setdefault(clave, []).append(m["nombre_archivo"])

    resumen = []
    for a in listar_actividades(anio_lectivo_id=anio_lectivo_id):
        archivos = archivos_por_actividad.get((a["materia"], a["numero"]), [])
        resumen.append({
            "materia": a["materia"], "numero": a["numero"], "nombre": a["nombre"],
            "archivos": archivos, "cantidad_archivos": len(archivos),
        })
    return resumen


def obtener_material(material_id: int):
    with memoria.conexion() as con:
        return con.execute("SELECT * FROM materiales WHERE id = ?", (material_id,)).fetchone()


def eliminar_material(material_id: int):
    with memoria.conexion() as con:
        con.execute("DELETE FROM materiales WHERE id = ?", (material_id,))
