"""
FUNCIONES AUXILIARES PARA CORRECCIÓN MASIVA
Se importan en main.py para mantener la estructura limpia.
Versión con Google Classroom API integration.
"""

import os
import sys
import subprocess


def iniciar_correccion_masiva_con_api_classroom(materias_info):
    """
    Inicia corrección masiva usando Google Classroom API.
    
    Flujo:
    1. Descarga TODAS las entregas de Classroom a carpetas locales
    2. Crea estructura: Correcciones_Classroom/[Materia]/[Actividad]/[Alumno]/
    3. Usa corrector_masivo_integrado.py para corregir desde carpetas locales
    
    Args:
        materias_info: Lista de dicts con credenciales de Classroom
    """
    print("\n" + "=" * 80)
    print(" 🎓 CORRECCIÓN MASIVA - DESCARGA Y EVALUACIÓN ")
    print("=" * 80)
    
    print("\n📊 Flujo de proceso:")
    print("   1️⃣  Descargar TODAS las entregas de Classroom")
    print("   2️⃣  Organizarlas en carpetas locales")
    print("   3️⃣  Evaluar desde carpetas locales")
    print("   4️⃣  Generar Excel con resultados")
    
    print("\n" + "=" * 80)
    input("Presioná ENTER para iniciar...")
    print("=" * 80 + "\n")
    
    try:
        # FASE 1: DESCARGAR ENTREGAS
        print("\n[FASE 1/2] 📥 Descargando entregas de Classroom...\n")
        from descargar_entregas_classroom import descargar_todas_las_entregas
        
        total_alumnos, total_archivos = descargar_todas_las_entregas(
            materias_info,
            ruta_base="Correcciones_Classroom",
            debug=False  # Debug deshabilitado
        )
        
        # FASE 2: CORREGIR USANDO CARPETAS LOCALES
        print("\n[FASE 2/2] 📊 Evaluando entregas descargadas...\n")
        from corrector_masivo_integrado import CorrectorMasivoIntegrado
        
        corrector = CorrectorMasivoIntegrado()
        total_evaluaciones = corrector.ejecutar_correccion_masiva("evaluaciones_completas.xlsx")
        
        print("\n✅ PROCESO COMPLETADO EXITOSAMENTE")
        print(f"   • Entregas descargadas: {total_alumnos} alumnos")
        print(f"   • Archivos procesados: {total_archivos}")
        print(f"   • Evaluaciones realizadas: {total_evaluaciones}")
        print(f"   • Excel generado: evaluaciones_completas.xlsx")
        print(f"   • Ubicación: {os.path.abspath('evaluaciones_completas.xlsx')}")
        
        # Opción para abrir el Excel
        print("\n" + "=" * 80)
        respuesta = input("¿Querés abrir el archivo Excel? (s/n): ").strip().lower()
        
        if respuesta in ("s", "si"):
            try:
                subprocess.Popen(["start", "evaluaciones_completas.xlsx"], shell=True)
                print("✓ Abriendo Excel...")
            except Exception as e:
                print(f"⚠️  No se pudo abrir: {e}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def iniciar_correccion_masiva_completa():
    """
    Versión LEGACY: Usa estructura local de carpetas.
    Esta función se mantiene para compatibilidad.
    """
    print("\n" + "=" * 80)
    print(" 🎓 CORRECCIÓN MASIVA INTEGRADA - TODAS LAS MATERIAS ")
    print("=" * 80)
    
    print("\n📊 Este módulo va a:")
    print("   1. Detectar todas las materias en Correcciones_Classroom/")
    print("   2. Detectar todas las actividades de cada materia")
    print("   3. Evaluar TODOS los estudiantes automáticamente")
    print("   4. Generar UN ÚNICO Excel con 11-12 hojas (una por materia)")
    print("   5. Dentro de cada hoja: todas las actividades y estudiantes")
    print("   6. Asignar notas y feedback pedagógico personalizado")
    
    print("\n" + "=" * 80)
    input("Presioná ENTER para iniciar la corrección masiva...")
    print("=" * 80 + "\n")
    
    try:
        # Método 1: Intentar import directo
        try:
            from corrector_masivo_integrado import CorrectorMasivoIntegrado
            
            corrector = CorrectorMasivoIntegrado()
            total = corrector.ejecutar_correccion_masiva("evaluaciones_completas.xlsx")
            
            print("\n✅ CORRECCIÓN MASIVA COMPLETADA")
            print(f"   • Archivo Excel: evaluaciones_completas.xlsx")
            print(f"   • Total de estudiantes evaluados: {total}")
            print(f"   • Ubicación: {os.path.abspath('evaluaciones_completas.xlsx')}")
            
            # Opción para abrir el Excel
            print("\n" + "=" * 80)
            respuesta = input("¿Querés abrir el archivo Excel? (s/n): ").strip().lower()
            
            if respuesta in ("s", "si"):
                try:
                    subprocess.Popen(["start", "evaluaciones_completas.xlsx"], shell=True)
                    print("✓ Abriendo Excel...")
                except Exception as e:
                    print(f"⚠️ No se pudo abrir el archivo: {e}")
            
            return
        
        except ImportError as e:
            print(f"⚠️ Import directo falló: {e}")
            print("   Intentando método alternativo...\n")
        
        # Método 2: Llamar al script directamente via subprocess
        print("Ejecutando corrector masivo via subprocess...")
        resultado = subprocess.run(
            [sys.executable, "corrector_masivo_integrado.py"],
            cwd=os.getcwd(),
            capture_output=False
        )
        
        if resultado.returncode == 0:
            print("\n✅ CORRECCIÓN MASIVA COMPLETADA")
            
            # Opción para abrir el Excel
            print("\n" + "=" * 80)
            respuesta = input("¿Querés abrir el archivo Excel? (s/n): ").strip().lower()
            
            if respuesta in ("s", "si"):
                try:
                    subprocess.Popen(["start", "evaluaciones_completas.xlsx"], shell=True)
                    print("✓ Abriendo Excel...")
                except Exception as e:
                    print(f"⚠️ No se pudo abrir el archivo: {e}")
        else:
            print(f"❌ Error: El script retornó código {resultado.returncode}")
        
    except Exception as e:
        print(f"❌ ERROR durante la corrección masiva: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    iniciar_correccion_masiva_completa()

