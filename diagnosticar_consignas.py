"""
📋 HERRAMIENTA DE DIAGNÓSTICO Y MEJORA DE CONSIGNAS
Verifica la calidad de las consignas y permite mejorarlas manualmente
"""

import os
import json
from pathlib import Path


def diagnosticar_consignas(ruta_base="Correcciones_Classroom"):
    """
    Escanea todas las consignas y reporte su calidad.
    """
    print("\n" + "="*70)
    print("  📋 DIAGNÓSTICO DE CONSIGNAS")
    print("="*70 + "\n")
    
    consignas = []
    
    for root, dirs, files in os.walk(ruta_base):
        if "CONSIGNA_REFERENCIA.txt" in files or "consigna_referencia.txt" in files:
            # Encontrar archivo (puede ser con mayúscula o minúscula)
            nombre_archivo = "CONSIGNA_REFERENCIA.txt" if "CONSIGNA_REFERENCIA.txt" in files else "consigna_referencia.txt"
            ruta_consigna = os.path.join(root, nombre_archivo)
            
            try:
                with open(ruta_consigna, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                tam_bytes = len(contenido.encode('utf-8'))
                lineas = len(contenido.strip().split('\n'))
                palabras = len(contenido.split())
                
                # Evaluar calidad
                if tam_bytes < 100:
                    calidad = "❌ MUY CORTA (< 100 bytes)"
                    recomendacion = "⚠️  Mejorar manualmente"
                elif tam_bytes < 500:
                    calidad = "⚠️  CORTA (< 500 bytes)"
                    recomendacion = "Considerar mejorar"
                else:
                    calidad = "✅ ADECUADA (> 500 bytes)"
                    recomendacion = "OK"
                
                # Extraer ruta relativa más legible
                ruta_relativa = os.path.relpath(root, ruta_base)
                
                consignas.append({
                    "materia_actividad": ruta_relativa,
                    "ruta": ruta_consigna,
                    "bytes": tam_bytes,
                    "lineas": lineas,
                    "palabras": palabras,
                    "calidad": calidad,
                    "recomendacion": recomendacion
                })
            
            except Exception as e:
                print(f"❌ Error leyendo {root}: {e}")
    
    # Mostrar resumen
    print(f"📊 Total de consignas encontradas: {len(consignas)}\n")
    
    # Agrupar por calidad
    muy_cortas = [c for c in consignas if "MUY CORTA" in c["calidad"]]
    cortas = [c for c in consignas if "CORTA" in c["calidad"] and "MUY" not in c["calidad"]]
    adecuadas = [c for c in consignas if "ADECUADA" in c["calidad"]]
    
    if muy_cortas:
        print(f"❌ MUY CORTAS ({len(muy_cortas)}):")
        for c in muy_cortas:
            print(f"   • {c['materia_actividad']}")
            print(f"     Tamaño: {c['bytes']} bytes | Palabras: {c['palabras']}")
            print(f"     ⚠️  ACCIÓN: Editar manualmente para mejorar\n")
    
    if cortas:
        print(f"⚠️  CORTAS ({len(cortas)}):")
        for c in cortas:
            print(f"   • {c['materia_actividad']}")
            print(f"     Tamaño: {c['bytes']} bytes | Palabras: {c['palabras']}\n")
    
    if adecuadas:
        print(f"✅ ADECUADAS ({len(adecuadas)}):")
        for c in adecuadas:
            print(f"   • {c['materia_actividad']}")
            print(f"     Tamaño: {c['bytes']} bytes | Palabras: {c['palabras']}\n")
    
    # Exportar reporte
    reporte = {
        "total": len(consignas),
        "muy_cortas": len(muy_cortas),
        "cortas": len(cortas),
        "adecuadas": len(adecuadas),
        "consignas": consignas
    }
    
    ruta_reporte = os.path.join(ruta_base, "DIAGNOSTICO_CONSIGNAS.json")
    with open(ruta_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Reporte exportado: {ruta_reporte}\n")
    
    return consignas


def sugerir_mejoras():
    """
    Sugiere cómo mejorar las consignas.
    """
    print("\n" + "="*70)
    print("  💡 CÓMO MEJORAR LAS CONSIGNAS CORTAS")
    print("="*70 + "\n")
    
    print("""
Para mejorar una consigna muy corta:

1️⃣  Abre el archivo CONSIGNA_REFERENCIA.txt en la carpeta de actividad

2️⃣  Reemplaza el contenido incompleto con:
    • Descripción clara de qué se pide
    • Objetivo de la actividad
    • Requisitos específicos (extensión, formato, etc.)
    • Criterios de evaluación
    • Ejemplos si es posible

3️⃣  Ejemplo de buena consigna:

    ╔══════════════════════════════════════════════════════════╗
    ║  ACTIVIDAD: Análisis de Chipset
    ╚══════════════════════════════════════════════════════════╝
    
    Objetivo: Comprender la arquitectura de chipsets en placas madre.
    
    Tareas:
    - Investigar diferencia entre Northbridge y Southbridge
    - Explicar funciones de cada componente
    - Comparar al menos 2 modelos diferentes
    - Crear un diagrama conceptual
    
    Criterios de Evaluación:
    • Profundidad: ≥500 palabras
    • Precisión técnica: definiciones correctas
    • Claridad: explicación comprensible
    • Completitud: responde todas las preguntas

4️⃣  Guarda el archivo y vuelve a ejecutar opción [6]

5️⃣  Las evaluaciones serán mucho más precisas 📈

Nota: Las consignas mejoradas se guardan automáticamente.
      No se sobrescriben en futuras ejecuciones.
""")


if __name__ == "__main__":
    consignas = diagnosticar_consignas()
    
    print("\n¿Deseas ver sugerencias de mejora? (S/N): ", end="")
    resp = input().strip().upper()
    
    if resp == "S":
        sugerir_mejoras()
    
    print("\n✅ Diagnóstico completado.")
