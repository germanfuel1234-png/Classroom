"""
╔═══════════════════════════════════════════════════════════════════╗
║  DESCARGA Y EVALUACIÓN CONSISTENTE POR ALUMNO                    ║
║  ✅ Motor único de evaluación (evaluar_entrega_automatica)       ║
║  ✅ Estructura: Materia/Actividad/NombreAlumno/                  ║
║  ✅ Reportes JSON + Excel consistentes                           ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


class DescargadorYEvaluadorConsistente:
    """
    Descarga entregas de Classroom y las evalúa con un motor único.
    Estructura: Correcciones_Classroom/Materia/Actividad/NombreAlumno/
    """
    
    def __init__(self, ruta_base="Correcciones_Classroom"):
        self.ruta_base = ruta_base
        self.evaluaciones = []
        self.estadisticas = {
            "total_alumnos": 0,
            "evaluaciones_exitosas": 0,
            "sin_entrega": 0,
            "errores": 0,
            "por_materia": {}
        }
    
    def descargar_y_evaluar_todo(self, service, service_drive, course_id):
        """
        Descarga TODAS las actividades de un curso y las evalúa con motor único.
        """
        # Importaciones lazy para evitar circular imports
        from main import (
            listar_trabajos_del_curso,
            listar_alumnos_por_actividad,
            evaluar_entrega_automatica,
            obtener_contexto_consigna,
            descargar_adjunto_drive,
            _obtener_drive_file_desde_attachment,
            _limpiar_nombre_ruta
        )
        
        print(f"\n{'='*70}")
        print("  🚀 DESCARGA Y EVALUACIÓN CONSISTENTE POR ALUMNO")
        print(f"{'='*70}\n")
        
        # Obtener materia
        try:
            materia = service.courses().get(courseId=course_id).execute()
            materia_nombre = materia.get("name", "Sin nombre")
        except:
            materia_nombre = f"Materia_{course_id}"
        
        print(f"📚 MATERIA: {materia_nombre}")
        print(f"{'─'*70}\n")
        
        # Crear carpeta base de materia
        carpeta_materia = os.path.join(self.ruta_base, _limpiar_nombre_ruta(materia_nombre))
        os.makedirs(carpeta_materia, exist_ok=True)
        
        # Listar todas las actividades
        print("   ⏳ Obteniendo actividades...")
        try:
            trabajos = listar_trabajos_del_curso(service, course_id)
        except:
            print("❌ Error al obtener actividades")
            return {"materia": materia_nombre, "actividades": []}
        
        actividades_procesadas = []
        
        for idx, trabajo in enumerate(trabajos, 1):
            work_id = trabajo.get("id")
            titulo_trabajo = trabajo.get("title", "Sin título")
            
            print(f"[{idx}/{len(trabajos)}] 📝 ACTIVIDAD: {titulo_trabajo}")
            print(f"{'─'*70}")
            
            # Crear carpeta para esta actividad
            carpeta_actividad = os.path.join(
                carpeta_materia, 
                _limpiar_nombre_ruta(titulo_trabajo)
            )
            os.makedirs(carpeta_actividad, exist_ok=True)
            
            # Obtener contexto de consigna
            print("   ⏳ Obteniendo consigna...")
            try:
                contexto_consigna = obtener_contexto_consigna(
                    service, service_drive, course_id, work_id, trabajo
                )
            except Exception as e:
                contexto_consigna = titulo_trabajo
                print(f"   ⚠️  No se pudo extraer consigna completa: {str(e)[:80]}")
            
            # Guardar consigna en archivo de referencia
            ruta_consigna = os.path.join(carpeta_actividad, "CONSIGNA_REFERENCIA.txt")
            
            # SI EXISTE ARCHIVO PREVIO, USARLO (prioridad a consignas mejoradas manualmente)
            if os.path.exists(ruta_consigna):
                try:
                    with open(ruta_consigna, 'r', encoding='utf-8') as f:
                        contexto_consigna = f.read()
                    print(f"   ✅ Consigna existente utilizada (mejorada manualmente)")
                except:
                    pass
            else:
                # CREAR CONSIGNA INICIAL
                try:
                    with open(ruta_consigna, 'w', encoding='utf-8') as f:
                        f.write(f"╔══════════════════════════════════════════════╗\n")
                        f.write(f"║  CONSIGNA DE REFERENCIA PARA EVALUACIÓN     ║\n")
                        f.write(f"╚══════════════════════════════════════════════╝\n\n")
                        f.write(f"MATERIA: {materia_nombre}\n")
                        f.write(f"ACTIVIDAD: {titulo_trabajo}\n")
                        f.write(f"FECHA DESCARGA: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"\n{'='*70}\n\n")
                        f.write(f"[CONTENIDO EXTRAÍDO AUTOMÁTICAMENTE DE CLASSROOM]\n\n")
                        f.write(contexto_consigna)
                        f.write(f"\n\n{'='*70}\n")
                        f.write(f"⚠️  NOTA: Si la consigna anterior está incompleta o solo contiene URLs,\n")
                        f.write(f"   edita este archivo manualmente para mejorar la descripción.\n")
                        f.write(f"   Esto mejorará la consistencia de las evaluaciones automáticas.\n")
                    print(f"   ✅ Consigna inicial guardada")
                except Exception as e:
                    print(f"   ⚠️  Error guardando consigna: {e}")
            
            # Listar alumnos y descargar entregas
            print(f"   ⏳ Obteniendo alumnos...")
            try:
                alumnos = listar_alumnos_por_actividad(service, course_id, work_id)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                alumnos = []
            
            resultado_actividad = self._procesar_alumnos_actividad(
                alumnos, 
                carpeta_actividad,
                service_drive,
                contexto_consigna,
                titulo_trabajo,
                materia_nombre
            )
            
            actividades_procesadas.append(resultado_actividad)
            print()
        
        # Generar reportes finales
        self._generar_reportes(carpeta_materia, materia_nombre)
        
        return {
            "materia": materia_nombre,
            "actividades": actividades_procesadas,
            "estadisticas": self.estadisticas
        }
    
    def _procesar_alumnos_actividad(self, alumnos, carpeta_actividad, service_drive, 
                                     contexto_consigna, titulo_actividad, materia_nombre):
        """
        Procesa todos los alumnos de una actividad.
        """
        # Lazy imports para evitar circular imports
        from main import (
            evaluar_entrega_automatica,
            _limpiar_nombre_ruta
        )
        
        resultado = {
            "actividad": titulo_actividad,
            "alumnos_procesados": 0,
            "evaluaciones": []
        }
        
        for idx, alumno in enumerate(alumnos, 1):
            nombre_alumno = alumno.get("nombre", "Sin_nombre")
            nombre_limpio = _limpiar_nombre_ruta(nombre_alumno)
            
            # Crear carpeta individual para alumno
            carpeta_alumno = os.path.join(carpeta_actividad, nombre_limpio)
            os.makedirs(carpeta_alumno, exist_ok=True)
            
            print(f"   [{idx:2d}] {nombre_alumno:40s} ", end="", flush=True)
            
            # Descargar archivos de entrega
            archivos_descargados = self._descargar_entrega_alumno(
                alumno, 
                carpeta_alumno,
                service_drive
            )
            
            # Evaluar usando motor único
            evaluacion = evaluar_entrega_automatica(
                alumno,
                titulo_actividad,
                service_drive,
                contexto_consigna
            )
            
            # Enriquecer evaluación con metadata
            evaluacion["alumno"] = nombre_alumno
            evaluacion["materia"] = materia_nombre
            evaluacion["actividad"] = titulo_actividad
            evaluacion["archivos_descargados"] = archivos_descargados
            evaluacion["fecha"] = datetime.datetime.now().isoformat()
            
            # Mostrar resultado
            nota = evaluacion.get("nota", 0)
            estado = evaluacion.get("estado", "?")
            
            if nota >= 7:
                icono = "✅"
            elif nota >= 4:
                icono = "⚠️"
            else:
                icono = "❌"
            
            print(f"{icono} Nota: {nota}/10 | {estado[:20]}")
            
            # Guardar JSON individual de evaluación
            ruta_json_eval = os.path.join(carpeta_alumno, "evaluacion.json")
            try:
                with open(ruta_json_eval, 'w', encoding='utf-8') as f:
                    json.dump(evaluacion, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"      ⚠️  Error guardando JSON: {e}")
            
            # Registrar evaluación
            self.evaluaciones.append(evaluacion)
            resultado["evaluaciones"].append(evaluacion)
            resultado["alumnos_procesados"] += 1
            
            # Actualizar estadísticas
            self.estadisticas["total_alumnos"] += 1
            if estado == "Adeuda entrega":
                self.estadisticas["sin_entrega"] += 1
            else:
                self.estadisticas["evaluaciones_exitosas"] += 1
            
            if materia_nombre not in self.estadisticas["por_materia"]:
                self.estadisticas["por_materia"][materia_nombre] = {
                    "total": 0, "exitosas": 0, "sin_entrega": 0
                }
            self.estadisticas["por_materia"][materia_nombre]["total"] += 1
        
        return resultado
    
    def _descargar_entrega_alumno(self, alumno, carpeta_alumno, service_drive):
        """
        Descarga todos los archivos adjuntos del alumno en su carpeta.
        """
        # Lazy imports para evitar circular imports
        from main import (
            descargar_adjunto_drive,
            _obtener_drive_file_desde_attachment
        )
        
        attachments = alumno.get("attachments", []) or []
        archivos_descargados = 0
        
        for adj in attachments[:10]:  # Limitar a 10 archivos por seguridad
            try:
                drive_file = _obtener_drive_file_desde_attachment(adj)
                if not drive_file:
                    continue
                
                file_id = drive_file.get("id")
                file_name = drive_file.get("title", "archivo")
                
                if not file_id:
                    continue
                
                # Obtener MIME type
                try:
                    metadata = service_drive.files().get(fileId=file_id, fields="mimeType").execute()
                    mime_type = metadata.get("mimeType", "")
                except:
                    mime_type = ""
                
                # Si es Google Doc, agregar .docx
                if mime_type == 'application/vnd.google-apps.document':
                    if not file_name.lower().endswith('.docx'):
                        file_name = file_name + '.docx'
                
                # Descargar
                contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
                if contenido:
                    ruta_archivo = os.path.join(carpeta_alumno, file_name)
                    with open(ruta_archivo, 'wb') as f:
                        f.write(contenido)
                    archivos_descargados += 1
            
            except Exception as e:
                pass  # Silenciar errores de descarga individual
        
        return archivos_descargados
    
    def _generar_reportes(self, carpeta_materia, materia_nombre):
        """
        Genera reportes finales en JSON y Excel.
        """
        if not self.evaluaciones:
            print("⚠️  No hay evaluaciones para reportar")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Reporte JSON
        print("\n💾 Generando reporte JSON...")
        reporte_json = {
            "materia": materia_nombre,
            "fecha": datetime.datetime.now().isoformat(),
            "total_evaluaciones": len(self.evaluaciones),
            "evaluaciones": self.evaluaciones,
            "estadisticas": self.estadisticas
        }
        
        ruta_json = os.path.join(carpeta_materia, f"REPORTE_EVALUACIONES_{timestamp}.json")
        try:
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(reporte_json, f, ensure_ascii=False, indent=2)
            print(f"   ✅ JSON: {ruta_json}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Reporte Excel
        print("📊 Generando reporte Excel...")
        self._generar_excel(carpeta_materia, timestamp)
    
    def _generar_excel(self, carpeta_materia, timestamp):
        """
        Genera planilla Excel con evaluaciones.
        """
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Evaluaciones"
            
            # Encabezados
            encabezados = [
                "Alumno",
                "Materia",
                "Actividad",
                "Nota",
                "Estado",
                "Motivo",
                "Feedback",
                "Fecha"
            ]
            
            ws.append(encabezados)
            
            # Estilos para encabezado
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True, size=11)
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            
            # Datos
            for eval in self.evaluaciones:
                nota = eval.get("nota", "?")
                estado = eval.get("estado", "?")
                
                # Color por nota
                if nota >= 7:
                    row_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif nota >= 4:
                    row_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                else:
                    row_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                fila = [
                    eval.get("alumno", "?"),
                    eval.get("materia", "?"),
                    eval.get("actividad", "?"),
                    nota,
                    estado,
                    eval.get("motivo", "")[:100],
                    eval.get("feedback", "")[:200],
                    eval.get("fecha", "?")[:10]
                ]
                
                ws.append(fila)
                
                # Aplicar color a la fila
                for cell in ws[ws.max_row]:
                    cell.fill = row_fill
                    cell.alignment = Alignment(vertical="top", wrap_text=True)
            
            # Ajustar ancho de columnas
            ws.column_dimensions['A'].width = 25
            ws.column_dimensions['B'].width = 20
            ws.column_dimensions['C'].width = 25
            ws.column_dimensions['D'].width = 8
            ws.column_dimensions['E'].width = 20
            ws.column_dimensions['F'].width = 30
            ws.column_dimensions['G'].width = 40
            ws.column_dimensions['H'].width = 12
            
            ruta_excel = os.path.join(
                Path(carpeta_materia).parent,
                f"EVALUACIONES_{timestamp}.xlsx"
            )
            wb.save(ruta_excel)
            print(f"   ✅ Excel: {ruta_excel}")
        
        except Exception as e:
            print(f"   ❌ Error generando Excel: {e}")


def menu_descarga_consistente():
    """
    Menú para usar el descargador consistente.
    """
    # Importaciones lazy para evitar circular imports
    from main import (
        obtener_credenciales,
        listar_materias_activas,
        listar_trabajos_del_curso,
        listar_alumnos_por_actividad,
        evaluar_entrega_automatica,
        obtener_contexto_consigna,
        descargar_adjunto_drive,
        _obtener_drive_file_desde_attachment,
        _limpiar_nombre_ruta
    )
    from googleapiclient.discovery import build
    
    print("\n" + "="*70)
    print("  DESCARGA Y EVALUACIÓN CONSISTENTE")
    print("="*70)
    print("\nEsta herramienta descarga entregas de Classroom y las evalúa")
    print("con UN SOLO motor de evaluación automático (consistente).")
    print("\nEstructura: Correcciones_Classroom/Materia/Actividad/NombreAlumno/\n")
    
    # Autenticar
    print("🔐 Autenticando con Google...")
    try:
        creds = obtener_credenciales()
        service = build("classroom", "v1", credentials=creds)
        service_drive = build("drive", "v3", credentials=creds)
        print("   ✅ Autenticación exitosa\n")
    except Exception as e:
        print(f"   ❌ Error de autenticación: {e}")
        return
    
    # Obtener materias
    print("📚 Obteniendo materias...")
    try:
        materias = listar_materias_activas(service)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    if not materias:
        print("⚠️  No se encontraron materias")
        return
    
    # Seleccionar materia
    print("\nMaterias disponibles:")
    for i, materia in enumerate(materias, 1):
        print(f"   [{i}] {materia['name']}")
    
    try:
        idx = int(input("\nSelecciona número de materia: ").strip())
        if idx < 1 or idx > len(materias):
            print("❌ Opción inválida")
            return
        
        materia_seleccionada = materias[idx - 1]
        course_id = materia_seleccionada["id"]
    except ValueError:
        print("❌ Entrada inválida")
        return
    
    # Ejecutar descarga y evaluación
    descargador = DescargadorYEvaluadorConsistente()
    resultado = descargador.descargar_y_evaluar_todo(service, service_drive, course_id)
    
    # Resumen final
    print("\n" + "="*70)
    print("  📊 RESUMEN DE PROCESAMIENTO")
    print("="*70)
    print(f"✅ Total de alumnos: {resultado['estadisticas']['total_alumnos']}")
    print(f"✅ Evaluaciones exitosas: {resultado['estadisticas']['evaluaciones_exitosas']}")
    print(f"⚠️  Sin entrega: {resultado['estadisticas']['sin_entrega']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    menu_descarga_consistente()
