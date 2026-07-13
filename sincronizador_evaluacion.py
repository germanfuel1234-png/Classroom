"""
🔄 SINCRONIZADOR DE EVALUACIÓN CONSISTENTE
Asegurar que opción [6] use EXACTAMENTE el mismo motor y lógica que opción [0]
"""

import json
import os


def diagnosticar_diferencias():
    """
    Compara la lógica entre opción [0] y opción [6] para encontrar inconsistencias.
    """
    print("\n" + "="*70)
    print("  🔍 DIAGNÓSTICO DE DIFERENCIAS ENTRE OPCIÓN [0] Y [6]")
    print("="*70 + "\n")
    
    # Leer main.py para encontrar las funciones de ambas opciones
    try:
        with open("main.py", 'r', encoding='utf-8') as f:
            main_content = f.read()
    except:
        print("❌ No se pudo leer main.py")
        return
    
    # Buscar referencias a opción [0] y [6]
    print("📊 Análisis de funciones:")
    print("-" * 70)
    
    # Opción [0]
    if "evaluar_entrega_automatica" in main_content:
        print("✅ Opción [0] usa: evaluar_entrega_automatica()")
    
    # Opción [6]
    if "DescargadorYEvaluadorConsistente" in main_content:
        print("✅ Opción [6] usa: DescargadorYEvaluadorConsistente (en archivo externo)")
    
    print("\n" + "-"*70)
    print("⚠️  POTENCIAL PROBLEMA:")
    print("   Opción [0] → Motor local en main.py")
    print("   Opción [6] → Motor importado de descarga_y_eval_consistente.py")
    print("   → Podrían tener lógicas ligeramente diferentes")
    
    print("\n" + "="*70)
    print("💡 RECOMENDACIÓN:")
    print("="*70)
    print("""
Opción 1 (Rápida - No recomendada):
  Editar CONSIGNA_REFERENCIA.txt manualmente en cada carpeta
  - Copiar consigna exitosa de "Lab Hardware/actividad diagnostico/Laureano Ianigro"
  - Pegar en "Lab Hardware/Actividad 5.1(Chipset Norte Sur)"
  
Opción 2 (Recomendada - Fundamental):
  Hacer que opción [6] use EXACTAMENTE el motor de opción [0]
  - Refactorizar descarga_y_eval_consistente.py
  - Importar evaluar_entrega_automatica() directamente
  - Asegurar que ambas opciones usan la MISMA lógica

Opción 3 (Mejor solución a largo plazo):
  Unificar en UN SOLO motor compartido
  - Crear motor_evaluacion_unico.py
  - Tanto [0] como [6] lo importan
  - Garantiza consistencia permanente
""")


def extraer_consignas_exitosas():
    """
    Busca consignas que ya generaron buenas evaluaciones.
    """
    print("\n" + "="*70)
    print("  📚 EXTRAYENDO CONSIGNAS EXITOSAS")
    print("="*70 + "\n")
    
    # Ubicación conocida de consigna que funcionó
    consigna_exitosa = "Correcciones_Classroom/Lab Hardware/actividad diagnostico/Laureano Ianigro/CONSIGNA_REFERENCIA.txt"
    
    if os.path.exists(consigna_exitosa):
        print(f"✅ Encontrada consigna exitosa:")
        print(f"   {consigna_exitosa}\n")
        
        with open(consigna_exitosa, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        print(f"📏 Tamaño: {len(contenido)} bytes")
        print(f"\n📄 Primeras líneas:\n")
        print(contenido[:300] + "...\n")
        
        # Proponer copiar a otras ubicaciones
        destinos = [
            "Correcciones_Classroom/Lab Hardware/Actividad 5.1(Chipset Norte Sur)/consigna_referencia.txt",
            "Correcciones_Classroom/Lab Hardware/Actividad 5.1(Chipset Norte Sur)/CONSIGNA_REFERENCIA.txt"
        ]
        
        print("💡 Esta consigna funcionó correctamente (10/10)")
        print("   ¿Quieres copiarla a otras actividades? (S/N): ", end="")
        resp = input().strip().upper()
        
        if resp == "S":
            for destino in destinos:
                try:
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    with open(destino, 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    print(f"✅ Copiado: {destino}")
                except Exception as e:
                    print(f"❌ Error: {destino} - {e}")
    else:
        print(f"❌ No encontrada consigna exitosa en: {consigna_exitosa}")


if __name__ == "__main__":
    diagnosticar_diferencias()
    print("\n")
    extraer_consignas_exitosas()
    print("\n✅ Diagnóstico completado.")
