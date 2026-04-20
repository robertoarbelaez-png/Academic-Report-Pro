from flask import Flask, render_template, request, jsonify, send_file
import os, uuid, requests, json, html
from werkzeug.utils import secure_filename

from reportlab.platypus import (
    Paragraph, Spacer, PageBreak,
    BaseDocTemplate, Frame, PageTemplate, TableOfContents
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -------- CONTENIDO LOCAL --------
def contenido_local(tema):
    return {
        "introduccion": f"Este informe analiza {tema}.",
        "objetivos": "Analizar el tema.",
        "marco_teorico": "Bases teóricas.",
        "metodologia": "Enfoque descriptivo.",
        "desarrollo": f"Análisis de {tema}.",
        "conclusiones": "Conclusiones del tema.",
        "recomendaciones": "Recomendaciones.",
        "referencias": "Fuentes académicas."
    }

# -------- IA --------
def generar_ia(tema):
    if not GROQ_API_KEY:
        return None

    try:
        prompt = f"""
Genera un informe académico sobre: "{tema}"

Responde SOLO en JSON:

{{
  "introduccion": "",
  "objetivos": "",
  "marco_teorico": "",
  "metodologia": "",
  "desarrollo": "",
  "conclusiones": "",
  "recomendaciones": "",
  "referencias": ""
}}
"""

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }

        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)

        if res.status_code != 200:
            return None

        texto = res.json()['choices'][0]['message']['content'].strip()

        if texto.startswith("```"):
            texto = texto.replace("```json", "").replace("```", "").strip()

        return json.loads(texto)

    except:
        return None

# -------- SEGURIDAD --------
def asegurar_secciones(secciones, tema):
    fallback = contenido_local(tema)
    for key in fallback:
        if key not in secciones or not str(secciones[key]).strip():
            secciones[key] = fallback[key]
    return secciones

# -------- LIMPIAR --------
def limpiar(texto):
    texto = html.escape(texto)
    return texto.replace("\n", "<br/>")

# -------- DOC TEMPLATE --------
class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height)
        template = PageTemplate(id='normal', frames=frame, onPage=self.add_page_number)
        self.addPageTemplates([template])

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            if flowable.style.name == 'Heading1':
                self.notify('TOCEntry', (0, flowable.getPlainText(), self.page))

    def add_page_number(self, canvas, doc):
        canvas.drawRightString(200*mm, 20, str(doc.page))

# -------- PDF --------
def generar_pdf(datos, secciones):
    filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
    path = os.path.join('informes_generados', filename)

    doc = MyDocTemplate(path)
    styles = getSampleStyleSheet()
    story = []

    # PORTADA
    story.append(Spacer(1, 200))
    story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
    story.append(Spacer(1, 40))
    story.append(Paragraph(datos['tema'], styles['Heading1']))
    story.append(Spacer(1, 40))
    story.append(Paragraph(f"Autor: {datos['nombre']}", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Institución: ________", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Fecha: ________", styles['Normal']))
    story.append(PageBreak())

    # ÍNDICE
    story.append(Paragraph("ÍNDICE", styles['Title']))
    story.append(Spacer(1, 20))

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(name='TOCHeading1', fontSize=12, leftIndent=20)
    ]
    story.append(toc)
    story.append(PageBreak())

    # SECCIONES
    titulos = {
        "introduccion": "1. INTRODUCCIÓN",
        "objetivos": "2. OBJETIVOS",
        "marco_teorico": "3. MARCO TEÓRICO",
        "metodologia": "4. METODOLOGÍA",
        "desarrollo": "5. DESARROLLO",
        "conclusiones": "6. CONCLUSIONES",
        "recomendaciones": "7. RECOMENDACIONES",
        "referencias": "8. REFERENCIAS"
    }

    for key, titulo in titulos.items():
        story.append(Paragraph(titulo, styles['Heading1']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(limpiar(secciones.get(key, "")), styles['Normal']))
        story.append(Spacer(1, 20))

    doc.build(story)
    return filename

# -------- RUTAS --------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    datos = request.json
    tema = datos.get('tema', '').strip()
    modo = datos.get('modo', 'auto')

    if len(tema) < 3:
        return jsonify({'success': False, 'error': 'Tema inválido'})

    nombre = datos.get('nombre', 'Estudiante')

    # 🔥 MODOS
    if modo == "manual":
        secciones = {
            "introduccion": datos.get('intro', ''),
            "objetivos": datos.get('obj', ''),
            "marco_teorico": "",
            "metodologia": "",
            "desarrollo": datos.get('des', ''),
            "conclusiones": "",
            "recomendaciones": "",
            "referencias": ""
        }
    else:
        secciones = generar_ia(tema)

    if not secciones:
        secciones = contenido_local(tema)
    else:
        secciones = asegurar_secciones(secciones, tema)

    filename = generar_pdf({'tema': tema, 'nombre': nombre}, secciones)

    return jsonify({
        "success": True,
        "download_url": f"/descargar/{filename}"
    })

@app.route('/descargar/<filename>')
def descargar(filename):
    path = os.path.join('informes_generados', secure_filename(filename))
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
