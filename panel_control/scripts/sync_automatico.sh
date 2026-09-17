#!/bin/bash
# Corrido por cron una vez por día (ver `crontab -l`) para que el dashboard
# tenga alumnos/materias/actividades siempre frescos sin que el profesor
# tenga que apretar "Traer de Classroom" a mano. Es todo lectura (nunca
# escribe nada en Classroom), así que no hace falta aprobación humana para
# automatizarlo. Confirmado con el profesor: una vez por día, a la madrugada.
cd "/home/german/Escritorio/Classroom" || exit 1
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> /tmp/sync_automatico.log
.venv/bin/python -m panel_control.sync_materias >> /tmp/sync_automatico.log 2>&1
.venv/bin/python -m panel_control.scripts.sincronizar_actividades >> /tmp/sync_automatico.log 2>&1
