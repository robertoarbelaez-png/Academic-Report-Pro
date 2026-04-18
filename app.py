from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import uuid
from datetime import datetime
import re
import requests

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

print("=" * 50)
print("🚀 VERSIÓN SIMPLIFICADA - Academic Report Pro")
print(f"🔑 API Key: {'SÍ ✅' if GROQ_API_KEY else 'NO ❌'}")
print("=" * 50)

def limpiar_texto(texto):
    if not texto:
        return ""
    # CORRECCIONES CLAVE
    texto = texto.replace('INFORMÉ', 'INFORME')
    texto = texto.replace('Conclusions', 'CONCLUSIONES')
    texto = texto.replace('CONCLUSIONS', 'CONCLUSIONES')
    return texto

def generar_informe(tema):
    """Genera contenido simple pero completo"""
    
    # Si hay API key, intentar con IA
    if GROQ_API_KEY:
        try:
            prompt = f"""Genera un informe académico corto sobre: "{tema}"

Escribe estas secciones:

**INTRODUCCIÓN** (un párrafo)
**OBJETIVOS** (1 general y 3 específicos)
**DESARROLLO** (un párrafo)
**CONCLUSIONES** (3 puntos)

Usa español. Usa CONCLUSIONES (nunca Conclusions)."""
            
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                resultado = response.json()
                contenido = resultado['choices'][0]['message']['content']
                contenido = limpiar_texto(contenido)
                
                # Extraer secciones
                secciones = {
                    'introduccion': re.search(r'\*\*INTRODUCCIÓN\*\*:?(.*?)(?=\*\*OBJETIVOS|\*\*DESARROLLO|\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*INTRODUCCIÓN\*\*:?(.*?)(?=\*\*OBJETIVOS|\*\*DESARROLLO|\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else f"Este informe analiza {tema}.",
                    'objetivos': re.search(r'\*\*OBJETIVOS\*\*:?(.*?)(?=\*\*DESARROLLO|\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*OBJETIVOS\*\*:?(.*?)(?=\*\*DESARROLLO|\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else f"<b>Objetivo General</b><br/>Analizar {tema}.",
                    'desarrollo': re.search(r'\*\*DESARROLLO\*\*:?(.*?)(?=\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*DESARROLLO\*\*:?(.*?)(?=\*\*CONCLUSIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else f"Los resultados muestran la importancia de {tema}.",
                    'conclusiones': re.search(r'\*\*CONCLUSIONES\*\*:?(.*?)$', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*CONCLUSIONES\*\*:?(.*?)$', contenido, re.DOTALL | re.IGNORECASE) else "1. Conclusión principal."
                }
                
                for key in secciones:
                    if secciones[key]:
                        secciones[key] = secciones[key].strip().replace('\n', '<br/>')
                        secciones[key] = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', secciones[key])
                    else:
                        secciones[key] = f"Contenido sobre {tema}."
                
                return secciones
        except Exception as e:
            print(f"Error IA: {e}")
    
    # Contenido local de respaldo (nunca vacío)
    tema_limpio = tema if tema else "el tema"
    return {
        'introduccion': f"El presente informe aborda el estudio de {tema_limpio}, una temática relevante en el contexto actual.",
        'objetivos': f"<b>Objetivo General</b><br/>Analizar {tema_limpio}.<br/><br/><b>Objetivos Específicos</b><br/>1. Identificar aspectos clave.<br/>2. Describir características.<br/>3. Proponer recomendaciones.",
        'desarrollo': f"Los resultados muestran que {tema_limpio} tiene un impacto significativo. Se identificaron múltiples factores que inciden en su desarrollo.",
        'conclusiones': f"1. {tema_limpio} es un tema importante.<br/>2. Se requiere más investigación.<br/>3. Las recomendaciones propuestas son viables."
    }

def obtener_referencias(tema):
    return [
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla."
    ]

class GeneradorPDF:
    def crear_estilos(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TextoJustificado', parent=styles['Normal'],
            alignment=TA_JUSTIFY, fontSize=11, fontName='Times-Roman', spaceAfter=12, leading=16))
        styles.add(ParagraphStyle(name='Titulo1', parent=styles['Heading1'],
            fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'), spaceBefore=24, spaceAfter=16))
        styles.add(ParagraphStyle(name='TituloPortada', parent=styles['Title'],
            fontSize=22, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a365d')))
        return styles
    
    def generar_pdf(self, datos_usuario, secciones):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        
        styles = self.crear_estilos()
        
        filename = f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.pdf"
        filepath = os.path.join('informes_generados', filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        story = []
        
        # PORTADA
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("INFORME ACADÉMICO", styles['TituloPortada']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(tema.upper(), styles['TextoJustificado']))
        story.append(Spacer(1, 1.2*inch))
        story.append(Paragraph(f"<b>Presentado por:</b> {nombre}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Asignatura:</b> {asignatura}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Docente:</b> {profesor}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Institución:</b> {institucion}", styles['TextoJustificado']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {fecha_entrega}", styles['TextoJustificado']))
        story.append(PageBreak())
        
        # CONTENIDO
        story.append(Paragraph("1. INTRODUCCIÓN", styles['Titulo1']))
        story.append(Paragraph(secciones.get('introduccion', ''), styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("2. OBJETIVOS", styles['Titulo1']))
        story.append(Paragraph(secciones.get('objetivos', ''), styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("3. DESARROLLO", styles['Titulo1']))
        story.append(Paragraph(secciones.get('desarrollo', ''), styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("4. CONCLUSIONES", styles['Titulo1']))
        story.append(Paragraph(secciones.get('conclusiones', ''), styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("5. REFERENCIAS", styles['Titulo1']))
        for i, ref in enumerate(obtener_referencias(tema), 1):
            story.append(Paragraph(f"{i}. {ref}", styles['TextoJustificado']))
        
        doc.build(story)
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
        texto_auto = datos.get('texto_completo', '')
        
        if modo == 'rapido' and texto_auto:
            tema = texto_auto
        
        if not tema or len(tema) < 3:
            return jsonify({'success': False, 'error': 'Por favor ingresa un tema válido'}), 400
        
        print(f"📨 Generando informe para: {tema[:50]}...")
        
        secciones = generar_informe(tema)
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': tema,
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', '')
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, secciones)
        
        return jsonify({'success': True, 'filename': filename, 'download_url': f'/descargar/{filename}'})
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join('informes_generados', filename), as_attachment=True, download_name=filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
