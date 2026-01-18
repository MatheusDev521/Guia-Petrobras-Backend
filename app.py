import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# =====================================================
# CONFIGURAÇÃO BÁSICA
# =====================================================

app = Flask(__name__)
CORS(app)  # Libera acesso externo (GitHub Pages)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_BASE = os.path.join(BASE_DIR, "backend", "Guia_Petrobras_base.pdf")

# =====================================================
# ROTA DE TESTE
# =====================================================

@app.route("/")
def home():
    return "API Guia Petrobras Online"

# =====================================================
# ROTA GERAR PDF
# =====================================================

@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    try:
        dados = request.json

        if not dados:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        # === Lê o PDF base ===
        reader = PdfReader(PDF_BASE)
        writer = PdfWriter()
        page = reader.pages[0]

        # === Overlay ===
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        # ================================
        # AQUI ENTRA O SEU MAPEAMENTO REAL
        # ================================

        c.setFont("Helvetica", 12)

        c.drawString(69, 448, dados.get("numero_carteira", ""))
        c.drawString(69, 470, dados.get("beneficiario_nome", ""))
        c.drawString(320, 380, dados.get("codigo_procedimento", ""))
        c.drawString(320, 350, dados.get("valor_procedimento", ""))

        # (continue com TODAS as suas coordenadas reais)

        c.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

        # === Saída final ===
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="GUIA_CONSULTA_PREENCHIDA.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =====================================================
# ROTA DEBUG (RÉGUA / TESTE)
# =====================================================

@app.route("/gerar-pdf-debug", methods=["POST"])
def gerar_pdf_debug():
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4

        c.setFont("Helvetica", 8)

        # Régua horizontal
        for x in range(0, int(largura), 50):
            c.drawString(x, altura - 20, str(x))

        # Régua vertical
        for y in range(0, int(altura), 50):
            c.drawString(5, y, str(y))

        c.showPage()
        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="Guia_Petrobras_DEBUG.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
