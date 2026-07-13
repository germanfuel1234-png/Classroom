#!/usr/bin/env python3
"""Diagnóstico para error 403 en Classroom API"""
import json
from main import obtener_credenciales, build

print("=" * 70)
print("DIAGNÓSTICO: Error 403 en Classroom")
print("=" * 70)

try:
    creds = obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)
    
    # Obtener perfil del usuario autenticado
    print("\n1️⃣ USUARIO AUTENTICADO:")
    try:
        profile = service.userProfiles().get(userId="me").execute()
        print(f"   Email: {profile.get('emailAddress', 'N/A')}")
        print(f"   Nombre: {profile.get('name', {}).get('fullName', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Listar cursos
    print("\n2️⃣ CURSOS DEL PROFESOR:")
    try:
        cursos = service.courses().list(courseStates="ACTIVE").execute()
        if not cursos.get("courses"):
            print("   ❌ No hay cursos activos")
        else:
            for curso in cursos.get("courses", []):
                print(f"   ✅ {curso['name']} (ID: {curso['id']})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Detalles de un curso específico (Sist. Operativos)
    print("\n3️⃣ VERIFICAR PERMISOS EN CADA CURSO:")
    for curso in cursos.get("courses", []):
        if "operativo" in curso['name'].lower() or "sist" in curso['name'].lower():
            print(f"\n   Curso: {curso['name']}")
            course_id = curso['id']
            
            # Listar tareas del curso
            try:
                works = service.courses().courseWork().list(courseId=course_id).execute()
                if works.get("courseWork"):
                    for work in works.get("courseWork")[:2]:  # Solo primeras 2
                        print(f"\n      📋 Tarea: {work['title']}")
                        print(f"         ID: {work['id']}")
                        print(f"         Creador: {work.get('creatorUserId', 'N/A')}")
                        
                        # Intentar listar submissions
                        try:
                            subs = service.courses().courseWork().studentSubmissions().list(
                                courseId=course_id,
                                courseWorkId=work['id'],
                                pageSize=1
                            ).execute()
                            if subs.get("studentSubmissions"):
                                sub = subs["studentSubmissions"][0]
                                print(f"         ✅ Puedo leer entregas")
                                
                                # Intentar hacer un PATCH vacío para probar permisos de escritura
                                try:
                                    service.courses().courseWork().studentSubmissions().patch(
                                        courseId=course_id,
                                        courseWorkId=work['id'],
                                        id=sub['id'],
                                        updateMask="state",  # Campo dummy
                                        body={"state": sub.get("state")}
                                    ).execute()
                                    print(f"         ✅ Puedo escribir entregas")
                                except Exception as e:
                                    print(f"         ❌ NO puedo escribir: {str(e)[:100]}")
                        except Exception as e:
                            print(f"         ⚠️ No puedo listar entregas: {str(e)[:100]}")
                else:
                    print(f"   No hay tareas en este curso")
            except Exception as e:
                print(f"   ❌ Error listando tareas: {e}")

except Exception as e:
    print(f"\n❌ ERROR GENERAL: {e}")

print("\n" + "=" * 70)
