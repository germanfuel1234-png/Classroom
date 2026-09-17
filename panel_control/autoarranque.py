"""Arranque automático del dashboard como servicio systemd de usuario.

No hace falta sudo: todo esto vive en systemd --user (bajo el usuario que
ya está corriendo el panel), no en /etc/systemd/system. La única acción que
podría pedir privilegios en algunas distros es "loginctl enable-linger"
(para que el servicio arranque también sin sesión gráfica abierta) — si
falla, se avisa igual pero el resto queda funcionando.

No mata ni reinicia la instancia que el profesor ya tiene corriendo a mano:
solo deja el servicio "instalado y habilitado" para la próxima vez que
prenda la compu o cierre sesión. Es intencional — evitar que un click en
el dashboard se corte a sí mismo a mitad de la respuesta HTTP.
"""
import os
import subprocess

RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOMBRE_SERVICIO = "classroom-dashboard.service"
RUTA_SERVICIO = os.path.expanduser(f"~/.config/systemd/user/{NOMBRE_SERVICIO}")

CONTENIDO_SERVICIO = f"""[Unit]
Description=Panel de Agentes - Classroom (German Rodriguez)
After=network-online.target

[Service]
WorkingDirectory={RAIZ_PROYECTO}
ExecStart={RAIZ_PROYECTO}/.venv/bin/streamlit run panel_control/dashboard.py --server.port 8600 --server.headless true --server.address localhost
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""


def esta_activado() -> bool:
    if not os.path.exists(RUTA_SERVICIO):
        return False
    resultado = subprocess.run(
        ["systemctl", "--user", "is-enabled", NOMBRE_SERVICIO],
        capture_output=True, text=True,
    )
    return resultado.stdout.strip() == "enabled"


def activar_arranque_automatico():
    """Escribe el .service, recarga systemd y lo habilita (no lo inicia
    ahora — la instancia manual actual sigue corriendo igual). Devuelve
    (ok, mensaje)."""
    try:
        os.makedirs(os.path.dirname(RUTA_SERVICIO), exist_ok=True)
        with open(RUTA_SERVICIO, "w") as f:
            f.write(CONTENIDO_SERVICIO)

        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True, text=True)
        subprocess.run(["systemctl", "--user", "enable", NOMBRE_SERVICIO], check=True, capture_output=True, text=True)

        aviso_linger = ""
        linger = subprocess.run(["loginctl", "enable-linger", os.environ.get("USER", "")], capture_output=True, text=True)
        if linger.returncode != 0:
            aviso_linger = (
                " (no se pudo activar 'linger' automáticamente — sin eso, el servicio arranca solo al "
                "iniciar sesión, no antes; si querés que ande incluso sin loguearte, pedile a alguien con "
                "sudo que corra: sudo loginctl enable-linger " + os.environ.get("USER", "") + ")"
            )

        return True, (
            "Listo. Quedó preparado para arrancar solo la próxima vez que prendas la compu o cierres "
            "sesión y vuelvas a entrar — esta instancia que estás usando ahora sigue corriendo igual, "
            "no se reinició nada." + aviso_linger
        )
    except subprocess.CalledProcessError as e:
        return False, f"No se pudo activar: {e.stderr or e.stdout}"
    except Exception as e:
        return False, f"No se pudo activar: {e}"


def desactivar_arranque_automatico():
    try:
        subprocess.run(["systemctl", "--user", "disable", NOMBRE_SERVICIO], capture_output=True, text=True)
        return True, "Arranque automático desactivado. La instancia actual sigue corriendo igual."
    except Exception as e:
        return False, f"No se pudo desactivar: {e}"
