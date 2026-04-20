from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY
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

# CONFIG
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ================= LIMPIEZA =================
def limpiar_texto(texto):
    if not texto:
        return ""

    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)

    # **negrita** → HTML
    texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)

    # saltos
    texto = texto.replace('\n', '<br/><br/>')

    texto = texto.replace('Conclusions', 'CONCLUSIONES')
    texto = texto.replace('CONCLUSIONS', 'CONCLUSIONES')

    return texto.strip()

def extraer_seccion(contenido, nombre):
    patron = rf'\*\*{nombre}\*\*:?(.*?)(?=\*\*[A-Z]|$)'
    match = re.search(patron, contenido, re.DOTALL | re.IGNORECASE)
    if match:
        return limpiar_texto(match.group(1).strip())
    return ""

# ================= CONTENIDO LOCAL =================
def contenido_local(tema):
    return {
        'introduccion': f"Este informe analiza {tema} desde una perspectiva académica.",
        'objetivos': f"Analizar {tema} y comprender su impacto.",
        'marco_teorico': f"Se fundamenta en teorías relacionadas con {tema}.",
        'metodologia': "Enfoque descriptivo del estudio.",
        'desarrollo': f"Se desarrolla el tema {tema} con análisis crítico.",
        'conclusiones': f"{tema} es relevante en el contexto actual.",
        'recomendaciones': "Se recomienda profundizar en el tema."
    }

# ================= RUTAS =================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        tema = datos.get('tema', '')
        nombre = datos.get('nombre', 'Estudiante')

        if not tema:
            return jsonify({'success': False, 'error': 'Tema requerido'}), 400

        # ================= IA =================
        secciones = None
        if GROQ_API_KEY:
            try:
                prompt = f"""Genera un informe académico sobre: {tema}

**INTRODUCCIÓN**
**OBJETIVOS**
**MARCO TEÓRICO**
**METODOLOGÍA**
**DESARROLLO**
**CONCLUSIONES**
**RECOMENDACIONES**
"""

                headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
                data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500
                }

                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=40
                )

                if r.status_code == 200:
                    contenido = r.json()['choices'][0]['message']['content']

                    secciones = {
                        'introduccion': extraer_seccion(contenido, 'INTRODUCCIÓN'),
                        'objetivos': extraer_seccion(contenido, 'OBJETIVOS'),
                        'marco_teorico': extraer_seccion(contenido, 'MARCO TEÓRICO'),
                        'metodologia': extraer_seccion(contenido, 'METODOLOGÍA'),
                        'desarrollo': extraer_seccion(contenido, 'DESARROLLO'),
                        'conclusiones': extraer_seccion(contenido, 'CONCLUSIONES'),
                        'recomendaciones': extraer_seccion(contenido, 'RECOMENDACIONES')
                    }
            except:
                pass

        if not secciones:
            secciones = contenido_local(tema)

        # ================= PDF =================
        filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
        path = os.path.join('informes_generados', filename)

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='Titulo',
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=10
        ))

        styles.add(ParagraphStyle(
            name='TextoPro',
            parent=styles['Normal'],
            alignment=TA_JUSTIFY,
            leading=16
        ))

        story = []

        # PORTADA
        story.append(Spacer(1, 100))
        story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(tema.upper(), styles['Normal']))
        story.append(Spacer(1, 40))
        story.append(Paragraph(f"Autor: {nombre}", styles['Normal']))
        story.append(PageBreak())

        # ÍNDICE
        story.append(Paragraph("ÍNDICE", styles['Titulo']))
        indice = [
            "1. INTRODUCCIÓN .......... 2",
            "2. OBJETIVOS ............. 3",
            "3. MARCO TEÓRICO ......... 4",
            "4. METODOLOGÍA ........... 5",
            "5. DESARROLLO ............ 6",
            "6. CONCLUSIONES .......... 7",
            "7. RECOMENDACIONES ....... 8",
        ]
        for i in indice:
            story.append(Paragraph(i, styles['Normal']))
        story.append(PageBreak())

        # SECCIONES
        for i, (titulo, key) in enumerate([
            ("INTRODUCCIÓN", "introduccion"),
            ("OBJETIVOS", "objetivos"),
            ("MARCO TEÓRICO", "marco_teorico"),
            ("METODOLOGÍA", "metodologia"),
            ("DESARROLLO", "desarrollo"),
            ("CONCLUSIONES", "conclusiones"),
            ("RECOMENDACIONES", "recomendaciones"),
        ], 1):
            story.append(Paragraph(f"{i}. {titulo}", styles['Titulo']))
            story.append(Paragraph(secciones[key], styles['TextoPro']))
            story.append(PageBreak())

        doc.build(story)

        return jsonify({
            'success': True,
            'download_url': f'/descargar/{filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join('informes_generados', filename), as_attachment=True)

if __name__ == '__main__':
    app.run()
