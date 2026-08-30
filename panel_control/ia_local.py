"""Prender/apagar el servidor de IA local (Ollama) desde el panel, sin
necesitar sudo ni la terminal. Ollama se instaló en la carpeta del usuario
(~/.local/ollama), así que se controla como un proceso normal.
"""
import os
import subprocess
import time

import requests

OLLAMA_HOME = os.path.expanduser("~/.local/ollama")
OLLAMA_BIN = os.path.join(OLLAMA_HOME, "bin", "ollama")
OLLAMA_MODELS_DIR = os.path.join(OLLAMA_HOME, "models")
OLLAMA_URL = "http://localhost:11434"


def esta_corriendo() -> bool:
    try:
        r = requests.get(OLLAMA_URL, timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def prender(timeout_seg: int = 15) -> bool:
    """Arranca Ollama en segundo plano. Devuelve True si quedó levantado."""
    if esta_corriendo():
        return True
    if not os.path.exists(OLLAMA_BIN):
        raise FileNotFoundError(f"No encontré el binario de Ollama en {OLLAMA_BIN}")

    env = os.environ.copy()
    env["OLLAMA_MODELS"] = OLLAMA_MODELS_DIR
    subprocess.Popen(
        [OLLAMA_BIN, "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    esperado = 0.0
    paso = 0.5
    while esperado < timeout_seg:
        time.sleep(paso)
        esperado += paso
        if esta_corriendo():
            return True
    return False


def apagar(timeout_seg: int = 8) -> bool:
    """Para el proceso de Ollama. Devuelve True si quedó apagado."""
    subprocess.run(["pkill", "-f", f"{OLLAMA_BIN} serve"], check=False)
    esperado = 0.0
    paso = 0.3
    while esperado < timeout_seg:
        time.sleep(paso)
        esperado += paso
        if not esta_corriendo():
            return True
    return False
