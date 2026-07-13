"""
SCRIPT DE DIAGNÓSTICO: Inspecciona estructura real de studentSubmissions de Classroom API
Ayuda a entender dónde están los attachments y por qué no se descargan
"""

import sys
import json

def diagnosticar_estructura_submissions(service, course_id, work_id, max_alumnos=2):
    """
    Obtiene la estructura real de studentSubmissions y la imprime para análisis.
    """
    print("\n" + "=" * 80)
    print(" 🔍 DIAGNÓSTICO: Estructura de studentSubmissions ")
    print("=" * 80)
    
    try:
        # Obtener submissions
        alumnos_result = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=work_id,
            states=['TURNED_IN', 'CREATED', 'RETURNED']
        ).execute()
        
        alumnos = alumnos_result.get("studentSubmissions", [])
        
        if not alumnos:
            print("❌ No hay submissions para esta actividad")
            return
        
        print(f"\n✅ Se encontraron {len(alumnos)} submissions")
        print(f"Analizando primeros {min(max_alumnos, len(alumnos))} alumnos...\n")
        
        for i, alumno_submission in enumerate(alumnos[:max_alumnos], 1):
            print(f"\n{'─' * 80}")
            print(f"[Alumno {i}]")
            print(f"{'─' * 80}")
            
            # Estructura principal
            print(f"\n📋 Keys principales de la submission:")
            for key in sorted(alumno_submission.keys()):
                valor = alumno_submission.get(key)
                if isinstance(valor, (str, int, bool, type(None))):
                    print(f"   • {key}: {valor}")
                elif isinstance(valor, list):
                    print(f"   • {key}: [list con {len(valor)} items]")
                    if valor and isinstance(valor[0], dict):
                        print(f"      └─ Primero item tiene keys: {list(valor[0].keys())}")
                elif isinstance(valor, dict):
                    print(f"   • {key}: {{dict con keys: {list(valor.keys())}}}")
            
            # Análisis profundo de submissionHistory
            if "submissionHistory" in alumno_submission:
                submission_history = alumno_submission.get("submissionHistory", [])
                print(f"\n📚 submissionHistory:")
                print(f"   • Cantidad de items: {len(submission_history)}")
                
                for j, history_item in enumerate(submission_history):
                    print(f"\n   [History item {j}]")
                    print(f"   Keys: {list(history_item.keys())}")
                    
                    if "submission" in history_item:
                        submission = history_item.get("submission", {})
                        print(f"   ├─ submission keys: {list(submission.keys())}")
                        if "attachments" in submission:
                            attachments = submission.get("attachments", [])
                            print(f"   │  └─ attachments: {len(attachments)} items")
                            if attachments:
                                for k, att in enumerate(attachments[:2]):
                                    print(f"   │      └─ [{k}] keys: {list(att.keys())}")
            
            # Análisis de attachments directos
            if "attachments" in alumno_submission:
                attachments = alumno_submission.get("attachments", [])
                print(f"\n📎 attachments (directo):")
                print(f"   • Cantidad: {len(attachments)} items")
                if attachments:
                    for k, att in enumerate(attachments[:2]):
                        print(f"   [{k}] {att}")
            
            # Guardar JSON completo para análisis
            archivo_debug = f"submission_alumno_{i}_debug.json"
            with open(archivo_debug, 'w', encoding='utf-8') as f:
                # Simplificar para que sea legible
                submission_simple = {}
                for key in alumno_submission.keys():
                    valor = alumno_submission.get(key)
                    if isinstance(valor, (str, int, bool, type(None))):
                        submission_simple[key] = valor
                    elif isinstance(valor, list) and len(str(valor)) < 500:
                        submission_simple[key] = valor
                
                json.dump(submission_simple, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 JSON completo guardado en: {archivo_debug}")
        
        print(f"\n{'=' * 80}")
        print("✅ Diagnóstico completado")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"❌ Error durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Este script debe ser llamado desde main.py con las credenciales de Classroom")
