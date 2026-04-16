from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import uuid
from datetime import datetime
import re
import requests

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== REFERENCIAS REALES ==========
REFERENCIAS = {
    'informatica': [
        "Tanenbaum, A. S. (2017). Organización de Computadores. Pearson.",
        "Stallings, W. (2016). Sistemas Operativos. Pearson.",
        "Laudon, K. C., & Laudon, J. P. (2021). Sistemas de Información Gerencial. Pearson."
    ],
    'default': [
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla."
    ]
}

def obtener_referencias(tema):
    tema_lower = tema.lower()
    if 'informática' in tema_lower or 'computación' in tema_lower:
        return REFERENCIAS['informatica']
    return REFERENCIAS['default']

# ========== GENERADOR DE CONTENIDO ==========
def generar_contenido(tipo, tema, info_usuario=""):
    tema_limpio = tema if tema else "el tema de investigación"
    
    if tipo == 'introduccion':
        return f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia en el contexto educativo actual.<br/><br/>

<b>Contextualización del problema</b><br/>
En las instituciones educativas, se ha observado que los estudiantes presentan dificultades significativas en la comprensión de los conceptos fundamentales relacionados con {tema_limpio}.<br/><br/>

<b>Planteamiento del problema</b><br/>
¿Cuál es el nivel de comprensión y aplicación de los conceptos fundamentales de {tema_limpio} en los estudiantes?<br/><br/>

<b>Justificación</b><br/>
Este trabajo se justifica desde el punto de vista teórico, práctico e institucional, aportando al conocimiento existente y ofreciendo estrategias de mejora."""
    
    elif tipo == 'objetivos':
        return f"""<b>Objetivo General</b><br/><br/>
Analizar la comprensión y aplicación de los conceptos fundamentales de {tema_limpio} en estudiantes de educación superior.<br/><br/><br/>

<b>Objetivos Específicos</b><br/><br/>
1. Identificar los conceptos teóricos básicos relacionados con {tema_limpio}.<br/><br/>
2. Describir las dificultades más comunes que enfrentan los estudiantes.<br/><br/>
3. Analizar la relación entre el dominio de {tema_limpio} y el rendimiento académico.<br/><br/>
4. Proponer estrategias didácticas específicas para mejorar el aprendizaje."""
    
    elif tipo == 'marco_teorico':
        return f"""<b>Antecedentes</b><br/><br/>
El estudio de {tema_limpio} ha sido abordado por diversos autores en las últimas décadas.<br/><br/>

<b>Bases teóricas</b><br/><br/>
La teoría constructivista del aprendizaje proporciona el marco pedagógico fundamental.<br/><br/>

<b>Conceptos clave</b><br/><br/>
• Aprendizaje significativo<br/>
• Competencia digital<br/>
• Metacognición"""
    
    elif tipo == 'metodologia':
        return f"""<b>Enfoque y tipo de investigación</b><br/><br/>
Enfoque mixto (cualitativo-cuantitativo), diseño no experimental transversal.<br/><br/>

<b>Población y muestra</b><br/>
Estudiantes de educación superior, muestra representativa.<br/><br/>

<b>Instrumentos</b><br/>
• Cuestionario estructurado<br/>
• Prueba de conocimientos<br/>
• Entrevistas semiestructuradas"""
    
    elif tipo == 'desarrollo':
        return f"""<b>Análisis de resultados</b><br/><br/>
Los hallazgos indican que el dominio de {tema_limpio} presenta variaciones significativas.<br/><br/>

<b>Dimensiones analizadas</b><br/>
• Conocimientos teóricos<br/>
• Habilidades prácticas<br/>
• Actitudes hacia el aprendizaje"""
    
    elif tipo == 'conclusiones':
        return f"""1. Se ha logrado cumplir con los objetivos planteados.<br/><br/>
2. Las metodologías prácticas demostraron mayor efectividad.<br/><br/>
3. Se requiere investigación adicional para generalizar hallazgos."""
    
    elif tipo == 'recomendaciones':
        return f"""<b>Para la institución</b><br/><br/>
1. Fortalecer programas de formación.<br/><br/>
<b>Para los docentes</b><br/>
2. Implementar metodologías activas.<br/><br/>
<b>Para futuros estudios</b><br/>
3. Ampliar la muestra y el alcance."""
    
    return ""

# ========== GENERADOR DE PDF ==========
class GeneradorPDF:
    def __init__(self):
        self.estilos = self._crear_estilos()
    
    def _crear_estilos(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TextoJustificado', parent=styles['Normal'],
            alignment=TA_JUSTIFY, fontSize=11, fontName='Times-Roman', spaceAfter=12, leading=16))
        styles.add(ParagraphStyle(name='Titulo1', parent=styles['Heading1'],
            fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'), spaceBefore=24, spaceAfter=16))
        styles.add(ParagraphStyle(name='TituloPortada', parent=styles['Title'],
            fontSize=24, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a365d')))
        return styles
    
    def generar_pdf(self, datos_usuario, opciones, texto_auto=""):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        
        # Generar o usar contenido del usuario
        introduccion = datos_usuario.get('introduccion', '')
        if not introduccion or len(introduccion) < 50:
            introduccion = generar_contenido('introduccion', tema, texto_auto)
        
        objetivos = datos_usuario.get('objetivos', '')
        if not objetivos or len(objetivos) < 50:
            objetivos = generar_contenido('objetivos', tema)
        
        marco_teorico = datos_usuario.get('marco_teorico', '')
        if not marco_teorico or len(marco_teorico) < 50:
            marco_teorico = generar_contenido('marco_teorico', tema)
        
        metodologia = datos_usuario.get('metodologia', '')
        if not metodologia or len(metodologia) < 50:
            metodologia = generar_contenido('metodologia', tema)
        
        desarrollo = datos_usuario.get('desarrollo', '')
        if not desarrollo or len(desarrollo) < 50:
            desarrollo = generar_contenido('desarrollo', tema)
        
        conclusiones = datos_usuario.get('conclusiones', '')
        if not conclusiones or len(conclusiones) < 50:
            conclusiones = generar_contenido('conclusiones', tema)
        
        recomendaciones = datos_usuario.get('recomendaciones', '')
        if opciones.get('incluir_recomendaciones', True) and (not recomendaciones or len(recomendaciones) < 50):
            recomendaciones = generar_contenido('recomendaciones', tema)
        
        referencias = obtener_referencias(tema)
        
        # Generar PDF
        filename = f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.pdf"
        filepath = os.path.join('informes_generados', filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        story = []
        
        # PORTADA
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("INFORME ACADÉMICO", self.estilos['TituloPortada']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(tema.upper(), self.estilos['TextoJustificado']))
        story.append(Spacer(1, 1.2*inch))
        story.append(Paragraph(f"<b>Presentado por:</b> {nombre}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Asignatura:</b> {asignatura}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Docente:</b> {profesor}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Institución:</b> {institucion}", self.estilos['TextoJustificado']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {fecha_entrega}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # ÍNDICE
        story.append(Paragraph("ÍNDICE", self.estilos['Titulo1']))
        indices = ["1. INTRODUCCIÓN", "2. OBJETIVOS", "3. MARCO TEÓRICO", "4. METODOLOGÍA",
                   "5. DESARROLLO", "6. CONCLUSIONES", "7. REFERENCIAS"]
        if opciones.get('incluir_resultados', True):
            indices.insert(5, "6. RESULTADOS")
        if opciones.get('incluir_recomendaciones', True):
            indices.append("RECOMENDACIONES")
        
        for idx in indices:
            story.append(Paragraph(f"• {idx}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # SECCIONES
        contador = 1
        story.append(Paragraph(f"{contador}. INTRODUCCIÓN", self.estilos['Titulo1']))
        story.append(Paragraph(introduccion.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. OBJETIVOS", self.estilos['Titulo1']))
        story.append(Paragraph(objetivos.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. MARCO TEÓRICO", self.estilos['Titulo1']))
        story.append(Paragraph(marco_teorico.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. METODOLOGÍA", self.estilos['Titulo1']))
        story.append(Paragraph(metodologia.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. DESARROLLO", self.estilos['Titulo1']))
        story.append(Paragraph(desarrollo.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        if opciones.get('incluir_resultados', True):
            story.append(Paragraph(f"{contador}. RESULTADOS", self.estilos['Titulo1']))
            data = [['Indicador', 'Valor', 'Observación'], ['Conocimiento teórico', '72.4/100', 'Dominio moderado'], ['Habilidades prácticas', '68.7/100', 'Requiere refuerzo']]
            tabla = Table(data, colWidths=[1.8*inch, 1.5*inch, 2*inch])
            tabla.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a365d')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
            story.append(tabla)
            story.append(PageBreak())
            contador += 1
        
        story.append(Paragraph(f"{contador}. CONCLUSIONES", self.estilos['Titulo1']))
        story.append(Paragraph(conclusiones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        if opciones.get('incluir_recomendaciones', True):
            story.append(Paragraph(f"{contador}. RECOMENDACIONES", self.estilos['Titulo1']))
            story.append(Paragraph(recomendaciones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        story.append(Paragraph(f"{contador}. REFERENCIAS", self.estilos['Titulo1']))
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {ref}", self.estilos['TextoJustificado']))
        
        doc.build(story)
        return filename, filepath

generador = GeneradorPDF()

# ========== RUTAS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        modo = datos.get('modo', 'auto')
        texto_auto = datos.get('texto_completo', '') if modo in ['auto', 'rapido'] else ''
        
        opciones = {
            'incluir_resumen': datos.get('incluir_resumen', False),
            'incluir_resultados': datos.get('incluir_resultados', True),
            'incluir_recomendaciones': datos.get('incluir_recomendaciones', True)
        }
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': datos.get('tema', ''),
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', ''),
            'introduccion': datos.get('introduccion', ''),
            'objetivos': datos.get('objetivos', ''),
            'marco_teorico': datos.get('marco_teorico', ''),
            'metodologia': datos.get('metodologia', ''),
            'desarrollo': datos.get('desarrollo', ''),
            'conclusiones': datos.get('conclusiones', ''),
            'recomendaciones': datos.get('recomendaciones', '')
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, texto_auto)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/descargar/{filename}'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(
        os.path.join('informes_generados', filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
