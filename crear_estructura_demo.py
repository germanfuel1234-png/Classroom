"""
SCRIPT DE CREACIÓN DE ESTRUCTURA DE DEMOSTRACIÓN
Crea la estructura de carpetas para las 12 materias mencionadas
y genera archivos de prueba.
"""

import os
import json
from datetime import datetime

def crear_estructura_demo():
    """Crea la estructura completa de carpetas para demostración."""
    
    print("\n" + "="*80)
    print(" CREADOR DE ESTRUCTURA DE CARPETAS - DEMOSTRACIÓN")
    print("="*80 + "\n")
    
    # Las 12 materias del usuario
    materias = [
        "probando",
        "Sistemas Digitales 5to",
        "Inst. Mant. De Redes Inf.",
        "Sist. Operativos",
        "Sistemas Digitales",
        "Procesos Industriales",
        "Desarrollo de aplicaciones web (dinamicas)",
        "Lab Hardware",
        "DES. SOFT. PLAT. MOVILES",
        "Lab. Aplicaciones 2026 4to",
        "Lab. Programacion 4to 2026",
        "Lab. Programacion 2026"
    ]
    
    base = "Correcciones_Classroom"
    
    # Crear estructura básica
    print("[Creando estructura de carpetas...]")
    
    for i, materia in enumerate(materias, 1):
        ruta_materia = os.path.join(base, materia)
        os.makedirs(ruta_materia, exist_ok=True)
        
        # Crear 2 actividades por materia de ejemplo
        for j in range(1, 3):
            actividad = f"Actividad {j}"
            ruta_actividad = os.path.join(ruta_materia, actividad)
            os.makedirs(ruta_actividad, exist_ok=True)
            
            # Crear consigna de ejemplo
            consigna_path = os.path.join(ruta_actividad, "consigna_referencia.txt")
            if not os.path.exists(consigna_path):
                consigna = f"""CONSIGNA - {materia} - {actividad}

Objetivo:
Completar la actividad propuesta en clase.

Requisitos:
1. Realizar un análisis completo del tema
2. Justificar tu respuesta
3. Presentar de forma clara y ordenada

Recursos:
- Apuntes de clase
- Material de referencia en Drive

Plazo de entrega: {datetime.now().strftime("%d/%m/%Y")}

Evaluación:
- Completitud: 40%
- Claridad: 30%
- Fundamentación: 30%
"""
                with open(consigna_path, 'w', encoding='utf-8') as f:
                    f.write(consigna)
            
            # Crear carpetas de 2 estudiantes de ejemplo por actividad
            estudiantes = [f"Estudiante {k}" for k in range(1, 3)]
            
            for estudiante in estudiantes:
                ruta_estudiante = os.path.join(ruta_actividad, estudiante)
                os.makedirs(ruta_estudiante, exist_ok=True)
                
                # Crear entrega de ejemplo si no existe
                ruta_entrega = os.path.join(ruta_estudiante, f"entrega_{estudiante}.docx")
                
                # Para la demostración, crear un archivo de texto simulado
                # (en producción sería un .docx real)
                if not os.path.exists(ruta_entrega):
                    # Crear un archivo .docx simulado (en realidad es ZIP, pero para demo funciona)
                    entrega_simulada = f"""ENTREGA - {estudiante}

{materia} - {actividad}

Respuesta del estudiante:
Este es un archivo de prueba para demostrar el funcionamiento del sistema.

En producción, aquí iría la entrega real del estudiante en formato Word.

Conclusión:
Se completó la actividad según los requisitos especificados en la consigna.
"""
                    with open(ruta_entrega.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
                        f.write(entrega_simulada)
        
        print(f"[{i:2d}/{len(materias)}] ✓ {materia}")
    
    print(f"\n{'='*80}")
    print(f"✅ ESTRUCTURA CREADA EXITOSAMENTE")
    print(f"{'='*80}")
    print(f"\nTotal de carpetas creadas:")
    print(f"  • Materias: {len(materias)}")
    print(f"  • Actividades: {len(materias) * 2} (2 por materia)")
    print(f"  • Estudiantes: {len(materias) * 2 * 2} (2 por actividad)")
    print(f"\nUbicación base: {os.path.abspath(base)}")
    
    print("\n" + "="*80)
    print("📋 PRÓXIMO PASO:")
    print("="*80)
    print("\n1. Ve a main.py y selecciona opción [4]: Corrección Masiva")
    print("2. El sistema detectará automáticamente todas las materias y actividades")
    print("3. Generará un Excel con 12 hojas (una por materia)")
    print("4. Dentro de cada hoja, verás todas las actividades y estudiantes")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    crear_estructura_demo()
