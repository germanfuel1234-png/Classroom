"""
GENERADOR DE PLANILLA DE CÁLCULO EXCEL
Convierte evaluaciones JSON a planilla Excel con una hoja por materia.
"""

import json
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class GeneradorPlanilla:
    """
    Crea planillas Excel con evaluaciones organizadas por materia.
    """
    
    def __init__(self):
        self.wb = Workbook()
        self.wb.remove(self.wb.active)  # Remover hoja por defecto
        self.materias_hojas = {}
        
    def cargar_evaluaciones(self, ruta_json):
        """Carga las evaluaciones desde un archivo JSON."""
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def crear_hoja_materia(self, materia):
        """Crea una nueva hoja para una materia."""
        if materia in self.materias_hojas:
            return self.materias_hojas[materia]
        
        ws = self.wb.create_sheet(title=materia[:31])  # Límite de 31 caracteres en Excel
        self.materias_hojas[materia] = ws
        
        # Crear encabezados
        encabezados = [
            "Apellido y Nombre",
            "Actividad",
            "Nota (1-10)",
            "Descripción Técnica",
            "Comentario Pedagógico"
        ]
        
        for col, encabezado in enumerate(encabezados, start=1):
            celda = ws.cell(row=1, column=col)
            celda.value = encabezado
            celda.font = Font(bold=True, color="FFFFFF", size=11)
            celda.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Configurar anchos de columna
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 50
        
        # Altura de encabezado
        ws.row_dimensions[1].height = 30
        
        return ws
    
    def agregar_evaluacion(self, materia, evaluacion):
        """Agrega una evaluación a la hoja de la materia."""
        ws = self.crear_hoja_materia(materia)
        
        # Encontrar siguiente fila
        fila = ws.max_row + 1
        
        # Agregar datos
        datos = [
            evaluacion.get("apellido_nombre", ""),
            evaluacion.get("actividad", ""),
            evaluacion.get("nota", ""),
            evaluacion.get("descripcion", ""),
            evaluacion.get("comentario_privado", "")
        ]
        
        for col, dato in enumerate(datos, start=1):
            celda = ws.cell(row=fila, column=col)
            celda.value = dato
            
            # Formato según columna
            if col == 3:  # Nota
                celda.alignment = Alignment(horizontal="center", vertical="top")
                celda.font = Font(bold=True, size=11)
                # Color de fondo según nota
                if isinstance(dato, (int, float)):
                    if dato >= 8:
                        celda.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    elif dato >= 6:
                        celda.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                    else:
                        celda.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            else:
                celda.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            # Bordes
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            celda.border = thin_border
        
        # Ajustar altura de fila automáticamente
        ws.row_dimensions[fila].height = 60
    
    def agregar_hoja_resumen(self):
        """Crea una hoja de resumen con estadísticas."""
        ws = self.wb.create_sheet("Resumen", 0)  # Primera hoja
        
        ws['A1'] = "REPORTE DE EVALUACIONES PEDAGÓGICAS"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        ws.merge_cells('A1:D1')
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws['A2'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(italic=True, size=10)
        
        # Estadísticas por materia
        fila = 4
        ws['A4'] = "Materia"
        ws['B4'] = "Total Estudiantes"
        ws['C4'] = "Promedio de Notas"
        ws['D4'] = "Aprobados"
        
        for col in ['A', 'B', 'C', 'D']:
            celda = ws[f'{col}4']
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        fila = 5
        for materia, ws_materia in self.materias_hojas.items():
            notas = []
            for fila_datos in range(2, ws_materia.max_row + 1):
                nota = ws_materia.cell(row=fila_datos, column=3).value
                if isinstance(nota, (int, float)):
                    notas.append(nota)
            
            aprobados = sum(1 for n in notas if n >= 6)
            promedio = sum(notas) / len(notas) if notas else 0
            
            ws[f'A{fila}'] = materia
            ws[f'B{fila}'] = len(notas)
            ws[f'C{fila}'] = f"{promedio:.2f}"
            ws[f'D{fila}'] = aprobados
            
            fila += 1
        
        # Ancho de columnas
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
    
    def guardar(self, ruta_salida):
        """Guarda la planilla Excel."""
        # Agregar hoja de resumen al inicio
        if len(self.materias_hojas) > 0:
            self.agregar_hoja_resumen()
        
        self.wb.save(ruta_salida)
        print(f"✓ Planilla de cálculo guardada en: {ruta_salida}")


def procesar_evaluaciones_a_planilla(ruta_json_entrada, ruta_excel_salida):
    """
    Procesa archivo JSON de evaluaciones y genera Excel.
    
    Args:
        ruta_json_entrada (str): Ruta al JSON de evaluaciones
        ruta_excel_salida (str): Ruta de salida para el Excel
    """
    # Cargar evaluaciones
    with open(ruta_json_entrada, 'r', encoding='utf-8') as f:
        evaluaciones = json.load(f)
    
    # Crear planilla
    generador = GeneradorPlanilla()
    
    # Agrupar por materia (usar 'actividad' como materia por ahora)
    for evaluacion in evaluaciones:
        materia = evaluacion.get("actividad", "General")
        generador.agregar_evaluacion(materia, evaluacion)
    
    # Guardar
    generador.guardar(ruta_excel_salida)


if __name__ == "__main__":
    # Configurar rutas
    ruta_json = "evaluaciones_masivas.json"
    ruta_excel = "evaluaciones_estudiantes.xlsx"
    
    # Procesar
    if os.path.exists(ruta_json):
        procesar_evaluaciones_a_planilla(ruta_json, ruta_excel)
        print(f"\n{'='*60}")
        print("PLANILLA GENERADA EXITOSAMENTE")
        print(f"{'='*60}")
    else:
        print(f"ERROR: No se encontró {ruta_json}")
        print("Por favor, ejecuta primero: python evaluacion_masiva.py")
