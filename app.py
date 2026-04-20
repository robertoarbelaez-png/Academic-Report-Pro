from flask import Flask, render_template, request, jsonify, send_file
import os, uuid, requests, json, html
from werkzeug.utils import secure_filename

from reportlab.platypus import (
    Paragraph, Spacer, PageBreak,
    BaseDocTemplate, Frame, PageTemplate
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -------- CONTENIDO RÁPIDO --------
def contenido_local(tema):
    return {
        "introduccion": f"Este informe analiza {tema} desde una perspectiva académica.",
        "objetivos": "Analizar el tema y comprender su impacto.",
        "marco_teorico": "Se basa en conceptos teóricos relevantes.",
        "metodologia": "Se utiliza un enfoque descriptivo.",
        "desarrollo": f"Se desarrolla el tema {tema} con análisis crítico.",
        "conclusiones": "Se concluye que el tema es relevante.",
        "recomendaciones": "Se recomienda profundizar en el estudio.",
        "referencias": "Fuentes académicas generales."
    }

# -------- IA (OPCIONAL) --------
def generar_ia(tema):
    if not GROQ_API_KEY:
        return None

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": f"Genera un informe sobre {tema} en JSON"}],
            "max_tokens": 1200
        }

        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=20)

        if res.status_code != 200:
            return None

        texto = res.json()['choices'][0]['message']['content'].strip()
        return json.loads(texto)

    except:
        return None

# -------- LIMPIAR --------
def limpiar(texto):
    texto = html.escape(texto)
    return texto.replace("\n", "<br/>")

# -------- DOC TEMPLATE --------
class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40)
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

    estilo_normal = ParagraphStyle(
        name='TextoAPA',
        fontSize=11,
        leading=16,
        firstLineIndent=20
    )

    estilo_titulo = ParagraphStyle(
        name='TituloPro',
        fontSize=13,
        spaceAfter=12
    )

    story = []

    # PORTADA
    story.append(Spacer(1, 200))
    story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
    story.append(Spacer(1, 40))
    story.append(Paragraph(datos['tema'], styles['Heading1']))
    story.append(Spacer(1, 40))
    story.append(Paragraph(f"Autor: {datos['nombre']}", styles['Normal']))
    story.append(PageBreak())

    # ÍNDICE
    story.append(Paragraph("ÍNDICE", styles['Title']))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle(name='TOC', fontSize=11, leftIndent=20)]
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(PageBreak())

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
        story.append(Paragraph(titulo, estilo_titulo))
        story.append(Spacer(1, 12))
        story.append(Paragraph(limpiar(secciones.get(key, "")), estilo_normal))
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
    nombre = datos.get('nombre', 'Estudiante')

    if len(tema) < 3:
        return jsonify({'success': False})

    # ⚡ SIEMPRE RÁPIDO
    secciones = contenido_local(tema)

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
