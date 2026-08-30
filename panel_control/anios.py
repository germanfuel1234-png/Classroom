"""Años lectivos.

Cada año (2026, 2027, ...) tiene exactamente un registro `activo` a la vez.
El horario y las materias que ve el resto del sistema por defecto
(panel_control.horario, memoria.guardar_snapshot_materia/listar_snapshots_materias)
son siempre los del año activo, así que iniciar un año nuevo es lo único que
hace falta para que todo el panel "salte" a trabajar sobre él.

Uso interactivo: python -m panel_control.anios
"""
from datetime import datetime

from panel_control import memoria


def anio_activo():
    """Fila completa (id, anio, activo, creado_en) del año lectivo activo, o
    None si por algún motivo no hay ninguno (no debería pasar tras init_db)."""
    with memoria.conexion() as con:
        return con.execute("SELECT * FROM anios_lectivos WHERE activo = 1 LIMIT 1").fetchone()


def anio_activo_id() -> int:
    fila = anio_activo()
    if not fila:
        raise RuntimeError("No hay ningún año lectivo activo. Corré memoria.init_db() primero.")
    return fila["id"]


def listar_anios():
    with memoria.conexion() as con:
        return con.execute("SELECT * FROM anios_lectivos ORDER BY anio DESC").fetchall()


def crear_anio(anio: int, activar: bool = False) -> int:
    """Crea el año lectivo si no existe (no falla si ya estaba). Devuelve su id."""
    with memoria.conexion() as con:
        con.execute(
            "INSERT OR IGNORE INTO anios_lectivos (anio, activo, creado_en) VALUES (?, 0, ?)",
            (anio, datetime.now().isoformat(timespec="seconds")),
        )
        anio_id = con.execute("SELECT id FROM anios_lectivos WHERE anio = ?", (anio,)).fetchone()["id"]
        if activar:
            con.execute("UPDATE anios_lectivos SET activo = 0")
            con.execute("UPDATE anios_lectivos SET activo = 1 WHERE id = ?", (anio_id,))
        return anio_id


def activar_anio(anio_id: int):
    with memoria.conexion() as con:
        fila = con.execute("SELECT id FROM anios_lectivos WHERE id = ?", (anio_id,)).fetchone()
        if not fila:
            raise ValueError(f"No existe el año lectivo con id={anio_id}")
        con.execute("UPDATE anios_lectivos SET activo = 0")
        con.execute("UPDATE anios_lectivos SET activo = 1 WHERE id = ?", (anio_id,))


def iniciar_anio_nuevo(anio_nuevo: int) -> int:
    """Crea `anio_nuevo`, le clona el horario completo del año activo (mismos
    valores — el profesor corrige después lo que cambió: el año dentro del
    nombre del curso de Classroom, cambios de grado, etc.) y lo activa.

    A propósito NO toca materias_snapshot: alumnos y calificaciones tienen
    que salir siempre frescos de Classroom cuando se sincronice el año
    nuevo, nunca arrastrados del año anterior.

    Lanza ValueError si `anio_nuevo` ya existe (no se reinicia un año por
    esta vía, para no pisar horario que el profesor ya haya cargado)."""
    with memoria.conexion() as con:
        ya_existe = con.execute("SELECT 1 FROM anios_lectivos WHERE anio = ?", (anio_nuevo,)).fetchone()
        if ya_existe:
            raise ValueError(f"El año lectivo {anio_nuevo} ya existe.")

        anio_previo = con.execute("SELECT id FROM anios_lectivos WHERE activo = 1 LIMIT 1").fetchone()

        cur = con.execute(
            "INSERT INTO anios_lectivos (anio, activo, creado_en) VALUES (?, 0, ?)",
            (anio_nuevo, datetime.now().isoformat(timespec="seconds")),
        )
        anio_nuevo_id = cur.lastrowid

        if anio_previo:
            bloques = con.execute(
                """SELECT dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar
                   FROM horarios WHERE anio_lectivo_id = ?""",
                (anio_previo["id"],),
            ).fetchall()
            for b in bloques:
                con.execute(
                    """INSERT INTO horarios
                       (anio_lectivo_id, dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (anio_nuevo_id, b["dia"], b["hora_inicio"], b["hora_fin"], b["materia"],
                     b["curso_grupo"], b["curso_classroom"], b["verificar"]),
                )

        con.execute("UPDATE anios_lectivos SET activo = 0")
        con.execute("UPDATE anios_lectivos SET activo = 1 WHERE id = ?", (anio_nuevo_id,))

        return anio_nuevo_id


def menu():
    memoria.init_db()
    activo = anio_activo()
    print(f"Año lectivo activo: {activo['anio'] if activo else '(ninguno)'}")
    print("\nAños cargados:")
    for a in listar_anios():
        marca = " (activo)" if a["activo"] else ""
        print(f"  {a['anio']}{marca}")

    resp = input("\n¿Iniciar un año lectivo nuevo? (número de año, o Enter para salir): ").strip()
    if not resp:
        return
    try:
        anio_nuevo = int(resp)
    except ValueError:
        print("Año inválido.")
        return
    nuevo_id = iniciar_anio_nuevo(anio_nuevo)
    print(f"Año {anio_nuevo} iniciado y activado (id={nuevo_id}). Horario clonado del año anterior — revisalo en el panel.")


if __name__ == "__main__":
    menu()
