import os
import io
from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter

# ======================================================
# CONFIGURAÇÃO BÁSICA
# ======================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_ORIGINAL = os.path.join(BASE_DIR, "backend", "Guia_Petrobras_base.pdf")

if not os.path.exists(PDF_ORIGINAL):
    raise FileNotFoundError(f"PDF não encontrado: {PDF_ORIGINAL}")

# ======================================================
# MAPEAMENTO PRECISO DOS CAMPOS
# ======================================================
# PDF A4: 595 x 842 pontos (origem no canto inferior esquerdo)
# Baseado na análise do PDF real da Guia Petrobras

CAMPOS = {
    # ===== CAMPO 2 - Nº Guia no Prestador (canto superior direito) =====
    "numero_guia_prestador":  (470, 785),
    
    # ===== CAMPO 3 - Número da Guia Atribuído pela Operadora =====
    "numero_guia_operadora":  (270, 760),
    
    # ===== DADOS DO BENEFICIÁRIO =====
    # Campo 4 - Número da Carteira (quadradinhos)
    "numero_carteira":        (69, 448),
    
    # Campo 5 - Validade da Carteira (formato MM/AAAA)
    "validade_carteira":      (320, 447),
    
    # Campo 6 - Atendimento a RN (Sim ou Não)
    "atendimento_rn":         (469.5, 448),
    
    # Campo 7 - Nome do Beneficiário
    "beneficiario_nome":      (72, 410),
    
    # Campo 8 - Cartão Nacional de Saúde (CNS)
    "cns":                    (400, 690),

    # ===== DADOS DO CONTRATADO =====
    # Campo 9 - Código na Operadora
    "codigo_operadora":       (110, 650),
    
    # Campo 10 - Nome do Contratado
    "nome_contratado":        (250, 650),
    
    # Campo 11 - Código CNES
    "cnes":                   (460, 650),

    # ===== DADOS DO PROFISSIONAL =====
    # Campo 12 - Nome do Profissional Executante
    "nome_profissional":      (72, 310),
    
    # Campo 13 - Conselho Profissional
    "conselho":               (278, 308),
    
    # Campo 14 - Número no Conselho
    "numero_conselho":        (332, 308),
    
    # Campo 15 - UF
    "uf_conselho":            (479, 308),
    
    # Campo 16 - Código CBO
    "cbo":                    (509, 308),

    # ===== DADOS DO ATENDIMENTO / PROCEDIMENTO =====
    # Campo 17 - Indicação de Acidente
    "indicacao_acidente":     (131.9, 252),
    
    # Campo 18 - Data do Atendimento (DD/MM/AAAA)
    "data_atendimento":       (67, 203),
    
    # Campo 19 - Tipo de Consulta
    "tipo_consulta":          (230, 490),
    
    # Campo 20 - Tabela
    "tabela":                 (279, 203),
    
    # Campo 21 - Código do Procedimento
    "codigo_procedimento":    (337, 203),
    
    # Campo 22 - Valor do Procedimento
    "valor_procedimento":     (466, 203),

    # ===== CAMPO 23 - Observação/Justificativa =====
    "observacao":             (110, 430),
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

        # Canvas em memória
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        # ==================================================
        # DESENHAR CAMPOS
        # ==================================================

        for campo, (x, y) in CAMPOS.items():
            valor = dados.get(campo, "").strip()

            if not valor or campo == "observacao":
                continue
            
            # Campos com quadradinhos (espaçamento entre caracteres)
            campos_quadriculados = [
                "numero_guia_prestador", "numero_guia_operadora",
                "numero_carteira", "validade_carteira", "atendimento_rn",
                "codigo_operadora", "cnes", "indicacao_acidente",
                "tipo_consulta",
                "codigo_procedimento", "valor_procedimento", "cns"
            ]
            
            # Conselho (CRM)
            if campo == "conselho":
                c.setFont("Helvetica", 11.5)
                espacamento = 11.1
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Número no Conselho (quadradinhos)
            elif campo == "numero_conselho":
                c.setFont("Helvetica", 12)
                espacamento = 10.3
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # UF do Conselho (quadradinhos)
            elif campo == "uf_conselho":
                c.setFont("Helvetica", 10.8)
                espacamento = 11
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Código CBO (quadradinhos)
            elif campo == "cbo":
                c.setFont("Helvetica", 10)
                espacamento = 9
                x_atual = x
                for char in valor:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento

            # Data do Atendimento (DD/MM/AAAA) - quadradinhos
            elif campo == "data_atendimento":
                from datetime import datetime

                try:
                    # Converte de YYYY-MM-DD para formato separado
                    data_obj = datetime.strptime(valor, "%Y-%m-%d")
                    dia = data_obj.strftime("%d")
                    mes = data_obj.strftime("%m")
                    ano = data_obj.strftime("%Y")
                except ValueError:
                    # Fallback se vier em outro formato
                    dia = mes = ano = ""

                c.setFont("Helvetica", 12)
                
                # Posições específicas para cada parte da data
                # DIA (2 dígitos)
                x_atual = x
                espacamento_dia = 11.3
                for char in dia:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento_dia
                
                # Pula a barra (/)
                x_atual += 5.9
                
                # MÊS (2 dígitos)
                espacamento_mes = 11.2
                for char in mes:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento_mes
                
                # Pula a barra (/)
                x_atual += 5
                
                # ANO (4 dígitos)
                espacamento_ano = 11
                for char in ano:
                    c.drawString(x_atual, y, char)
                    x_atual += espacamento_ano

            # tabela
            elif campo == "tabela":
                c.setFont("Helvetica", 11)
                espacamento = {
                    'T': 9,
                    'U': 10.8,
                    'S': 9.5,
                }
                x_atual = x
                for i, char in enumerate(valor):
                    c.drawString(x_atual, y, char)
                    # Pega o espaçamento específico da letra ou usa o padrão
                    x_atual += espacamento.get(char, 9.9)       

            # valor_procedimento
            elif campo == "valor_procedimento":
                c.setFont("Helvetica", 12)
                espacamento = {
                    'R$': 11,
                    '2': 3,
                }
                x_atual = x
                for i, char in enumerate(valor):
                    c.drawString(x_atual, y, char)
                    # Pega o espaçamento específico da letra ou usa o padrão
                    x_atual += espacamento.get(char, 11.3)       


            # Campos quadriculados
            elif campo in campos_quadriculados:
                c.setFont("Helvetica", 12.5)
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
        # OBSERVAÇÃO (TEXTO LONGO COM QUEBRA AUTOMÁTICA)
        # ==================================================

        obs = dados.get("observacao", "").strip()
        if obs:
            x_obs, y_obs = CAMPOS["observacao"]
            largura_max = 470
            
            c.setFont("Helvetica", 9)
            
            # Quebra de texto manual
            palavras = obs.split()
            linha_atual = ""
            y_atual = y_obs
            espacamento_linha = 15
            
            for palavra in palavras:
                teste = f"{linha_atual} {palavra}".strip()
                largura_teste = c.stringWidth(teste, "Helvetica", 9)
                
                if largura_teste <= largura_max:
                    linha_atual = teste
                else:
                    if linha_atual:
                        c.drawString(x_obs, y_atual, linha_atual)
                        y_atual -= espacamento_linha
                    linha_atual = palavra
            
            # Desenha última linha
            if linha_atual:
                c.drawString(x_obs, y_atual, linha_atual)

        # Finaliza overlay
        c.save()
        packet.seek(0)

        # ==================================================
        # MESCLAR COM PDF ORIGINAL
        # ==================================================

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


# ======================================================
# ROTA DE DEBUG - ATIVA COM ?debug=1
# ======================================================

@app.route("/gerar-pdf-debug", methods=["POST"])
def gerar_pdf_debug():
    """Gera PDF com régua de coordenadas para calibração"""
    try:
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)
        
        # Desenha régua horizontal
        c.setFont("Courier", 6)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        for x in range(0, 600, 50):
            c.line(x, 0, x, 842)
            c.drawString(x + 2, 5, f"x={x}")
        
        # Desenha régua vertical
        for y in range(0, 850, 50):
            c.line(0, y, 595, y)
            c.drawString(5, y + 2, f"y={y}")
        
        # Marca os pontos dos campos
        c.setStrokeColorRGB(1, 0, 0)
        c.setFont("Courier", 7)
        for campo, (x, y) in CAMPOS.items():
            c.circle(x, y, 3, fill=1)
            c.drawString(x + 5, y, campo[:15])
        
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
            download_name="GUIA_DEBUG.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)