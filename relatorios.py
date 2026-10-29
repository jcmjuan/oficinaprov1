"""
Oficina Pro v1.0 - Geração de Documentos em PDF
Arquivo: relatorios.py
"""
import os

# Tratamento de erro caso o ReportLab não esteja instalado na máquina do professor
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

from dominio import OrdemServico, Peca, MaoDeObra

class EmissorPDF:
    def __init__(self, pasta_saida: str = "documentos"):
        self.pasta_saida = pasta_saida
        if not os.path.exists(self.pasta_saida):
            os.makedirs(self.pasta_saida)

    def gerar_pdf_ordem_servico(self, os_obj: OrdemServico) -> str:
        if not REPORTLAB_DISPONIVEL:
            raise ImportError("A biblioteca 'reportlab' não está instalada. Execute: pip install reportlab")

        nome_arquivo = f"OS_{os_obj.numero_os:04d}_{os_obj.veiculo.placa}.pdf"
        caminho_completo = os.path.join(self.pasta_saida, nome_arquivo)

        doc = SimpleDocTemplate(
            caminho_completo, pagesize=A4,
            leftMargin=15 * mm, rightMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm
        )

        elementos = []
        estilos = getSampleStyleSheet()

        cor_grafite = colors.HexColor("#1E2938")
        cor_laranja = colors.HexColor("#F97316")
        cor_verde = colors.HexColor("#22C55E")
        cor_fundo_tabela = colors.HexColor("#F8FAFC")
        cor_linha = colors.HexColor("#CBD5E1")

        estilo_topo = ParagraphStyle('Topo', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=cor_grafite)
        estilo_sub = ParagraphStyle('Sub', parent=estilos['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor("#64748B"))
        estilo_os_badge = ParagraphStyle('BadgeOS', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=17, alignment=2, textColor=cor_laranja)
        estilo_secao = ParagraphStyle('Secao', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=cor_grafite)
        estilo_celula = ParagraphStyle('Celula', parent=estilos['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=cor_grafite)
        estilo_celula_bold = ParagraphStyle('CelulaB', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=cor_grafite)

        mec_txt = os_obj.mecanico_principal.nome if os_obj.mecanico_principal else "A Definir"

        # 1. Cabeçalho
        dados_cabecalho = [
            [Paragraph("<b>OFICINA PRO v1.0</b><br/>Gestão Mecânica & Balcão", estilo_topo),
             Paragraph(f"{'ORÇAMENTO' if os_obj.status == 'Orçamento' else 'ORDEM DE SERVIÇO'}<br/><b>#{os_obj.numero_os:04d}</b><br/><font size=8 color='#64748B'>Status: {os_obj.status.upper()}</font>", estilo_os_badge)],
            [Paragraph("Oficina Pro Auto Center Ltda.<br/>CNPJ: 00.000.000/0001-00 | WhatsApp: (51) 98888-7777", estilo_sub),
             Paragraph(f"Data: <b>{os_obj.data_abertura}</b>", ParagraphStyle('Data', parent=estilo_celula, alignment=2, textColor=colors.HexColor("#64748B")))]
        ]
        tabela_topo = Table(dados_cabecalho, colWidths=[110 * mm, 70 * mm])
        tabela_topo.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elementos.append(tabela_topo)
        elementos.append(Spacer(1, 10))

        # 2. Dados do Veículo, Cliente e Responsável Técnico
        elementos.append(Paragraph("DADOS DO CLIENTE, VEÍCULO E PROFISSIONAL RESPONSÁVEL", estilo_secao))
        elementos.append(Spacer(1, 4))
        dados_cv = [
            [Paragraph(f"<b>Cliente:</b> {os_obj.cliente.nome}", estilo_celula), Paragraph(f"<b>Veículo:</b> {os_obj.veiculo.marca_modelo}", estilo_celula)],
            [Paragraph(f"<b>WhatsApp:</b> {os_obj.cliente.telefone}", estilo_celula), Paragraph(f"<b>Placa:</b> {os_obj.veiculo.placa} | <b>Ano:</b> {os_obj.veiculo.ano}", estilo_celula)],
            [Paragraph(f"<b>CPF/CNPJ:</b> {os_obj.cliente.cpf_cnpj}", estilo_celula), Paragraph(f"<b>KM:</b> {os_obj.veiculo.quilometragem:,} km", estilo_celula)],
            [Paragraph(f"<b>Mecânico Responsável:</b> {mec_txt}", estilo_celula_bold), Paragraph(f"<b>Cadastrado na Oficina:</b> Sim", estilo_celula)]
        ]
        tabela_cv = Table(dados_cv, colWidths=[90 * mm, 90 * mm])
        tabela_cv.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cor_fundo_tabela), ('BOX', (0, 0), (-1, -1), 1, cor_linha),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cor_linha), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        elementos.append(tabela_cv)
        elementos.append(Spacer(1, 10))

        # 3. Itens Lançados
        elementos.append(Paragraph("DISCRIMINAÇÃO DE PEÇAS E SERVIÇOS", estilo_secao))
        elementos.append(Spacer(1, 4))
        dados_itens = [[
            Paragraph("<b>Tipo</b>", estilo_celula_bold), Paragraph("<b>Descrição Detalhada / Executor</b>", estilo_celula_bold),
            Paragraph("<b>Qtd</b>", estilo_celula_bold), Paragraph("<b>Unitário</b>", estilo_celula_bold), Paragraph("<b>Subtotal</b>", estilo_celula_bold)
        ]]

        for item in os_obj.itens:
            if isinstance(item, Peca):
                tipo = "PEÇA"
                desc = f"{item.descricao} <font color='#64748B' size=8>(Cód: {item.codigo_sku})</font>"
            else:
                tipo = "SERVIÇO"
                mec_nome = item.mecanico_responsavel.nome if hasattr(item, 'mecanico_responsavel') and item.mecanico_responsavel else mec_txt
                desc = f"{item.descricao} <font color='#64748B' size=8>(Mecânico: {mec_nome})</font>"

            dados_itens.append([
                Paragraph(tipo, estilo_celula), Paragraph(desc, estilo_celula),
                Paragraph(f"{item.quantidade:.1f}", estilo_celula), Paragraph(f"R$ {item.valor_unitario:.2f}", estilo_celula),
                Paragraph(f"R$ {item.calcular_subtotal():.2f}", estilo_celula_bold)
            ])

        tabela_itens = Table(dados_itens, colWidths=[24 * mm, 86 * mm, 22 * mm, 24 * mm, 24 * mm])
        tabela_itens.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")), ('BOX', (0, 0), (-1, -1), 1, cor_linha),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cor_linha), ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'), ('ALIGN', (4, 0), (-1, -1), 'RIGHT')
        ]))
        elementos.append(tabela_itens)
        elementos.append(Spacer(1, 8))

        # 4. Totais
        dados_totais = [
            [Paragraph("Subtotal Bruto:", estilo_celula), Paragraph(f"R$ {os_obj.calcular_total_bruto():.2f}", estilo_celula)],
            [Paragraph("Desconto Concedido:", estilo_celula), Paragraph(f"- R$ {os_obj.desconto:.2f}", estilo_celula)],
            [Paragraph("<b>TOTAL FINAL:</b>", estilo_celula_bold), Paragraph(f"<b>R$ {os_obj.calcular_total_liquido():.2f}</b>", ParagraphStyle('Tot', parent=estilo_celula_bold, textColor=cor_verde, alignment=2))]
        ]
        tabela_tot = Table(dados_totais, colWidths=[40 * mm, 35 * mm], hAlign='RIGHT')
        tabela_tot.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cor_fundo_tabela), ('BOX', (0, 0), (-1, -1), 1, cor_linha),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, cor_linha), ('ALIGN', (1, 0), (1, -1), 'RIGHT')
        ]))
        elementos.append(tabela_tot)
        elementos.append(Spacer(1, 20))

        # 5. Assinaturas
        dados_ass = [
            [Paragraph("__________________________________________<br/><b>Responsável Técnico</b><br/>Oficina Pro", ParagraphStyle('A1', parent=estilo_celula, alignment=1)),
             Paragraph(f"__________________________________________<br/><b>{os_obj.cliente.nome}</b><br/>Cliente Proprietário", ParagraphStyle('A2', parent=estilo_celula, alignment=1))]
        ]
        tabela_ass = Table(dados_ass, colWidths=[90 * mm, 90 * mm])
        elementos.append(KeepTogether(tabela_ass))

        doc.build(elementos)
        return caminho_completo