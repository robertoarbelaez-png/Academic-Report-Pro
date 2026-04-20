from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
from datetime import datetime
import requests
import re
import html
from werkzeug.utils import secure_filename

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# API KEY (opcional)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ---------- UTILIDADES ----------

def validar_texto(texto, minimo=3):
    return isinstance(texto, str) and len(texto.strip()) >= minimo

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = html.escape(texto)
    texto = texto.replace('\n', '<br/>')
    return texto

def contenido_local(tema):
    return f"""
Introducción:<br/>
Este informe trata sobre {tema}. Se analiza su impacto y relevancia actual.<br/><br/>

Desarrollo:<br/>
El tema {tema} es importante en la actualidad debido a su influencia en la sociedad.<br/><br/>

Conclusiones:<br/>
Se concluye que {tema} es un aspecto clave que requiere estudio continuo.
"""

# ---------- PDF ----------

def generar_pdf(datos, contenido):
    filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
    path = os.path.join('informes_generados', filename)

    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"<b>Tema:</b> {datos['tema']}", styles['Normal']))
    story.append(Paragraph(f"<b>Nombre:</b> {datos['nombre']}", styles['Normal']))
    story.append(Spacer(1, 20))

    story.append(Paragraph(limpiar_texto(contenido), styles['Normal']))

    doc.build(story)

    return filename, path

# ---------- RUTAS ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        tema = datos.get('tema', '').strip()

        if not validar_texto(tema):
            return jsonify({'success': False, 'error': 'Tema inválido'}), 400

        nombre = datos.get('nombre', 'Estudiante')

        contenido = ""

        # 🔥 IA (si hay API)
        if GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": f"Escribe un informe sobre {tema}"}],
                    "max_tokens": 2000
                }

                res = requests.post(GROQ_URL, headers=headers, json=data, timeout=30)

                if res.status_code == 200:
                    contenido = res.json()['choices'][0]['message']['content']
                else:
                    contenido = contenido_local(tema)

            except:
                contenido = contenido_local(tema)
        else:
            contenido = contenido_local(tema)

        filename, path = generar_pdf({'tema': tema, 'nombre': nombre}, contenido)

        return jsonify({
            'success': True,
            'download_url': f'/descargar/{filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/descargar/<filename>')
def descargar(filename):
    safe = secure_filename(filename)
    path = os.path.join('informes_generados', safe)

    if not os.path.exists(path):
        return "No existe", 404

    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
