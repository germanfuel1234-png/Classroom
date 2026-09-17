"""Corrido por cron una vez por día (ver panel_control/scripts/sync_automatico.sh
y `crontab -l`): si hoy es una fecha patria, deja UN borrador esperando en
Aprobaciones — nunca publica nada solo.

Uso: python -m panel_control.scripts.revisar_fechas_patrias
"""
from panel_control import agente_fechas_patrias, memoria


def main():
    memoria.init_db()
    aprobacion_id = agente_fechas_patrias.revisar_y_encolar()
    if aprobacion_id:
        print(f"Hoy es fecha patria — borrador #{aprobacion_id} listo en Aprobaciones.")
    else:
        print("Hoy no es fecha patria (o ya se había generado el borrador de hoy).")


if __name__ == "__main__":
    main()
