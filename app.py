import os
import io
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS  # ← ADICIONAR ESTA LINHA
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter

# ======================================================
# CONFIGURAÇÃO BÁSICA
# ======================================================

app = Flask(__name__)
CORS(app)  # ← ADICIONAR ESTA LINHA - Permite requisições de qualquer origem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_ORIGINAL = os.path.join(BASE_DIR, "backend", "Guia_Petrobras_base.pdf")

if not os.path.exists(PDF_ORIGINAL):
    raise FileNotFoundError(f"PDF não encontrado: {PDF_ORIGINAL}")

# ======================================================
# MAPEAMENTO DOS CAMPOS (PDF A4 – 595 x 842)
# ======================================================

CAMPOS = {
    "numero_carteira":           (56, 618),
    "beneficiario_nome":         (65, 581),
    "atendimento_rn":            (463.5, 618),
    "nome_profissional":         (65, 480),
    "conselho":                  (269, 476),
    "numero_conselho":           (324, 476),
    "uf_conselho":               (474, 476),
    "cbo":                       (504.5, 476),
    "indicacao_acidente":        (119.4, 420),
    "data_atendimento":          (54.5, 370),
    "tabela":                    (265, 370),
    "codigo_procedimento":       (329, 370),
    "valor_procedimento":        (460, 370),
    "observacao":                (110, 335),
}

# ======================================================
# ROTAS
# ======================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        campos_quadriculados = [
            "atendimento_rn",
            "codigo_operadora", "indicacao_acidente", "tabela"
        ]

        for campo, (x, y) in CAMPOS.items():
            valor = dados.get(campo, "").strip()
            if not valor or campo == "observacao":
                continue

        # Número da Carteira
            if campo == "numero_carteira":
                c.setFont("Helvetica", 12)

                # Espaçamento específico entre cada dígito
                espacamentos = [
                    12.3,  # 1º → 2º
                    11.2,  # 2º → 3º
                    11.2,  # 3º → 4º
                    11.2,  # 4º → 5º
                    10.8,  # 5º → 6º
                    11.2,  # 6º → 7º
                    11.2,  # 7º → 8º
                    11.2,  # ...
                    11.2,
                    11.2,
                    11.2,
                    11.2,
                    11.2
                ]

                x_atual = x

                for i, char in enumerate(valor):
                    c.drawString(x_atual, y, char)

                    # Usa o espaçamento correspondente ou um padrão
                    if i < len(espacamentos):
                        x_atual += espacamentos[i]
                    else:
                        x_atual += 12
                        

            # Conselho (CRM)
            elif campo == "conselho":
                c.setFont("Helvetica", 11.5)
                espacamento = 11.1
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Número do Conselho
            elif campo == "numero_conselho":
                c.setFont("Helvetica", 12)
                espacamento = 10.3
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # UF
            elif campo == "uf_conselho":
                c.setFont("Helvetica", 10.8)
                espacamento = 11
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # CBO
            elif campo == "cbo":
                c.setFont("Helvetica", 10)
                espacamento = 9
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # ==================================================
            # DATA DO ATENDIMENTO – DD MM AAAA (ROBUSTO)
            # ==================================================
            elif campo == "data_atendimento":
                dia = mes = ano = ""

                try:
                    data_obj = datetime.strptime(valor, "%Y-%m-%d")
                except ValueError:
                    try:
                        data_obj = datetime.strptime(valor, "%d/%m/%Y")
                    except ValueError:
                        data_obj = None

                if data_obj:
                    dia = data_obj.strftime("%d")
                    mes = data_obj.strftime("%m")
                    ano = data_obj.strftime("%Y")

                c.setFont("Helvetica", 12)

                # Espaçamento entre os dígitos
                espacamento_digito = 11

                # Espaçamento entre blocos (DD | MM | AAAA)
                espacamento_bloco = 17

                x_atual = x

                # DIA
                for i, char in enumerate(dia):
                    c.drawString(x_atual, y, char)
                    if i < len(dia) - 1:
                        x_atual += espacamento_digito

                x_atual += espacamento_bloco

                # MÊS
                for i, char in enumerate(mes):
                    c.drawString(x_atual, y, char)
                    if i < len(mes) - 1:
                        x_atual += espacamento_digito

                x_atual += espacamento_bloco

                # ANO
                for i, char in enumerate(ano):
                    c.drawString(x_atual, y, char)
                    if i < len(ano) - 1:
                        x_atual += espacamento_digito


            # Tabela – 3 caracteres
            elif campo == "tabela":
                c.setFont("Helvetica", 12)
                espacamento = 11.5
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Código do Procedimento – 9 caracteres
            elif campo == "codigo_procedimento":
                c.setFont("Helvetica", 12)

                # Espaçamento ENTRE os dígitos (8 espaços para 9 caracteres)
                espacamentos = [11.5, 11.5, 10.9, 11.3, 11.1, 10.9, 11.5, 11.5]

                x_atual = x

                for i, char in enumerate(valor):
                    c.drawString(x_atual, y, char)

                    # Aplica o espaçamento correspondente
                    if i < len(espacamentos):
                        x_atual += espacamentos[i]


            # Valor do Procedimento – 7 caracteres
            elif campo == "valor_procedimento":
                c.setFont("Helvetica", 12)

                # Espaçamento ENTRE cada caractere (ajuste individual)
                # Formato: R$ 112 00
                espacamentos = [
                    12.5,  # R → $
                    12.5,     # $ → (espaço)
                    11.5,  # (espaço) → 1
                    12.5,  # 1 → 1
                    12.5,  # 1 → 2
                    12.5,  # 2 → (espaço)
                    12.5   # (espaço) → 0
                ]

                x_atual = x

                for i, char in enumerate(valor):
                    c.drawString(x_atual, y, char)
                    
                    # Aplica o espaçamento correspondente (se ainda houver)
                    if i < len(espacamentos):
                        x_atual += espacamentos[i]


            # Campos quadriculados padrão
            elif campo in campos_quadriculados:
                c.setFont("Helvetica", 13)
                espacamento = 11.1
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Texto livre
            else:
                c.setFont("Helvetica", 14)
                c.drawString(x, y, valor)

        # ==================================================
        # OBSERVAÇÃO – TEXTO LONGO COM QUEBRA MANUAL
        # ==================================================

        obs = dados.get("observacao", "").strip()
        if obs:
            x_obs, y_obs = CAMPOS["observacao"]
            largura_max = 470
            c.setFont("Helvetica", 9)

            palavras = obs.split()
            linha_atual = ""
            y_atual = y_obs
            espacamento_linha = 15

            for palavra in palavras:
                teste = f"{linha_atual} {palavra}".strip()
                if c.stringWidth(teste, "Helvetica", 9) <= largura_max:
                    linha_atual = teste
                else:
                    c.drawString(x_obs, y_atual, linha_atual)
                    y_atual -= espacamento_linha
                    linha_atual = palavra

            if linha_atual:
                c.drawString(x_obs, y_atual, linha_atual)

        # ==================================================
        # FINALIZAÇÃO E MERGE COM PDF BASE
        # ==================================================

        c.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        base = PdfReader(PDF_ORIGINAL)

        writer = PdfWriter()
        page = base.pages[0]
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

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