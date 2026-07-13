"""
🔬 DEPURADOR DE EVALUACIONES - Comparar opción [0] vs [6] para Laureano
"""

import json
import os
from pathlib import Path


def comparar_evaluaciones():
    """
    Busca evaluaciones de Laureano Ianigro en reportes y las compara.
    """
    print("\n" + "="*70)
    print("  🔬 COMPARANDO EVALUACIONES DE LAUREANO IANIGRO")
    print("="*70 + "\n")
    
    # Opción [0] reportes - buscar evaluación manual
    print("📊 Opción [0] - Corrector Pedagógico:")
    print("-" * 70)
    
    reportes_0 = "reportes"  # Carpeta de opción [0]
    if os.path.exists(reportes_0):
        encontrado_0 = False
        for root, dirs, files in os.walk(reportes_0):
            for file in files:
                if "Laureano" in file and file.endswith(".json"):
                    ruta = os.path.join(root, file)
                    try:
                        with open(ruta, 'r', encoding='utf-8') as f:
                            datos = json.load(f)
                        
                        print(f"✅ Encontrado: {file}")
                        print(f"   Nota: {datos.get('nota', '?')}/10")
                        print(f"   Estado: {datos.get('estado', '?')}")
                        print(f"   Motivo: {datos.get('motivo', '?')[:60]}...")
                        encontrado_0 = True
                    except:
                        pass
        
        if not encontrado_0:
            print("❌ No encontrad evaluación de Laureano en reportes opción [0]")
    else:
        print("❌ No existe carpeta 'reportes'")
    
    # Opción [6] - buscar en Correcciones_Classroom
    print("\n📊 Opción [6] - Descarga y Evaluación Consistente:")
    print("-" * 70)
    
    base_path = "Correcciones_Classroom"
    encontrado_6 = False
    
    for root, dirs, files in os.walk(base_path):
        if "evaluacion.json" in files and "Laureano" in root:
            ruta = os.path.join(root, "evaluacion.json")
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                # Extraer información del path
                partes = Path(root).parts
                actividad = partes[-2] if len(partes) > 1 else "?"
                materia_idx = partes.index(base_path) + 1 if base_path in partes else 0
                materia = partes[materia_idx] if materia_idx < len(partes) else "?"
                
                print(f"✅ Encontrado: {materia} / {actividad}")
                print(f"   Ruta: {root}")
                print(f"   Nota: {datos.get('nota', '?')}/10")
                print(f"   Estado: {datos.get('estado', '?')}")
                print(f"   Motivo: {datos.get('motivo', '?')[:60]}...")
                print()
                encontrado_6 = True
            except Exception as e:
                print(f"❌ Error leyendo {ruta}: {e}")
    
    if not encontrado_6:
        print("❌ No encontradas evaluaciones de Laureano en opción [6]")
    
    # Análisis
    print("\n" + "="*70)
    print("  📈 ANÁLISIS")
    print("="*70)
    print("""
Si las notas son DIFERENTES entre [0] y [6]:
  → El motor NO es idéntico entre ambas opciones
  → Hay un problema en cómo se pasan parámetros o se procesa información

Si las notas son IGUALES:
  → El motor SÍ es consistente
  → El problema está en otro lado (consignas, parámetros de entrada)
    
Próximo paso: Verificar archivo de consigna usado en cada evaluación
""")


if __name__ == "__main__":
    comparar_evaluaciones()
