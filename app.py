import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
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

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        largura, altura = A4

        # =============================
        # EXEMPLO DE CAMPOS (AJUSTE AQUI)
        # =============================

        c.setFont("Helvetica", 10)

        campos = [
            ("Beneficiário:", dados.get("beneficiario_nome", ""), 50, altura - 80),
            ("Carteira:", dados.get("numero_carteira", ""), 50, altura - 110),
            ("Profissional:", dados.get("nome_profissional", ""), 50, altura - 140),
            ("Data Atendimento:", dados.get("data_atendimento", ""), 50, altura - 170),
            ("Procedimento:", dados.get("codigo_procedimento", ""), 50, altura - 200),
            ("Valor:", dados.get("valor_procedimento", ""), 50, altura - 230),
        ]

        for label, valor, x, y in campos:
            c.drawString(x, y, f"{label} {valor}")

        c.showPage()
        c.save()

        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="Guia_Petrobras.pdf",
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
