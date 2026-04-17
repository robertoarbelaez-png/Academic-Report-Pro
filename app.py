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

# ========== CONFIGURACIÓN DE GROQ ==========
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

print("=" * 50)
print("🚀 INICIANDO APLICACIÓN")
print(f"🔑 Groq API Key cargada: {'SÍ ✅' if GROQ_API_KEY else 'NO ❌'}")
print("=" * 50)

def generar_informe_completo_con_ia(tema, info_usuario=""):
    """Genera TODO el informe en UNA sola llamada a Groq"""
    
    if not GROQ_API_KEY:
        print("❌ No hay API key de Groq configurada")
        return None
    
    print(f"🤖 Generando informe COMPLETO con Groq para: {tema[:50]}...")
    
    prompt = f"""Genera un INFORME ACADÉMICO COMPLETO sobre el tema: "{tema}".

Información adicional: {info_usuario if info_usuario else 'No hay información adicional'}

El informe debe tener estas secciones:

INTRODUCCION: (Contexto, problema, justificación - 300-400 palabras)

OBJETIVOS: 
- Objetivo General: (1)
- Objetivos Específicos: (4 numerados)

MARCO TEORICO:
- Antecedentes:
- Bases Teóricas:
- Estado del Arte:

METODOLOGIA:
- Enfoque:
- Población y muestra:
- Instrumentos:
- Procedimiento:

DESARROLLO:
- Análisis de resultados:
- Dimensiones analizadas:
- Discusión:

CONCLUSIONES: (5 puntos principales)

RECOMENDACIONES: (Para institución, docentes, futuros estudios)

Escribe en español, tono académico profesional. Cada sección debe ser detallada."""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un asistente académico profesional. Generas informes universitarios completos y detallados en español."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        print(f"📡 Enviando petición a Groq...")
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=120)
        print(f"📡 Respuesta código: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            contenido = resultado['choices'][0]['message']['content']
            print(f"✅ Groq generó {len(contenido)} caracteres")
            
            # Extraer secciones
            secciones = {
                'introduccion': extraer_seccion_simple(contenido, 'INTRODUCCION'),
                'objetivos': extraer_seccion_simple(contenido, 'OBJETIVOS'),
                'marco_teorico': extraer_seccion_simple(contenido, 'MARCO TEORICO'),
                'metodologia': extraer_seccion_simple(contenido, 'METODOLOGIA'),
                'desarrollo': extraer_seccion_simple(contenido, 'DESARROLLO'),
                'conclusiones': extraer_seccion_simple(contenido, 'CONCLUSIONES'),
                'recomendaciones': extraer_seccion_simple(contenido, 'RECOMENDACIONES')
            }
            
            # Verificar que todas las secciones tengan contenido
            for key in secciones:
                if not secciones[key] or len(secciones[key]) < 50:
                    print(f"⚠️ Sección {key} vacía, usando contenido local")
                    secciones[key] = generar_contenido_local(key, tema)
            
            return secciones
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando con Groq: {str(e)}")
        return None

def extraer_seccion_simple(contenido, nombre):
    """Extrae una sección del contenido generado por IA"""
    # Buscar patrones como "INTRODUCCION:" o "INTRODUCCION\n"
    patrones = [
        rf'{nombre}[:\\s]*(.*?)(?={{"|$|\\n\\n[A-Z]|\\n[A-Z]+:)',
        rf'{nombre}\\s*\\n(.*?)(?=\\n\\n[A-Z]|\\n[A-Z]+:)',
    ]
    
    for patron in patrones:
        match = re.search(patron, contenido, re.DOTALL | re.IGNORECASE)
        if match:
            texto = match.group(1).strip()
            # Limpiar y formatear
            texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
            texto = texto.replace('\n', '<br/>')
            # Limitar longitud
            if len(texto) > 3000:
                texto = texto[:3000] + "..."
            return texto
    
    # Si no encuentra la sección, buscar por palabras clave
    if nombre == 'INTRODUCCION':
        match = re.search(r'(?i)(INTRODUCCIÓN|INTRODUCCION)[:\\s]*(.*?)(?=\\n\\n[A-Z]|$)', contenido, re.DOTALL)
        if match:
            texto = match.group(2).strip()
            texto = texto.replace('\n', '<br/>')
            return texto[:2000]
    
    return ""

def generar_contenido_local(tipo, tema):
    """Contenido de respaldo (cuando no hay IA o falla)"""
    tema_limpio = tema if tema else "el tema de investigación"
    
    contenidos = {
        'introduccion': f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia.<br/><br/>
<b>Contextualización</b><br/>En las instituciones educativas, se observan dificultades en la comprensión de {tema_limpio}.<br/><br/>
<b>Planteamiento del problema</b><br/>¿Cuál es el nivel de comprensión de {tema_limpio}?<br/><br/>
<b>Justificación</b><br/>Este estudio aporta al conocimiento existente.""",
        
        'objetivos': f"""<b>Objetivo General</b><br/><br/>Analizar la comprensión de {tema_limpio}.<br/><br/><br/>
<b>Objetivos Específicos</b><br/><br/>1. Identificar conceptos teóricos.<br/><br/>2. Describir dificultades.<br/><br/>3. Analizar relación con rendimiento.<br/><br/>4. Proponer estrategias.""",
        
        'marco_teorico': f"""<b>Antecedentes</b><br/><br/>El estudio de {tema_limpio} ha sido abordado por diversos autores.<br/><br/>
<b>Bases teóricas</b><br/>La teoría constructivista del aprendizaje es fundamental.<br/><br/>
<b>Conceptos clave</b><br/>• Aprendizaje significativo<br/>• Competencia digital<br/>• Metacognición""",
        
        'metodologia': f"""<b>Enfoque</b><br/>Enfoque mixto.<br/><br/>
<b>Población y muestra</b><br/>Estudiantes de educación superior.<br/><br/>
<b>Instrumentos</b><br/>Cuestionario, prueba de conocimientos, entrevistas.""",
        
        'desarrollo': f"""<b>Análisis de resultados</b><br/>Los hallazgos indican variaciones significativas.<br/><br/>
<b>Dimensiones analizadas</b><br/>• Conocimientos teóricos<br/>• Habilidades prácticas<br/>• Actitudes""",
        
        'conclusiones': f"""1. Se cumplieron los objetivos.<br/><br/>2. Metodologías prácticas son más efectivas.<br/><br/>3. La experiencia previa influye.<br/><br/>4. No hay diferencias por género.<br/><br/>5. Se requiere más investigación.""",
        
        'recomendaciones': f"""<b>Para la institución</b><br/>1. Fortalecer programas.<br/><br/>
<b>Para los docentes</b><br/>2. Implementar metodologías activas.<br/><br/>
<b>Para futuros estudios</b><br/>3. Ampliar la muestra."""
    }
    return contenidos.get(tipo, "Contenido en desarrollo.")

# ========== REFERENCIAS ==========
REFERENCIAS = {
    'default': [
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla."
    ]
}

def obtener_referencias(tema):
    return REFERENCIAS['default']

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
    
    def generar_pdf(self, datos_usuario, opciones, secciones_ia=None):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        
        # Usar secciones de IA si existen
        if secciones_ia and isinstance(secciones_ia, dict):
            introduccion = secciones_ia.get('introduccion', '')
            objetivos = secciones_ia.get('objetivos', '')
            marco_teorico = secciones_ia.get('marco_teorico', '')
            metodologia = secciones_ia.get('metodologia', '')
            desarrollo = secciones_ia.get('desarrollo', '')
            conclusiones = secciones_ia.get('conclusiones', '')
            recomendaciones = secciones_ia.get('recomendaciones', '')
            print("✅ Usando secciones generadas por IA")
        else:
            introduccion = generar_contenido_local('introduccion', tema)
            objetivos = generar_contenido_local('objetivos', tema)
            marco_teorico = generar_contenido_local('marco_teorico', tema)
            metodologia = generar_contenido_local('metodologia', tema)
            desarrollo = generar_contenido_local('desarrollo', tema)
            conclusiones = generar_contenido_local('conclusiones', tema)
            recomendaciones = generar_contenido_local('recomendaciones', tema)
            print("⚠️ Usando contenido local")
        
        referencias = obtener_referencias(tema)
        
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
        if opciones.get('incluir_recomendaciones', True):
            indices.insert(-1, "RECOMENDACIONES")
        
        for idx in indices:
            story.append(Paragraph(f"• {idx}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # SECCIONES
        story.append(Paragraph("1. INTRODUCCIÓN", self.estilos['Titulo1']))
        story.append(Paragraph(introduccion, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("2. OBJETIVOS", self.estilos['Titulo1']))
        story.append(Paragraph(objetivos, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("3. MARCO TEÓRICO", self.estilos['Titulo1']))
        story.append(Paragraph(marco_teorico, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("4. METODOLOGÍA", self.estilos['Titulo1']))
        story.append(Paragraph(metodologia, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("5. DESARROLLO", self.estilos['Titulo1']))
        story.append(Paragraph(desarrollo, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("6. CONCLUSIONES", self.estilos['Titulo1']))
        story.append(Paragraph(conclusiones, self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        if opciones.get('incluir_recomendaciones', True):
            story.append(Paragraph("7. RECOMENDACIONES", self.estilos['Titulo1']))
            story.append(Paragraph(recomendaciones, self.estilos['TextoJustificado']))
            story.append(PageBreak())
            story.append(Paragraph("8. REFERENCIAS", self.estilos['Titulo1']))
        else:
            story.append(Paragraph("7. REFERENCIAS", self.estilos['Titulo1']))
        
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {ref}", self.estilos['TextoJustificado']))
            story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        print(f"✅ PDF generado: {filename}")
        return filename, filepath

generador = GeneradorPDF()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        modo = datos.get('modo', 'auto')
        tema = datos.get('tema', '')
        texto_auto = datos.get('texto_completo', '') if modo in ['auto', 'rapido'] else ''
        
        if modo == 'rapido' and texto_auto:
            tema = texto_auto
        
        print(f"📨 Solicitud recibida - Modo: {modo}, Tema: {tema[:50] if tema else 'VACIO'}")
        
        opciones = {
            'incluir_recomendaciones': datos.get('incluir_recomendaciones', True)
        }
        
        secciones_ia = None
        if tema and len(tema) > 5:
            secciones_ia = generar_informe_completo_con_ia(tema, texto_auto)
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': tema if tema else 'Tema de Investigación',
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', '')
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, secciones_ia)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/descargar/{filename}'
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(
        os.path.join('informes_generados', filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado en puerto {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
