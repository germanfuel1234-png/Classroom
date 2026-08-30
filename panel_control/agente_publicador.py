"""Agente Publicador.

Redacta tareas y anuncios nuevos para Classroom a partir de un tema/brief
que le das, y los deja como BORRADOR esperando tu aprobación (mismo
mecanismo de panel_control.memoria.aprobaciones que usa el Agente
Consultas). Nunca publica nada en Classroom por su cuenta.

Uso interactivo: python -m panel_control.agente_publicador
"""
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import main as classroom  # reutiliza OAuth y listados ya probados
from panel_control import materiales, memoria, proveedor_ia, recursos_educativos

AGENTE = "Agente Publicador"
AREA = "Publicaciones"

_REGEX_YOUTUBE_ID = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})")


def construir_prompt_publicacion(nombre_materia, tipo_publicacion, tema, contexto_curricular=""):
    seccion_curricular = ""
    if contexto_curricular.strip():
        seccion_curricular = (
            "\n---- DISEÑO CURRICULAR DE REFERENCIA (respetalo) ----\n"
            f"{contexto_curricular}\n"
        )
    if tipo_publicacion == "tarea":
        instrucciones = (
            "Redactá la consigna completa de un Trabajo Práctico nuevo para Classroom sobre el tema "
            "indicado. Primera línea: solo el título, corto. Después: breve introducción, la consigna "
            "con preguntas o ejercicios numerados, y qué se espera que entreguen. NO agregues "
            "aclaraciones de formato de entrega (carátula, imagen ilustrativa, etc.), eso ya se lo "
            "exige el profesor aparte a cada entrega."
        )
    else:
        instrucciones = (
            "Redactá un anuncio breve (2-4 párrafos) para publicar en el muro de Classroom sobre el "
            "tema indicado. Primera línea: solo el título, corto. Después el cuerpo, tono cercano y "
            "claro, sin firma."
        )
    return (
        f"Sos el profesor de \"{nombre_materia}\" en una escuela técnica secundaria.\n"
        f"{instrucciones}\n"
        + seccion_curricular +
        f"\n---- TEMA / BRIEF ----\n{tema}\n"
    )


def generar_titulo_y_cuerpo(nombre_materia, tipo_publicacion, tema, contexto_curricular=""):
    prompt = construir_prompt_publicacion(nombre_materia, tipo_publicacion, tema, contexto_curricular)
    texto, proveedor = proveedor_ia.generar_texto(prompt)
    lineas = texto.strip().split("\n", 1)
    titulo = lineas[0].strip().strip("#*").strip()[:100] if lineas else tema[:100]
    cuerpo = lineas[1].strip() if len(lineas) > 1 else texto
    return titulo, cuerpo, proveedor


def crear_borrador_publicacion(nombre_materia, course_id, tipo_publicacion, tema,
                                fecha_entrega=None, puntos=None, buscar_recursos=False):
    """Genera el texto con IA y deja la publicación en la cola de aprobación.

    Si `buscar_recursos=True` (solo tiene efecto para tipo_publicacion=="tarea"),
    además busca con panel_control.recursos_educativos (grounding real de
    Gemini, no inventa links) bibliografía/videos/manuales sobre el tema y
    los deja guardados en la aprobación como sugerencia — el profesor los
    revisa y confirma cuáles adjuntar antes de publicar. Si la búsqueda
    falla (sin Gemini, cuota agotada, etc.) el borrador se genera igual,
    solo que sin recursos sugeridos."""
    contexto_curricular = memoria.contexto_curricular(nombre_materia)
    titulo, cuerpo, proveedor = generar_titulo_y_cuerpo(nombre_materia, tipo_publicacion, tema, contexto_curricular)

    recursos_sugeridos = []
    aviso_recursos = None
    if buscar_recursos and tipo_publicacion == "tarea":
        try:
            recursos_sugeridos = recursos_educativos.buscar_recursos(nombre_materia, tema)
        except Exception as e:
            aviso_recursos = f"No se pudieron buscar recursos para adjuntar: {str(e)[:200]}"

    tarea_id = memoria.registrar_tarea(
        AGENTE, f"{tipo_publicacion.capitalize()} '{titulo}' — esperando tu aprobación",
        curso=nombre_materia, estado="pendiente_aprobacion",
    )
    aprobacion_id = memoria.crear_aprobacion(tarea_id, tipo="publicacion_classroom", datos={
        "course_id": course_id,
        "materia": nombre_materia,
        "tipo_publicacion": tipo_publicacion,
        "titulo": titulo,
        "descripcion": cuerpo,
        "fecha_entrega": fecha_entrega,
        "puntos": puntos,
        "proveedor": proveedor,
        "agente": AGENTE,
        "recursos_sugeridos": recursos_sugeridos,
    })
    print(f"📝 Borrador de {tipo_publicacion} listo: '{titulo}' (vía {proveedor}) — esperando tu aprobación en el panel")
    if recursos_sugeridos:
        print(f"   + {len(recursos_sugeridos)} recurso(s) sugerido(s) para adjuntar")
    if aviso_recursos:
        print(f"   ⚠️ {aviso_recursos}")
    return aprobacion_id


def _material_desde_recurso(recurso):
    """Convierte un recurso {tipo, titulo, url} en un material de Classroom.
    Si la URL es un video de YouTube usa el tipo nativo youtubeVideo
    (se embebe con miniatura); si no, un link normal con título."""
    if recurso.get("tipo") == "video":
        match = _REGEX_YOUTUBE_ID.search(recurso.get("url", ""))
        if match:
            return {"youtubeVideo": {"id": match.group(1)}}
    return {"link": {"url": recurso["url"], "title": recurso.get("titulo", recurso["url"])}}


def _construir_body_tarea(datos, recursos_confirmados=None):
    body = {
        "title": datos["titulo"],
        "description": datos["descripcion"],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }
    if datos.get("puntos") is not None:
        body["maxPoints"] = datos["puntos"]
    if datos.get("fecha_entrega"):
        anio, mes, dia = datos["fecha_entrega"].split("-")
        body["dueDate"] = {"year": int(anio), "month": int(mes), "day": int(dia)}
        body["dueTime"] = {"hours": 23, "minutes": 59}
    if recursos_confirmados:
        body["materials"] = [_material_desde_recurso(r) for r in recursos_confirmados]
    return body


def aprobar_y_publicar(aprobacion_id, creds, titulo_editado=None, descripcion_editada=None, recursos_confirmados=None):
    """Se llama desde el panel cuando el profesor aprueba el borrador. Recién
    acá se publica de verdad en Classroom. `recursos_confirmados` es la
    lista de recursos sugeridos que el profesor dejó tildados en el panel
    (puede venir vacía o None — no se adjunta nada en ese caso). Devuelve
    (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = dict(ap["datos"])
    if titulo_editado is not None:
        datos["titulo"] = titulo_editado
    if descripcion_editada is not None:
        datos["descripcion"] = descripcion_editada

    service = build("classroom", "v1", credentials=creds)
    try:
        if datos["tipo_publicacion"] == "tarea":
            resultado = service.courses().courseWork().create(
                courseId=datos["course_id"], body=_construir_body_tarea(datos, recursos_confirmados)
            ).execute()
        else:
            resultado = service.courses().announcements().create(
                courseId=datos["course_id"],
                body={"text": f"{datos['titulo']}\n\n{datos['descripcion']}", "state": "PUBLISHED"},
            ).execute()
    except HttpError as e:
        return False, f"Classroom rechazó la publicación: {str(e)[:200]}"
    except Exception as e:
        return False, f"No se pudo publicar: {str(e)[:200]}"

    link = resultado.get("alternateLink", "")
    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada")
    memoria.agregar_memoria(
        "publicacion_classroom", clave=datos["titulo"], valor=link or "publicado",
        curso=datos["materia"], agente=AGENTE,
    )
    return True, f"Publicado en Classroom. {link}"


def rechazar(aprobacion_id):
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap or ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."
    memoria.resolver_aprobacion(aprobacion_id, estado="rechazada", tarea_estado="rechazada")
    return True, "Rechazada."


def _leer_materials_actuales(service, course_id, work_id):
    """Trae los materials tal cual están HOY en Classroom para esa
    actividad. Hace falta porque courseWork().patch(updateMask="materials")
    reemplaza el array entero — si no se leen los actuales primero y se
    reenvían junto con los nuevos, se pierden los adjuntos que ya tenía."""
    actividad = service.courses().courseWork().get(courseId=course_id, id=work_id).execute()
    return actividad.get("materials", [])


def crear_borrador_adjuntar_bibliografia(nombre_materia, course_id, work_id, titulo_actividad, recursos):
    """Deja pendiente de aprobación sumarle a una actividad YA PUBLICADA
    los recursos (bibliografía/videos/manuales) que ya encontramos con IA
    — como adjuntos reales de Classroom (materials), no como texto dentro
    de la consigna."""
    tarea_id = memoria.registrar_tarea(
        AGENTE, f"Adjuntar bibliografía a '{titulo_actividad}' — esperando tu aprobación",
        curso=nombre_materia, estado="pendiente_aprobacion",
    )
    aprobacion_id = memoria.crear_aprobacion(tarea_id, tipo="adjuntar_bibliografia_existente", datos={
        "course_id": course_id, "work_id": work_id, "materia": nombre_materia,
        "titulo_actividad": titulo_actividad, "recursos_sugeridos": recursos,
    })
    return aprobacion_id


def aprobar_y_adjuntar_bibliografia(aprobacion_id, creds, recursos_confirmados):
    """Se llama desde el panel al aprobar: recién acá se suman los
    recursos de verdad en Classroom, sin perder los materials que ya
    tenía la actividad. Devuelve (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = ap["datos"]
    service = build("classroom", "v1", credentials=creds)
    try:
        materials_actuales = _leer_materials_actuales(service, datos["course_id"], datos["work_id"])
        nuevos = [_material_desde_recurso(r) for r in (recursos_confirmados or [])]
        service.courses().courseWork().patch(
            courseId=datos["course_id"], id=datos["work_id"],
            updateMask="materials",
            body={"materials": materials_actuales + nuevos},
        ).execute()
    except HttpError as e:
        return False, f"Classroom rechazó el cambio: {str(e)[:200]}"
    except Exception as e:
        return False, f"No se pudo adjuntar: {str(e)[:200]}"

    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada")
    memoria.agregar_memoria(
        "bibliografia_adjuntada", clave=datos["titulo_actividad"], valor=f"{len(nuevos)} recurso(s) adjuntado(s)",
        curso=datos["materia"], agente=AGENTE,
    )
    return True, f"Listo, se adjuntaron {len(nuevos)} recurso(s) a '{datos['titulo_actividad']}' en Classroom."


def _subir_archivo_a_drive(service_drive, nombre_archivo, contenido, tipo_mime):
    """Sube un archivo al Drive del profesor (dueño del token) — mismo
    resultado que usar el botón 'Subir' del panel de Adjuntar en
    Classroom. Devuelve el id del archivo nuevo en Drive."""
    from googleapiclient.http import MediaIoBaseUpload
    import io
    media = MediaIoBaseUpload(io.BytesIO(contenido), mimetype=tipo_mime or "application/octet-stream", resumable=False)
    archivo_drive = service_drive.files().create(
        body={"name": nombre_archivo}, media_body=media, fields="id",
    ).execute()
    return archivo_drive["id"]


def crear_borrador_reemplazo_material(nombre_materia, course_id, work_id, titulo_actividad, material_id):
    """Deja pendiente de aprobación reemplazar el archivo adjunto de una
    actividad YA PUBLICADA por la mejora que el profesor ya subió a la
    tabla local `materiales` (identificada por `material_id`). No duplica
    el archivo en el JSON de la aprobación — se relee recién al aprobar."""
    tarea_id = memoria.registrar_tarea(
        AGENTE, f"Subir mejora a '{titulo_actividad}' en Classroom — esperando tu aprobación",
        curso=nombre_materia, estado="pendiente_aprobacion",
    )
    aprobacion_id = memoria.crear_aprobacion(tarea_id, tipo="reemplazar_material", datos={
        "course_id": course_id, "work_id": work_id, "materia": nombre_materia,
        "titulo_actividad": titulo_actividad, "material_id": material_id,
    })
    return aprobacion_id


def aprobar_y_reemplazar_material(aprobacion_id, creds):
    """Se llama desde el panel al aprobar: sube el archivo a Drive, lo
    adjunta a la actividad y saca los adjuntos tipo archivo que hubiera
    antes (los links/videos ya adjuntos quedan intactos). Devuelve
    (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = ap["datos"]
    archivo = materiales.obtener_material(datos["material_id"])
    if not archivo:
        return False, "El archivo local ya no existe (¿lo borraste?)."

    service = build("classroom", "v1", credentials=creds)
    service_drive = build("drive", "v3", credentials=creds)
    try:
        nuevo_id_drive = _subir_archivo_a_drive(
            service_drive, archivo["nombre_archivo"], archivo["contenido"], archivo["tipo_mime"]
        )
        materials_actuales = _leer_materials_actuales(service, datos["course_id"], datos["work_id"])
        materials_sin_archivos_viejos = [m for m in materials_actuales if "driveFile" not in m]
        nuevo_material = {"driveFile": {"driveFile": {"id": nuevo_id_drive}, "shareMode": "VIEW"}}
        service.courses().courseWork().patch(
            courseId=datos["course_id"], id=datos["work_id"],
            updateMask="materials",
            body={"materials": materials_sin_archivos_viejos + [nuevo_material]},
        ).execute()
    except HttpError as e:
        return False, f"Classroom rechazó el cambio: {str(e)[:200]}"
    except Exception as e:
        return False, f"No se pudo subir/adjuntar: {str(e)[:200]}"

    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada")
    memoria.agregar_memoria(
        "material_reemplazado", clave=datos["titulo_actividad"], valor=archivo["nombre_archivo"],
        curso=datos["materia"], agente=AGENTE,
    )
    return True, f"Listo, se reemplazó el archivo de '{datos['titulo_actividad']}' en Classroom."


def menu():
    memoria.init_db()
    memoria.agregar_agente(AGENTE, "Redacta tareas/anuncios nuevos y los deja para tu aprobación", AREA)

    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)

    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        return
    print("\nMaterias activas:")
    for i, c in enumerate(cursos, start=1):
        print(f"  [{i}] {c.get('name')}")
    idx = int(input("Elegí una materia: ")) - 1
    curso = cursos[idx]

    tipo_publicacion = ""
    while tipo_publicacion not in ("tarea", "anuncio"):
        tipo_publicacion = input("¿Tarea o anuncio? [tarea/anuncio]: ").strip().lower()

    tema = input("Tema / brief (de qué trata): ").strip()

    fecha_entrega = None
    puntos = None
    if tipo_publicacion == "tarea":
        fecha_entrega = input("Fecha de entrega (YYYY-MM-DD, opcional, Enter para omitir): ").strip() or None
        puntos_str = input("Puntaje máximo (opcional, Enter para omitir): ").strip()
        puntos = int(puntos_str) if puntos_str else None

    crear_borrador_publicacion(curso.get("name"), curso["id"], tipo_publicacion, tema, fecha_entrega, puntos)


if __name__ == "__main__":
    menu()
