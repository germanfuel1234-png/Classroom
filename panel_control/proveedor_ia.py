"""Abstracción de proveedor de IA para los agentes.

Soporta un modelo LOCAL (Ollama, sin costo ni límite de cuota), DeepSeek
(pago por uso), Gemini (con cuota gratis limitada), Groq (free tier
gratis y generoso, corre modelos Llama grandes a máxima velocidad),
OpenRouter (router con varios modelos gratis, entre ellos Kimi K2),
NVIDIA NIM (free tier propio, 100+ modelos open-weight), Mistral (plan
Experiment gratis, límites bajos) y Cline (cuenta personal, modelo fijo
marcado "Free" en su catálogo — otro balde de cuota gratis, aparte de
todos los anteriores), con fallback automático: si uno falla (sin API
key, sin cuota, servidor caído), prueba con el siguiente. Así los
agentes no dependen de un solo proveedor.

Orden por defecto: DeepSeek y Gemini primero (mejor calidad de
redacción), Groq/OpenRouter/NVIDIA como respaldos gratis con buena
cuota, Mistral y Cline después (cuota más chica/menos probados), y el
local al final como última red de emergencia — si se agota la cuota de
todos o no hay internet, sigue funcionando igual, aunque la redacción
sea más floja (es un modelo chico, 3B, para que ande bien en esta
compu).
Se puede cambiar con la variable de entorno
IA_PROVEEDOR_ORDEN="local,gemini,deepseek,groq,openrouter,nvidia,mistral,cline".
"""
import os
import time

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

ORDEN_POR_DEFECTO = ["deepseek", "gemini", "groq", "openrouter", "nvidia", "mistral", "cline", "local"]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", "llama3.2:3b")

_INDICADORES_TRANSITORIOS = ("503", "429", "unavailable", "rate limit", "timeout", "temporarily", "connection reset")


def _es_transitorio(error) -> bool:
    """Errores de saturación/red que ameritan reintento (a diferencia de, por
    ejemplo, 'sin saldo' o una API key inválida, que no se arreglan solos)."""
    texto = str(error).lower()
    if "perday" in texto or "free_tier" in texto or "free tier" in texto:
        return False  # cuota diaria agotada: reintentar en unos segundos no sirve de nada
    return any(x in texto for x in _INDICADORES_TRANSITORIOS)


def _con_reintentos(fn, etiqueta, intentos=3):
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            return fn()
        except Exception as e:
            ultimo_error = e
            if not _es_transitorio(e) or intento == intentos:
                raise
            espera = min(3 * intento, 10)
            print(f"      ⚠️ {etiqueta}: fallo transitorio, reintentando en {espera}s... [{intento}/{intentos}]")
            time.sleep(espera)
    raise ultimo_error


def _generar_local(prompt, modelo=None):
    """Ollama corriendo en esta misma máquina. No hace falta API key: si el
    servidor no está levantado, esto falla rápido y cae al siguiente
    proveedor (DeepSeek/Gemini)."""
    client = OpenAI(api_key="ollama", base_url=OLLAMA_URL)
    respuesta = client.chat.completions.create(
        model=modelo or OLLAMA_MODELO,
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_deepseek(prompt, modelo="deepseek-chat"):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Falta DEEPSEEK_API_KEY en el .env")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    respuesta = client.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_gemini(prompt, modelo="gemini-2.5-flash"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")
    client = genai.Client(api_key=api_key)
    respuesta = client.models.generate_content(model=modelo, contents=prompt)
    return respuesta.text


def _generar_groq(prompt, modelo=None):
    """Groq: free tier propio (nada que ver con la cuota de Gemini), API
    compatible con OpenAI. Conseguí una key gratis en https://console.groq.com/keys
    y ponela en .env como GROQ_API_KEY."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY en el .env")
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    respuesta = client.chat.completions.create(
        model=modelo or os.environ.get("GROQ_MODELO", "llama-3.3-70b-versatile"),
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_openrouter(prompt, modelo=None):
    """OpenRouter: router con varios modelos gratis bajo una sola key (entre
    ellos Kimi K2 de Moonshot AI). Es un balde de cuota gratis DISTINTO al
    de Groq y Gemini — no comparten límite entre sí. Conseguí una key
    gratis en https://openrouter.ai/keys y ponela en .env como
    OPENROUTER_API_KEY. Modelo por defecto: moonshotai/kimi-k2:free."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENROUTER_API_KEY en el .env")
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    respuesta = client.chat.completions.create(
        model=modelo or os.environ.get("OPENROUTER_MODELO", "moonshotai/kimi-k2:free"),
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_nvidia(prompt, modelo=None):
    """NVIDIA NIM (build.nvidia.com), free tier propio (créditos mensuales,
    ~40 pedidos/min), 100+ modelos open-weight (Llama, DeepSeek-R1, etc.).
    Conseguí una key gratis en https://build.nvidia.com y ponela en .env
    como NVIDIA_API_KEY."""
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("Falta NVIDIA_API_KEY en el .env")
    client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")
    respuesta = client.chat.completions.create(
        model=modelo or os.environ.get("NVIDIA_MODELO", "nvidia/nemotron-3-super-120b-a12b"),
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_mistral(prompt, modelo=None):
    """Mistral (La Plateforme), plan Experiment gratis — límites de cuota
    bajos (pensado para probar, no para producción), por eso va después de
    Groq/OpenRouter en el orden por defecto. Conseguí una key gratis en
    https://console.mistral.ai (requiere verificar teléfono) y ponela en
    .env como MISTRAL_API_KEY."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("Falta MISTRAL_API_KEY en el .env")
    client = OpenAI(api_key=api_key, base_url="https://api.mistral.ai/v1")
    respuesta = client.chat.completions.create(
        model=modelo or os.environ.get("MISTRAL_MODELO", "mistral-small-latest"),
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.choices[0].message.content


def _generar_cline(prompt, modelo=None):
    """Cline (cuenta personal vía app.cline.bot). Su API NO es compatible
    con el cliente openai (envuelve la respuesta en {"data": {...}} en vez
    de la forma plana esperada), así que acá se llama directo por HTTP.

    Fijo el modelo a uno de su catálogo con sufijo ":free" (gratis siempre,
    para cualquier cuenta, a diferencia de los modelos marcados "Free" en
    el selector de VS Code — esos SOLO andan desde la extensión/IDE, no
    por esta API; lo confirmé probándolo: devuelven 403 "only available
    via Cline product surfaces"). Esta cuenta no tiene tarjeta cargada,
    pero si algún día se le agregara, un modelo sin ":free" acá consumiría
    el saldo de créditos.
    Conseguí la key en https://app.cline.bot/dashboard y ponela en .env
    como CLINE_API_KEY."""
    api_key = os.environ.get("CLINE_API_KEY")
    if not api_key:
        raise RuntimeError("Falta CLINE_API_KEY en el .env")
    import requests
    resp = requests.post(
        "https://api.cline.bot/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": modelo or os.environ.get("CLINE_MODELO", "google/gemma-4-26b-a4b-it:free"),
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Cline devolvió {resp.status_code}: {resp.text[:300]}")
    return resp.json()["data"]["choices"][0]["message"]["content"]


_PROVEEDORES = {
    "local": _generar_local,
    "deepseek": _generar_deepseek,
    "gemini": _generar_gemini,
    "groq": _generar_groq,
    "openrouter": _generar_openrouter,
    "nvidia": _generar_nvidia,
    "mistral": _generar_mistral,
    "cline": _generar_cline,
}


def generar_texto(prompt, orden=None):
    """Prueba los proveedores en orden hasta que uno responda.

    Devuelve (texto, proveedor_usado). Lanza RuntimeError si todos fallan.
    """
    from panel_control import memoria  # import perezoso para evitar ciclos de import

    if orden is None:
        orden = os.environ.get("IA_PROVEEDOR_ORDEN", ",".join(ORDEN_POR_DEFECTO)).split(",")

    errores = []
    for nombre in orden:
        nombre = nombre.strip().lower()
        fn = _PROVEEDORES.get(nombre)
        if not fn:
            continue
        try:
            texto = _con_reintentos(lambda: fn(prompt), etiqueta=nombre)
            memoria.registrar_uso_proveedor(nombre)
            return texto, nombre
        except Exception as e:
            errores.append(f"{nombre}: {e}")

    raise RuntimeError("Todos los proveedores de IA fallaron:\n" + "\n".join(errores))
