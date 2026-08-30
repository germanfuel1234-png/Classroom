"""Búsqueda de recursos educativos reales (bibliografía, videos, manuales)
para adjuntar a un TP nuevo.

A diferencia de panel_control.proveedor_ia, esto NO tiene cadena de
fallback entre proveedores: DeepSeek/Groq/OpenRouter/NVIDIA/Mistral/local
son de solo texto y, si se les pide "buscá un video", inventan una URL que
suena real pero no existe. La única pieza ya integrada capaz de buscar en
la web de verdad es Gemini con grounding de Google Search — así que si
Gemini no está disponible, esto falla visible en vez de arriesgarse a
mandarle a un alumno un link inventado.

Detalle importante confirmado en pruebas reales: Gemini devuelve las URLs
encontradas ya sea vía grounding_metadata.grounding_chunks — nunca hay que
confiar en URLs que el modelo haya escrito en el texto libre, esas sí
pueden estar inventadas aunque la búsqueda haya sido real. Además esas URLs
vienen envueltas en un redirect de Google (vertexaisearch.cloud.google.com)
y el "título" que da la API es solo el dominio (ej. "youtube.com"), no un
título descriptivo de la página — por eso acá se resuelve el redirect a la
URL real (para poder detectar YouTube/manuales y armar un link limpio) y
el título que se guarda es honesto y simple, no uno inventado.
"""
import os
import re
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_DOMINIOS_MANUAL = (
    "docs.python.org", "cplusplus.com", "cppreference.com", "developer.mozilla.org",
    "docs.microsoft.com", "learn.microsoft.com", "docs.oracle.com", "readthedocs.io",
)

_REGEX_YOUTUBE_ID = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})")


def _resolver_url_real(url_redirect: str) -> str:
    """El link que devuelve el grounding de Gemini es un redirect de Google
    (vertexaisearch.cloud.google.com/...). Lo resuelve a la URL real de
    destino con un HEAD; si falla por lo que sea, devuelve el redirect tal
    cual (sigue funcionando al hacer clic, solo que no se puede clasificar
    ni limpiar)."""
    try:
        resp = requests.head(url_redirect, allow_redirects=True, timeout=6)
        return resp.url
    except Exception:
        return url_redirect


def _clasificar(url_real: str) -> str:
    dominio = urlparse(url_real).netloc.lower().removeprefix("www.")
    if "youtube.com" in dominio or "youtu.be" in dominio:
        return "video"
    if any(d in dominio for d in _DOMINIOS_MANUAL):
        return "manual"
    return "bibliografia"


_ETIQUETA_TIPO = {"video": "Video", "manual": "Manual", "bibliografia": "Bibliografía"}


def buscar_recursos(nombre_materia: str, tema: str) -> list[dict]:
    """Busca en internet (grounding real, no texto libre) recursos para un
    TP de `nombre_materia` sobre `tema`. Devuelve una lista de dicts
    {"tipo": "bibliografia"|"video"|"manual", "titulo": str, "url": str}.
    Puede devolver una lista vacía si el grounding no encontró nada
    confiable. Lanza RuntimeError si falta GEMINI_API_KEY o la búsqueda
    falla — a propósito no cae a otro proveedor de IA."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env — sin Gemini no hay forma de buscar recursos reales.")

    prompt = (
        f"Sos un profesor de una escuela técnica secundaria armando un Trabajo Práctico "
        f"de la materia \"{nombre_materia}\" sobre el tema: \"{tema}\".\n\n"
        "Buscá en internet (no respondas de memoria) y encontrá:\n"
        "1. Una fuente bibliográfica confiable sobre el tema.\n"
        "2. Uno o dos videos de YouTube en español que expliquen el tema con claridad.\n"
        "3. Si el tema es de programación o tiene documentación oficial (ej. un lenguaje "
        "como C++ o Python), un manual o documentación oficial de referencia. Si el tema "
        "no tiene un manual oficial aplicable, omitilo.\n"
    )

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    respuesta = client.models.generate_content(model="gemini-2.5-flash", contents=prompt, config=config)

    from panel_control import memoria  # import perezoso para evitar ciclos de import
    memoria.registrar_uso_proveedor("gemini")

    candidato = respuesta.candidates[0] if respuesta.candidates else None
    metadata = candidato.grounding_metadata if candidato else None
    chunks = metadata.grounding_chunks if metadata and metadata.grounding_chunks else []

    recursos = []
    urls_vistas = set()
    for chunk in chunks:
        if not chunk.web or not chunk.web.uri:
            continue
        url_real = _resolver_url_real(chunk.web.uri)
        if url_real in urls_vistas:
            continue
        urls_vistas.add(url_real)
        tipo = _clasificar(url_real)
        dominio = urlparse(url_real).netloc.lower().removeprefix("www.")
        recursos.append({
            "tipo": tipo,
            "titulo": f"{_ETIQUETA_TIPO[tipo]} — {dominio}",
            "url": url_real,
        })

    return recursos
