"""Agente de Fechas Patrias.

Todos los días (vía cron, ver panel_control/scripts/revisar_fechas_patrias.py)
se fija si hoy es una fecha patria (panel_control.fechas_patrias) y, si lo
es, deja UN borrador esperando aprobación — que al aprobarse una sola vez
publica el mismo saludo como anuncio en TODAS las materias activas
(agente_publicador.aprobar_y_publicar_global).

No genera nada con IA (el mensaje es fijo, ver fechas_patrias.py) y nunca
publica solo — como todo lo demás del panel, pasa por Aprobaciones.
"""
import datetime

from panel_control import fechas_patrias, memoria
from panel_control.identidad import NOMBRE_PROFESOR

AGENTE = "Agente Fechas Patrias"
AREA = "Publicaciones"


def revisar_y_encolar(fecha: datetime.date | None = None):
    """Se corre una vez por día. Devuelve el aprobacion_id si hoy es una
    fecha patria y se dejó un borrador nuevo; None si hoy no es una fecha
    patria o si ya se había generado el borrador de hoy (evita duplicar si
    el cron corre más de una vez el mismo día)."""
    fecha = fecha or datetime.date.today()
    entrada = fechas_patrias.fecha_de_hoy(fecha)
    if not entrada:
        return None

    fecha_iso = fecha.isoformat()
    if memoria.ya_se_genero_fecha_patria(fecha_iso):
        return None

    memoria.agregar_agente(AGENTE, "Detecta fechas patrias y arma el saludo para publicar en todas las materias", AREA)

    mensaje = f"{entrada['mensaje']}\n\n— {NOMBRE_PROFESOR}"

    tarea_id = memoria.registrar_tarea(
        AGENTE, f"{entrada['nombre']} — saludo listo para publicar en todas las materias, esperando tu aprobación",
        estado="pendiente_aprobacion",
    )
    aprobacion_id = memoria.crear_aprobacion(tarea_id, tipo="anuncio_global", datos={
        "clave": entrada["clave"], "nombre_fecha": entrada["nombre"],
        "mensaje": mensaje, "fecha_iso": fecha_iso,
    })
    memoria.marcar_fecha_patria_generada(fecha_iso, entrada["clave"])
    return aprobacion_id
