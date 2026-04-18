import os
import re
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from flask import Flask, render_template, request, jsonify, send_from_directory, abort

import bleach

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# ---------------------------
# App + config
# ---------------------------
app = Flask(__name__)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "informes_generados")
os.makedirs(OUTPUT_DIR, exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

MAX_TEMA_LEN = 180
MAX_TEXTO_COMPLETO_LEN = 4000

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("academic-report-pro")

logger.info("Iniciando aplicación")
logger.info("Groq configurado: %s", "SÍ" if GROQ_API_KEY else "NO")


# ---------------------------
# Normas
# ---------------------------
NORMAS_CONFIG = {
    "apa7": {"nombre": "APA 7ª Edición", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 12, "interlineado": 24, "sangria": 36},
    "apa6": {"nombre": "APA 6ª Edición", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 12, "interlineado": 24, "sangria": 36},
    "icontec": {"nombre": "ICONTEC (Colombia)", "margen_superior": 85, "margen_inferior": 85, "margen_izquierdo": 113, "margen_derecho": 85, "fuente": "Helvetica", "tamaño": 12, "interlineado": 18, "sangria": 0},
    "vancouver": {"nombre": "Vancouver", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 11, "interlineado": 16, "sangria": 0},
    "chicago": {"nombre": "Chicago", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 12, "interlineado": 18, "sangria": 36},
    "harvard": {"nombre": "Harvard", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 12, "interlineado": 18, "sangria": 36},
    "mla": {"nombre": "MLA 9ª Edición", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 12, "interlineado": 24, "sangria": 36},
    "ieee": {"nombre": "IEEE", "margen_superior": 72, "margen_inferior": 72, "margen_izquierdo": 72, "margen_derecho": 72, "fuente": "Times-Roman", "tamaño": 10, "interlineado": 12, "sangria": 0},
}

# Claves estables (sin tildes, sin espacios)
SECCIONES_KEYS = [
    "introduccion",
    "objetivos",
    "marco_teorico",
    "metodologia",
    "desarrollo",
    "conclusiones",
    "recomendaciones",
]


# ---------------------------
# HTTP session (retries)
# ---------------------------
def build_http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("POST", "GET"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


HTTP = build_http_session()


# ---------------------------
# Sanitización segura (para ReportLab Paragraph)
# ---------------------------
ALLOWED_TAGS = ["b", "br", "i", "u"]
ALLOWED_ATTRS: Dict[str, List[str]] = {}


def limpiar_texto(texto: Any) -> str:
    if not texto:
        return ""

    if isinstance(texto, bytes):
        texto = texto.decode("utf-8", errors="ignore")
    else:
        texto = str(texto)

    reemplazos = {
        "\xa0": " ",
        "\xad": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)

    # Correcciones puntuales
    texto = texto.replace("INFORMÉ", "INFORME")
    texto = texto.replace("Conclusions", "CONCLUSIONES")
    texto = texto.replace("CONCLUSIONS", "CONCLUSIONES")

    # Saltos de línea a <br/>
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    texto = texto.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")

    # Sanitizar: permite solo tags seguros
    texto = bleach.clean(texto, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return texto


# ---------------------------
# Fallback local
# ---------------------------
def generar_contenido_local_generico(tipo: str, tema: str) -> str:
    tema_limpio = tema or "el tema de investigación"

    contenidos = {
        "introduccion": f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia en el contexto actual.<br/><br/>
La investigación se justifica por la necesidad de generar evidencia empírica que contribuya al conocimiento existente.<br/><br/>
Las preguntas que guían esta investigación son: ¿Cuáles son los principales aspectos relacionados con {tema_limpio}? ¿Qué estrategias pueden implementarse?""",
        "objetivos": f"""<b>Objetivo General</b><br/><br/>Analizar los principales aspectos relacionados con {tema_limpio} en el contexto actual.<br/><br/><br/>
<b>Objetivos Específicos</b><br/><br/>
1. Identificar los factores clave asociados a {tema_limpio}.<br/>
2. Describir las principales características y tendencias actuales.<br/>
3. Analizar las implicaciones prácticas y teóricas de los hallazgos.<br/>
4. Proponer recomendaciones basadas en el análisis realizado.""",
        "marco_teorico": f"""<b>Conceptos clave</b><br/><br/>
Para comprender adecuadamente {tema_limpio}, es necesario definir los conceptos fundamentales que lo sustentan.<br/><br/>
<b>Bases teóricas</b><br/><br/>
Las teorías existentes proporcionan un marco conceptual sólido para el análisis de {tema_limpio}.<br/><br/>
<b>Estado del arte</b><br/><br/>
Investigaciones recientes han profundizado en aspectos específicos de {tema_limpio}.""",
        "metodologia": f"""<b>Enfoque</b><br/><br/>La investigación adopta un enfoque mixto.<br/><br/>
<b>Población y muestra</b><br/><br/>Se seleccionó una muestra representativa de 120 participantes.<br/><br/>
<b>Instrumentos</b><br/><br/>Cuestionarios estructurados, entrevistas semiestructuradas.<br/><br/>
<b>Procedimiento</b><br/><br/>El estudio se desarrolló en tres fases: diseño, recolección y análisis.""",
        "desarrollo": f"""<b>Resultados obtenidos</b><br/><br/>
El 75% de los participantes reportó afectaciones relacionadas con {tema_limpio}.<br/><br/>
<b>Análisis de resultados</b><br/><br/>
Los hallazgos indican que existen múltiples factores que inciden en {tema_limpio}.<br/><br/>
<b>Discusión</b><br/><br/>
Los resultados se alinean con lo reportado en la literatura especializada.""",
        "conclusiones": f"""1. El análisis realizado permite identificar los principales aspectos relacionados con {tema_limpio}.<br/>
2. Los hallazgos confirman la importancia de abordar este tema.<br/>
3. Se requiere mayor investigación para profundizar en aspectos específicos.<br/>
4. Las recomendaciones propuestas constituyen una base para futuras intervenciones.<br/>
5. Este estudio contribuye al conocimiento existente.""",
        "recomendaciones": f"""<b>Para la institución</b><br/><br/>
1. Fortalecer las líneas de investigación relacionadas con {tema_limpio}.<br/><br/>
<b>Para los profesionales</b><br/><br/>
2. Aplicar los hallazgos en contextos prácticos.<br/><br/>
<b>Para futuros estudios</b><br/><br/>
3. Ampliar la muestra y el alcance geográfico.""",
    }
    return contenidos.get(tipo, "Contenido en desarrollo.")


# ---------------------------
# Referencias
# ---------------------------
def obtener_referencias(
    tema: str,
    referencias_ia: Optional[List[str]] = None,
    referencias_manuales: str = "",
    modo_referencias: str = "auto",
) -> List[str]:
    modo_referencias = (modo_referencias or "auto").strip().lower()

    if modo_referencias == "manual":
        refs = [r.strip() for r in (referencias_manuales or "").split("\n") if r.strip()]
        return refs if refs else ["Referencia no especificada"]

    if modo_referencias == "mixto":
        refs: List[str] = []
        if referencias_manuales:
            refs.extend([r.strip() for r in referencias_manuales.split("\n") if r.strip()])
        if referencias_ia:
            refs.extend([r.strip() for r in referencias_ia if r and r.strip()])
        return list(dict.fromkeys(refs))[:10] if refs else ["Referencia no especificada"]

    # auto
    if referencias_ia:
        cleaned = [r.strip() for r in referencias_ia if r and r.strip()]
        if cleaned:
            return cleaned[:8]

    tema_lower = (tema or "").lower()
    if any(k in tema_lower for k in ["tecnología", "tecnologia", "digital", "agro"]):
        return [
            "Bharadwaj, A. (2000). MIS Quarterly, 24(1), 169-196.",
            "Rogers, E. M. (2003). Diffusion of innovations. Free Press.",
            "Castells, M. (2010). The rise of the network society. Wiley-Blackwell.",
        ]
    if any(k in tema_lower for k in ["educación", "educacion", "aprendizaje"]):
        return [
            "Siemens, G. (2005). Connectivism. International Journal of Instructional Technology.",
            "Coll, C. (2018). Psicología de la educación virtual. UOC.",
            "García Aretio, L. (2022). Educación a distancia y virtual. UNED.",
        ]
    return [
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla.",
    ]


# ---------------------------
# Groq: pedir JSON (robusto)
# ---------------------------
def groq_generar_secciones_json(tema: str) -> Dict[str, str]:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY no configurada")

    prompt = f"""
Devuélveme SOLO un JSON válido (sin markdown, sin ```), en español, con EXACTAMENTE estas claves:
{", ".join(SECCIONES_KEYS)}.

Tema: "{tema}"

Requisitos:
- objetivos: incluir 1 objetivo general y 4 objetivos específicos.
- conclusiones: 5 puntos concretos.
- recomendaciones: 3 a 4 puntos.
- No uses la palabra "Conclusions".
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4500,
        "temperature": 0.6,
    }

    resp = HTTP.post(GROQ_URL, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(f"Groq error HTTP {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # Extraer JSON si el modelo mete texto adicional
    json_text = content
    if not content.startswith("{"):
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            json_text = m.group(0)

    parsed = json.loads(json_text)
    if not isinstance(parsed, dict):
        raise RuntimeError("Respuesta de IA no es un JSON objeto")

    out: Dict[str, str] = {}
    for k in SECCIONES_KEYS:
        out[k] = limpiar_texto(parsed.get(k, ""))

    return out


# ---------------------------
# PDF Generator
# ---------------------------
class GeneradorPDF:
    def crear_estilos(self, config_norma: Dict[str, Any]):
        styles = getSampleStyleSheet()

        styles.add(
            ParagraphStyle(
                name="TextoJustificado",
                parent=styles["Normal"],
                alignment=TA_JUSTIFY,
                fontSize=config_norma["tamaño"],
                fontName=config_norma["fuente"],
                spaceAfter=12,
                leading=config_norma["interlineado"],
                leftIndent=config_norma["sangria"],
            )
        )

        styles.add(
            ParagraphStyle(
                name="Titulo1",
                parent=styles["Heading1"],
                fontSize=config_norma["tamaño"] + 2,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor("#1a365d"),
                spaceBefore=20,
                spaceAfter=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="TituloPortada",
                parent=styles["Title"],
                fontSize=22,
                alignment=TA_CENTER,
                spaceAfter=16,
                textColor=colors.HexColor("#1a365d"),
            )
        )

        styles.add(
            ParagraphStyle(
                name="TemaPortada",
                parent=styles["Title"],
                fontSize=15,
                alignment=TA_CENTER,
                spaceAfter=10,
                textColor=colors.HexColor("#0f172a"),
            )
        )

        return styles

    def generar_pdf(
        self,
        datos_usuario: Dict[str, Any],
        secciones: Optional[Dict[str, str]] = None,
        referencias_ia: Optional[List[str]] = None,
    ):
        nombre = (datos_usuario.get("nombre") or "Estudiante").strip() or "Estudiante"
        tema = (datos_usuario.get("tema") or "Tema de Investigación").strip() or "Tema de Investigación"
        asignatura = (datos_usuario.get("asignatura") or "Asignatura").strip() or "Asignatura"
        profesor = (datos_usuario.get("profesor") or "Docente").strip() or "Docente"
        institucion = (datos_usuario.get("institucion") or "Institución Educativa").strip() or "Institución Educativa"

        fecha_entrega = (datos_usuario.get("fecha_entrega") or "").strip()
        if not fecha_entrega:
            fecha_entrega = datetime.now().strftime("%d/%m/%Y")

        norma = (datos_usuario.get("norma") or "apa7").strip().lower()
        modo_referencias = (datos_usuario.get("modo_referencias") or "auto").strip().lower()
        referencias_manuales = datos_usuario.get("referencias_manuales") or ""

        config_norma = NORMAS_CONFIG.get(norma, NORMAS_CONFIG["apa7"])
        logger.info("Aplicando norma: %s", config_norma["nombre"])

        if secciones and isinstance(secciones, dict):
            sec = {k: limpiar_texto(secciones.get(k, "")) for k in SECCIONES_KEYS}
            logger.info("Usando secciones generadas por IA")
        else:
            sec = {k: limpiar_texto(generar_contenido_local_generico(k, tema)) for k in SECCIONES_KEYS}
            logger.warning("Usando contenido local genérico")

        referencias = obtener_referencias(
            tema=tema,
            referencias_ia=referencias_ia,
            referencias_manuales=referencias_manuales,
            modo_referencias=modo_referencias,
        )

        filename = f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)

        styles = self.crear_estilos(config_norma)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=config_norma["margen_derecho"],
            leftMargin=config_norma["margen_izquierdo"],
            topMargin=config_norma["margen_superior"],
            bottomMargin=config_norma["margen_inferior"],
        )

        story = []

        # Portada
        story.append(Spacer(1, 1.2 * inch))
        story.append(Paragraph("INFORME ACADÉMICO", styles["TituloPortada"]))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(limpiar_texto(tema), styles["TemaPortada"]))
        story.append(Spacer(1, 0.9 * inch))

        # Datos (sin HTML permitido)
        safe = lambda s: bleach.clean(str(s or ""), tags=[], strip=True)

        story.append(Paragraph(f"<b>Presentado por:</b> {safe(nombre)}", styles["TextoJustificado"]))
        story.append(Paragraph(f"<b>Asignatura:</b> {safe(asignatura)}", styles["TextoJustificado"]))
        story.append(Paragraph(f"<b>Docente:</b> {safe(profesor)}", styles["TextoJustificado"]))
        story.append(Paragraph(f"<b>Institución:</b> {safe(institucion)}", styles["TextoJustificado"]))
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {safe(fecha_entrega)}", styles["TextoJustificado"]))
        story.append(Paragraph(f"<b>Norma aplicada:</b> {config_norma['nombre']}", styles["TextoJustificado"]))
        story.append(PageBreak())

        # Índice simple
        story.append(Paragraph("ÍNDICE", styles["Titulo1"]))
        indices = [
            "1. INTRODUCCIÓN",
            "2. OBJETIVOS",
            "3. MARCO TEÓRICO",
            "4. METODOLOGÍA",
            "5. DESARROLLO",
            "6. CONCLUSIONES",
            "7. RECOMENDACIONES",
            "8. REFERENCIAS",
        ]
        for idx in indices:
            story.append(Paragraph(f"• {idx}", styles["TextoJustificado"]))
        story.append(PageBreak())

        # Secciones
        story.append(Paragraph("1. INTRODUCCIÓN", styles["Titulo1"]))
        story.append(Paragraph(sec["introduccion"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("2. OBJETIVOS", styles["Titulo1"]))
        story.append(Paragraph(sec["objetivos"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("3. MARCO TEÓRICO", styles["Titulo1"]))
        story.append(Paragraph(sec["marco_teorico"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("4. METODOLOGÍA", styles["Titulo1"]))
        story.append(Paragraph(sec["metodologia"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("5. DESARROLLO", styles["Titulo1"]))
        story.append(Paragraph(sec["desarrollo"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("6. CONCLUSIONES", styles["Titulo1"]))
        story.append(Paragraph(sec["conclusiones"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("7. RECOMENDACIONES", styles["Titulo1"]))
        story.append(Paragraph(sec["recomendaciones"], styles["TextoJustificado"]))
        story.append(PageBreak())

        story.append(Paragraph("8. REFERENCIAS", styles["Titulo1"]))
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {safe(ref)}", styles["TextoJustificado"]))
            story.append(Spacer(1, 0.08 * inch))

        doc.build(story)
        logger.info("PDF generado: %s", filename)

        return filename, filepath


generador = GeneradorPDF()


# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


def _validate_filename(filename: str) -> bool:
    return bool(re.fullmatch(r"informe_\d{8}_\d{6}_[0-9a-f]{4}\.pdf", filename))


@app.route("/generar", methods=["POST"])
def generar():
    try:
        datos = request.get_json(force=True, silent=False) or {}

        modo = (datos.get("modo") or "auto").strip().lower()
        tema = (datos.get("tema") or "").strip()
        texto_completo = (datos.get("texto_completo") or "").strip()

        modo_referencias = (datos.get("modo_referencias") or "auto").strip().lower()
        referencias_manuales = (datos.get("referencias_manuales") or "").strip()

        if len(tema) > MAX_TEMA_LEN:
            return jsonify({"success": False, "error": f"El tema es demasiado largo (máx {MAX_TEMA_LEN} caracteres)."}), 400
        if len(texto_completo) > MAX_TEXTO_COMPLETO_LEN:
            return jsonify({"success": False, "error": f"El texto completo es demasiado largo (máx {MAX_TEXTO_COMPLETO_LEN} caracteres)."}), 400

        # Modo rápido: si no envían tema, usar texto_completo como tema
        if modo == "rapido" and texto_completo and not tema:
            tema = texto_completo

        if not tema or len(tema) < 3:
            return jsonify({"success": False, "error": "Por favor ingresa un tema válido"}), 400

        # IA
        secciones_ia: Optional[Dict[str, str]] = None
        if GROQ_API_KEY:
            try:
                secciones_ia = groq_generar_secciones_json(tema)
            except Exception:
                logger.exception("Error con IA, usando fallback local")
                secciones_ia = None

        datos_usuario = {
            "nombre": datos.get("nombre", ""),
            "tema": tema,
            "asignatura": datos.get("asignatura", ""),
            "profesor": datos.get("profesor", ""),
            "institucion": datos.get("institucion", ""),
            "fecha_entrega": datos.get("fecha_entrega", ""),
            "norma": datos.get("norma", "apa7"),
            "modo_referencias": modo_referencias,
            "referencias_manuales": referencias_manuales,
        }

        filename, _ = generador.generar_pdf(datos_usuario, secciones=secciones_ia, referencias_ia=None)

        return jsonify({"success": True, "filename": filename, "download_url": f"/descargar/{filename}"})

    except Exception as e:
        logger.exception("Error en /generar")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/descargar/<filename>")
def descargar(filename: str):
    if not _validate_filename(filename):
        abort(404)

    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        abort(404)

    return send_from_directory(
        OUTPUT_DIR,
        filename,
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Servidor iniciado en puerto %s", port)
    app.run(debug=False, host="0.0.0.0", port=port)
