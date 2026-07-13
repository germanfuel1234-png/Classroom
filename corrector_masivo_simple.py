"""
CORRECTOR MASIVO SIMPLIFICADO - 2 CRITERIOS ÚNICAMENTE
Evalúa entregas con 2 criterios: Completitud + Contenido
Genera Excel con estructura: Materia | TP | Alumno | Estado | Nota | Motivo | Devolución
"""

import os
import json
import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from docx import Document
import PyPDF2


class CorrectorMasivoSimple:
    """Evaluador simplificado: solo completitud + contenido"""
    
    def __init__(self):
        self.evaluaciones = []
    
    def ejecutar_correccion_masiva_simple(self, ruta_base="Correcciones_Classroom"):
        """
        FASE 2: Lee archivos descargados y genera evaluaciones simples.
        
        Args:
            ruta_base (str): Carpeta raíz con estructura Materia/TP/Alumno
            
        Returns:
            dict: {total_alumnos, evaluaciones_generadas}
        """
        print("[FASE 2/2] 📊 Evaluando entregas (2 criterios)...\n")
        
        if not os.path.exists(ruta_base):
            print(f"❌ Carpeta {ruta_base} no existe")
            return {"total_alumnos": 0, "evaluaciones_generadas": 0}
        
        self.evaluaciones = []
        total_alumnos = 0
        
        # Iterar: Materia → TP → Alumno
        for materia_dir in sorted(os.listdir(ruta_base)):
            materia_path = os.path.join(ruta_base, materia_dir)
            if not os.path.isdir(materia_path):
                continue
            
            print(f"📚 Materia: {materia_dir}")
            
            for tp_dir in sorted(os.listdir(materia_path)):
                tp_path = os.path.join(materia_path, tp_dir)
                if not os.path.isdir(tp_path):
                    continue
                
                print(f"   📝 TP: {tp_dir}")
                
                # Leer consigna si existe
                consigna = ""
                ruta_consigna = os.path.join(tp_path, "consigna_referencia.txt")
                if os.path.exists(ruta_consigna):
                    try:
                        with open(ruta_consigna, 'r', encoding='utf-8') as f:
                            consigna = f.read()[:200]
                    except:
                        pass
                
                # Iterar alumnos
                for alumno_dir in sorted(os.listdir(tp_path)):
                    alumno_path = os.path.join(tp_path, alumno_dir)
                    if not os.path.isdir(alumno_path):
                        continue
                    
                    total_alumnos += 1
                    
                    # EVALUAR: 2 criterios simples
                    evaluacion = self._evaluar_alumno_simple(
                        materia=materia_dir,
                        tp=tp_dir,
                        alumno=alumno_dir,
                        ruta_entrega=alumno_path,
                        consigna=consigna
                    )
                    
                    self.evaluaciones.append(evaluacion)
                    
                    # Mostrar feedback de evaluación
                    estado_icon = "✅" if evaluacion["nota"] >= 7 else "⚠️" if evaluacion["nota"] >= 4 else "❌"
                    print(f"      {estado_icon} {alumno_dir}: {evaluacion['nota']}/10 ({evaluacion['estado']})")
        
        # Generar Excel
        print("\n💾 Generando Excel...")
        self._generar_excel(ruta_base)
        
        return {
            "total_alumnos": total_alumnos,
            "evaluaciones_generadas": len(self.evaluaciones)
        }
    
    def _evaluar_alumno_simple(self, materia, tp, alumno, ruta_entrega, consigna):
        """
        Evalúa alumno con 2 criterios:
        1. COMPLETITUD: ¿Tiene archivos o está vacío?
        2. CONTENIDO: ¿El contenido coincide con la consigna?
        
        Nota simple:
        - 1: Vacío/No entregó
        - 3-4: Entrega incompleta o sin relación
        - 5-6: Entrega mínima, parcial
        - 7-8: Entrega adecuada
        - 9-10: Entrega excelente
        """
        
        # Buscar archivos de entrega
        archivos_entrega = []
        contenido_texto = ""
        
        try:
            for archivo in os.listdir(ruta_entrega):
                if archivo in ["consigna_referencia.txt", "estado_descarga.txt", "debug_estructura.json"]:
                    continue
                
                ruta_archivo = os.path.join(ruta_entrega, archivo)
                
                # Extraer texto según tipo
                if archivo.endswith(".txt"):
                    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                        contenido_texto += f.read() + "\n"
                    archivos_entrega.append(archivo)
                
                elif archivo.endswith(".docx"):
                    try:
                        doc = Document(ruta_archivo)
                        contenido_texto += "\n".join([p.text for p in doc.paragraphs]) + "\n"
                        archivos_entrega.append(archivo)
                    except:
                        pass
                
                elif archivo.endswith(".pdf"):
                    try:
                        with open(ruta_archivo, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                contenido_texto += page.extract_text() + "\n"
                        archivos_entrega.append(archivo)
                    except:
                        pass
        
        except Exception as e:
            print(f"   [ERROR] {e}")
        
        # CRITERIO 1: COMPLETITUD
        # ¿Tiene algo?
        tiene_entrega = len(archivos_entrega) > 0
        contenido_vacio = len(contenido_texto.strip()) < 20
        
        if not tiene_entrega or contenido_vacio:
            return {
                "materia": materia,
                "tp": tp,
                "alumno": alumno,
                "estado": "Vacía/Incompleta",
                "nota": 1,
                "motivo": "Entrega vacía o sin contenido detectable.",
                "devolucion": f"Estimado/a {alumno.split()[0]},\n\nTu entrega para {tp} aparece sin contenido o vacía. Por favor, "
                             f"completa el trabajo según los requisitos de la consigna y reentrega.\n\nNota: 1/10."
            }
        
        # CRITERIO 2: CONTENIDO
        # Análisis simple: ¿coincide con consigna?
        
        # Buscar palabras clave de consigna
        consigna_lower = consigna.lower()
        contenido_lower = contenido_texto.lower()
        
        # Extraer palabras clave (>4 caracteres)
        palabras_clave = [
            palabra for palabra in consigna_lower.split()
            if len(palabra) > 4 and palabra.isalnum()
        ][:10]  # Max 10 palabras
        
        # Contar coincidencias
        coincidencias = sum(1 for p in palabras_clave if p in contenido_lower)
        cobertura = (coincidencias / len(palabras_clave)) * 100 if palabras_clave else 0
        
        # Contar palabras de la entrega
        palabras_entrega = len(contenido_texto.split())
        
        # ASIGNAR NOTA SIMPLE
        if palabras_entrega < 20:
            nota = 2
            estado = "Entrega muy breve"
        elif palabras_entrega < 50:
            nota = 3
            estado = "Entrega corta"
        elif cobertura >= 80:
            nota = 9
            estado = "Excelente"
        elif cobertura >= 60:
            nota = 8
            estado = "Buena"
        elif cobertura >= 40:
            nota = 6
            estado = "Aceptable"
        elif cobertura >= 20:
            nota = 5
            estado = "Deficiente"
        else:
            nota = 3
            estado = "No relacionada"
        
        # Ajustar por longitud
        if palabras_entrega > 300:
            nota = min(10, nota + 1)
        
        motivo = f"Concordancia: {cobertura:.0f}%. Palabras: {palabras_entrega}. {estado}."
        
        primer_nombre = alumno.split()[0] if alumno else "Estimado/a"
        
        if nota >= 7:
            devolucion = (
                f"Estimado/a {primer_nombre},\n\n"
                f"Excelente trabajo en {tp}. Tu entrega demuestra "
                f"buena comprensión del tema y cumple con los requisitos solicitados.\n\n"
                f"✓ Bien abordado\n"
                f"✗ Por mejorar: ampliar análisis\n\n"
                f"Nota: {nota}/10."
            )
        elif nota >= 5:
            devolucion = (
                f"Estimado/a {primer_nombre},\n\n"
                f"Tu entrega en {tp} requiere mejoras. Si bien abordas el tema, "
                f"falta profundidad o contenido según los requisitos de la consigna.\n\n"
                f"Por favor, considera: ampliar la entrega, incluir más ejemplos, "
                f"y revisar los puntos solicitados en la consigna.\n\n"
                f"Nota: {nota}/10."
            )
        else:
            devolucion = (
                f"Estimado/a {primer_nombre},\n\n"
                f"Tu entrega en {tp} no cumple adecuadamente con los requisitos. "
                f"Te recomiendo revisar la consigna nuevamente e incluir el análisis "
                f"o contenido faltante.\n\n"
                f"Reentrega solicitada.\n\n"
                f"Nota: {nota}/10."
            )
        
        return {
            "materia": materia,
            "tp": tp,
            "alumno": alumno,
            "estado": estado,
            "nota": nota,
            "motivo": motivo,
            "devolucion": devolucion
        }
    
    def _generar_excel(self, ruta_base="Correcciones_Classroom"):
        """
        Genera Excel con evaluaciones simplificadas.
        Columnas: Materia | TP | Alumno | Estado | Nota | Motivo | Devolución
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluaciones"
        
        # ENCABEZADOS
        encabezados = ["Materia", "TP", "Alumno", "Estado", "Nota", "Motivo Técnico", "Devolución Pedagógica"]
        ws.append(encabezados)
        
        # Estilos encabezado
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for celda in ws[1]:
            celda.fill = header_fill
            celda.font = header_font
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Agregar datos
        for eval_data in self.evaluaciones:
            ws.append([
                eval_data["materia"],
                eval_data["tp"],
                eval_data["alumno"],
                eval_data["estado"],
                eval_data["nota"],
                eval_data["motivo"],
                eval_data["devolucion"]
            ])
        
        # Estilos celdas de datos
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=2):
            nota = row[4].value
            
            # Color según nota
            if nota >= 8:
                fill_color = "C6EFCE"  # Verde
            elif nota >= 6:
                fill_color = "FFEB9C"  # Amarillo
            else:
                fill_color = "FFC7CE"  # Rojo
            
            for celda in row:
                celda.border = thin_border
                celda.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                celda.alignment = Alignment(wrap_text=True, vertical="top")
        
        # Ajustar ancho columnas
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 35
        ws.column_dimensions['G'].width = 45
        
        # Altura fila
        ws.row_dimensions[1].height = 25
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            ws.row_dimensions[row[0].row].height = 60
        
        # Guardar
        ruta_excel = os.path.join(ruta_base, "evaluaciones_simples.xlsx")
        wb.save(ruta_excel)
        print(f"✅ Excel guardado: {ruta_excel}")
        
        return ruta_excel


# ─────────────────────────────────────────
# ENTRY POINT: Función para usar en main.py
# ─────────────────────────────────────────

def iniciar_correccion_masiva_simple(materias_info):
    """
    Ejecuta descarga + evaluación simple.
    
    Args:
        materias_info (list): Lista de dicts con datos de materias de API
    """
    print("\n" + "="*60)
    print("🚀 CORRECCIÓN MASIVA - MODO SIMPLIFICADO (2 Criterios)")
    print("="*60 + "\n")
    
    # FASE 1: Descargar
    print("[FASE 1/2] 📥 Descargando entregas...\n")
    try:
        from descargar_entregas_classroom import descargar_todas_las_entregas
        
        total_alumnos, total_archivos = descargar_todas_las_entregas(
            materias_info,
            ruta_base="Correcciones_Classroom",
            debug=False
        )
        
        print(f"\n✅ Descarga completada:")
        print(f"   - Alumnos: {total_alumnos}")
        print(f"   - Archivos: {total_archivos}")
    
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # FASE 2: Evaluar
    corrector = CorrectorMasivoSimple()
    resultado = corrector.ejecutar_correccion_masiva_simple("Correcciones_Classroom")
    
    print(f"\n✅ Evaluación completada:")
    print(f"   - Alumnos evaluados: {resultado['evaluaciones_generadas']}")
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN EVALUACIONES")
    print("="*60)
    
    for eval_data in corrector.evaluaciones[:5]:  # Mostrar primeros 5
        print(f"\n{eval_data['alumno']} ({eval_data['tp']}):")
        print(f"  Nota: {eval_data['nota']}/10")
        print(f"  Estado: {eval_data['estado']}")
        print(f"  Motivo: {eval_data['motivo']}")
    
    if len(corrector.evaluaciones) > 5:
        print(f"\n... y {len(corrector.evaluaciones) - 5} alumnos más")
    
    print("\n" + "="*60)
    print("✅ Corrección masiva completada")
    print("="*60 + "\n")
