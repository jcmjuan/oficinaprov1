"""
Oficina Pro v1.0 - Gerador da Documentação da Etapa 3
Arquivo: gerar_etapa3.py
Execução: python gerar_etapa3.py  (produz Etapa3.pdf)

COMO COMPLETAR O DOCUMENTO:
1. Prints das telas: salve como PNG na pasta 'prints/' com os nomes listados abaixo
   (o script insere os que existem e marca placeholders para os que faltam).
2. Diagrama UML: cole o conteúdo de diagrama-de-classes.mmd no https://mermaid.live
   e exporte o PNG substituindo diagrama-de-classes.png; depois rode este script de novo.
3. Reexecute: python gerar_etapa3.py

PRINTS ESPERADOS (pasta prints/):
  tela_principal.png, novo_atendimento.png, gerenciar_mecanicos.png,
  gerenciar_estoque.png, gerenciar_oficina.png, financeiro.png,
  comissoes.png, pasta_documentos.png, pdf_gerado.png, historico_veiculo.png
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, Image, PageBreak, Preformatted)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

COR_GRAFITE = colors.HexColor("#1E293B")
COR_LARANJA = colors.HexColor("#F97316")
COR_VERDE = colors.HexColor("#22C55E")
COR_LINHA = colors.HexColor("#CBD5E1")
COR_SUAVE = colors.HexColor("#F1F5F9")
COR_MUTED = colors.HexColor("#64748B")
COR_ERRO = colors.HexColor("#EF4444")

LINK_REPO = "https://github.com/jcmjuan/oficinaprov1"
DATA_ENTREGA = "31/10/2026"

PRINTS = [
    ("tela_principal.png", "Tela principal: ficha do veículo/cliente, lançamento de itens, totais e o Histórico de Atendimentos (antes 'Pátio') nas dimensões ampliadas."),
    ("novo_atendimento.png", "Novo Atendimento: busca por placa e o fluxo de Cadastro Rápido (janela reformulada para exibir o botão de confirmação sem redimensionamento)."),
    ("gerenciar_mecanicos.png", "Gerenciar > Mecânicos: lista editável com seleção por clique, comissão informável (padrão 20% quando vazio) e botão 'Salvar Alterações do Selecionado'."),
    ("gerenciar_estoque.png", "Gerenciar > Estoque: cadastro/reposição (upsert por nome) e edição direta do item selecionado (quantidade absoluta, custo e margem)."),
    ("gerenciar_oficina.png", "Gerenciar > Oficina: dados da oficina persistidos que aparecem no cabeçalho dos orçamentos em PDF."),
    ("financeiro.png", "Painel Financeiro: cards de Entradas, Saídas, Saldo, Custo das Peças e Lucro Estimado + gráfico de fluxo por mês (3 meses de dados do seed)."),
    ("comissoes.png", "Relatório de Comissões por mecânico com filtro de período (30/60/90 dias ou histórico completo)."),
    ("pasta_documentos.png", "Pasta de Documentos da OS: estrutura versionada (uma pasta por OS com todas as versões geradas)."),
    ("pdf_gerado.png", "PDF do orçamento/OS gerado com a versão congelada no nome (status + carimbo de data/hora)."),
    ("historico_veiculo.png", "Histórico do veículo: filtro por placa + prompt de atualização de KM ao finalizar a OS."),
]

def estilos_base():
    s = getSampleStyleSheet()
    devolver = {
        "topo": ParagraphStyle("Topo", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=COR_GRAFITE),
        "badge": ParagraphStyle("Badge", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=COR_LARANJA),
        "h1": ParagraphStyle("H1", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=COR_GRAFITE, spaceBefore=10, spaceAfter=6),
        "h2": ParagraphStyle("H2", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=COR_LARANJA, spaceBefore=8, spaceAfter=4),
        "corpo": ParagraphStyle("Corpo", parent=s["Normal"], fontSize=9.5, leading=13.5, spaceAfter=4),
        "corpo_destaque": ParagraphStyle("CorpoD", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=9.5, leading=13.5, textColor=COR_GRAFITE, spaceAfter=4),
        "item": ParagraphStyle("Item", parent=s["Normal"], fontSize=9.5, leading=13.5, leftIndent=10, spaceAfter=2),
        "cel": ParagraphStyle("Cel", parent=s["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=COR_GRAFITE),
        "cel_b": ParagraphStyle("CelB", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=COR_GRAFITE),
        "thead": ParagraphStyle("Thead", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white),
        "caption": ParagraphStyle("Cap", parent=s["Normal"], fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=COR_MUTED),
        "placeholder": ParagraphStyle("PH", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=COR_ERRO, alignment=1),
        "codigo": ParagraphStyle("Cod", parent=s["Code"], fontSize=7.5, leading=9.5, textColor=COR_GRAFITE),
    }
    return devolver

def tabela(est, dados, larguras=None, cabecalho=True):
    linhas = list(dados)
    style = [
        ('BOX', (0, 0), (-1, -1), 0.8, COR_LINHA),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, COR_LINHA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    if cabecalho:
        style += [('BACKGROUND', (0, 0), (-1, 0), COR_GRAFITE),
                  ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)]
        linhas = [[Paragraph(esc(c, est["thead"]), est["thead"]) if not isinstance(c, Paragraph) else c for c in line] for line in [linhas[0]]] + linhas[1:]
    tabela_ = Table(linhas, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    tabela_.setStyle(TableStyle(style))
    # faixa zebrada
    extra = [('ROWBACKGROUNDS', (0, 1 if cabecalho else 0), (-1, -1), [colors.white, COR_SUAVE])]
    tabela_.setStyle(TableStyle(extra))
    return [tabela_]

def esc(texto, estilo):
    import html
    return html.escape(texto)

def P(texto, estilo):
    return Paragraph(texto, estilo)

def lista(est, itens):
    return [P(f"&bull; {i}", est["item"]) for i in itens]

def bloco_print(est, nome, legenda):
    """Insere o PNG da pasta prints/ se existir; caso contrário, placeholder marcado."""
    pasta = os.path.join("prints", nome)
    if os.path.exists(pasta):
        el = [Image(pasta, width=170*mm, height=100*mm), Spacer(1, 3), P(legenda, est["caption"]), Spacer(1, 8)]
        return el
    caixa = Table([[P(f"[ INSERIR PRINT: prints/{nome} ]<br/><font size=8 color='#64748B'>{legenda}</font>", est["placeholder"])]],
                  colWidths=[170*mm], rowHeights=[26*mm])
    caixa.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, COR_ERRO), ('ALIGN', (0, 0), (0, 0), 'CENTER'), ('VALIGN', (0, 0), (0, 0), 'MIDDLE')]))
    return [caixa, Spacer(1, 8)]

def imagem_uml(est, elementos):
    if os.path.exists("diagrama-de-classes.png"):
        img = Image("diagrama-de-classes.png", width=168*mm, height=118*mm)
        elementos += [img, Spacer(1, 3),
                      P("Nota: regenerar este export pelo Mermaid Live (diagrama-de-classes.mmd) para refletir a versão final das classes antes de enviar.", est["caption"]),
                      Spacer(1, 6)]
    else:
        elementos += [P("[ INSERIR DIAGRAMA: diagrama-de-classes.png — exporte pelo Mermaid Live usando o diagrama-de-classes.mmd ]", est["placeholder"]), Spacer(1, 6)]

def cabecalho(est, elementos):
    dados = [
        [P("<b>DEVSOLO STUDIO</b><br/><font size=8 color='#64748B'>Projeto POO - G2</font>", est["topo"]),
         Paragraph("ETAPA 3 — DOCUMENTAÇÃO COMPLETA", ParagraphStyle("B2", parent=est["badge"], alignment=2)),
         Paragraph(f"OficinaPro v1.0<br/><b>Juan Carlos Matos</b><br/><font size=8 color='#64748B'>{DATA_ENTREGA}</font>", est["cel_b"])],
    ]
    logo = Image("logo.png", width=12*mm, height=12*mm) if os.path.exists("logo.png") else Spacer(0, 0)
    dados[0].insert(0, logo)
    t = Table(dados, colWidths=[16*mm, 110*mm, 60*mm, 42*mm])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('LINEBELOW', (0, 0), (-1, -1), 1.2, COR_LARANJA),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    elementos += [t, Spacer(1, 10)]

def build(est):
    e = []
    cabecalho(est, e)

    # ---------- 1. PROPOSTA ----------
    e += [P("1. PROPOSTA (ATUALIZADA)", est["h1"]),
          P("<b>Problema:</b> pequenas oficinas mecânicas de bairro gerenciam orçamentos e serviços em cadernos e planilhas, gerando erros de soma, orçamentos ilegíveis e perda de histórico dos veículos atendidos.", est["corpo"]),
          P("<b>Público:</b> proprietários de oficinas independentes, mecânicos autônomos e atendentes de balcão que precisam formalizar o atendimento sem o custo de um ERP por assinatura.", est["corpo"]),
          P("<b>Escopo atual:</b> gestão de orçamentos e ordens de serviço (peças e mão de obra com comissão), estoque com margem de lucro e baixa transacional, relatórios (financeiro com gráfico, comissões por mecânico), emissão de documentos em PDF versionados, integração com WhatsApp e histórico por veículo. 100% em Python orientado a objetos, com persistência local em SQLite e interface gráfica CustomTkinter.", est["corpo"]),]

    # ---------- 2. EVOLUÇÃO DESDE A ETAPA 2 ----------
    e += [P("2. EVOLUÇÃO DESDE A ETAPA 2", est["h1"]),
          P("Além da implementação planejada, o projeto incorporou melhorias identificadas na prática (Etapa 3 enfatiza a demonstração: todos os itens abaixo são funcionais):", est["corpo"])]
    e += tabela(est, [
        ["Ítem", "Descrição"],
        ["Estoque transacional", "A baixa no estoque acontece ao salvar a OS: devolve o que estava debitado, debita o estado atual validando saldo e desfaz tudo em caso de erro (sem 'vazamento' de peças)."],
        ["Reposição inteligente", "Cadastrar peça existente soma ao saldo em vez de duplicar registros; edição direta disponível na aba Gerenciar."],
        ["Relatório de comissões", "Promessa da Etapa 1 materializada: comissões por mecânico com filtro de período (30/60/90 dias ou histórico)."],
        ["Configurações da oficina", "Nome, CNPJ, WhatsApp e endereço persistidos e usados no cabeçalho dos PDFs."],
        ["PDFs versionados", "Cada geração cria arquivo novo em documentos/OS_NNNN_PLACA/ com status e carimbo no nome (ORCAMENTO_0001_PLACA_20261031-1045.pdf) — nada é sobrescrito."],
        ["Reversão financeira", "Entrada no caixa ao finalizar a OS; se o status voltar atrás, o lançamento financeiro é revertido."],
        ["Imutabilidade da OS paga", "OS 'Finalizada' é documento financeiro: edição de itens/desconto bloqueada até reabrir o status."],
        ["Update de KM", "Ao finalizar, o sistema oferece atualização da quilometragem (método do domínio garantindo não-regressão)."],
        ["Gerenciar editável", "Mecânicos e peças agora têm lista clicável e alteração persistida."],
        ["Testes automatizados", "23 testes de domínio/persistência/documentos (unittest) cobrindo regras de negócio."],
    ], larguras=[35*mm, 135*mm])

    # ---------- 3. REQUISITOS POO ----------
    e += [P("3. REQUISITOS POO ATENDIDOS (obrigatórios do projeto)", est["h1"])]
    e += tabela(est, [
        ["Requisito", "Onde está", "Status"],
        ["Pelo menos 5 classes", "9 no domínio (Pessoa, Cliente, Mecânico, Veículo, ItemOS, Peça, MãoDeObra, OrdemServico) + 4 de infraestrutura (GerenciadorBanco, RepositorioOficina, EmissorPDF, AplicacaoOficinaPro)", "OK"],
        ["Herança", "Pessoa → Cliente/Mecânico e ItemOS → Peça/MãoDeObra (duas hierarquias)", "OK"],
        ["Polimorfismo", "obter_resumo() e calcular_subtotal() reescritos e chamados via referência à superclasse", "OK"],
        ["Associação", "OrdemServico ↔ Cliente/Veículo/Mecânico/ItemOS; MãoDeObra → Mecânico; Cliente ↔ Veículo", "OK"],
        ["Método privado", "Pessoa.__validar_telefone(); Veiculo.__formatar_placa()", "OK"],
        ["Atributo privado", "__cpf_cnpj, __especialidade, __taxa_comissao, __desconto, __placa, __quilometragem, __custo_aquisicao, __caminho_db", "OK"],
        ["Main cria ≥ 2 objetos", "A GUI cria/mantém objetos de todas as classes (validado nos testes)", "OK"],
    ], larguras=[38*mm, 118*mm, 14*mm])

    # ---------- 4. ARQUITETURA E UML ----------
    e += [PageBreak(), P("4. ARQUITETURA E DIAGRAMA DE CLASSES", est["h1"]),
          P("O sistema é organizado em quatro camadas, cada uma em arquivo próprio:", est["corpo"])]
    e += tabela(est, [
        ["Arquivo", "Camada", "Responsabilidade"],
        ["dominio.py", "Domínio (POO)", "Regras de negócio: classes hierárquicas, cálculos, validações e geração do link do WhatsApp"],
        ["banco.py", "Persistência", "SQLite transacional (GerenciadorBanco) e CRUD no RepositorioOficina, incluindo reconciliação de estoque e financeiro"],
        ["relatorios.py", "Documentos", "Emissão do PDF de orçamento/OS com reportlab, com versionamento por pasta da OS"],
        ["app.py", "Interface", "GUI CustomTkinter: telas, fluxos de balcão, diálogo de KM e integração com as camadas abaixo"],
        ["seed.py", "Dados", "População do banco de demonstração (5 mecânicos, 6 clientes, 8 veículos, 12 OS, 15 peças, 24 movimentos)"],
        ["test_dominio.py", "Testes", "23 testes automáticos das regras de negócio e de persistência/documentos"],
    ], larguras=[30*mm, 32*mm, 108*mm])
    e += [Spacer(1, 6), P("4.1 Diagrama de classes (domínio)", est["h2"]),]
    imagem_uml(est, e)
    e += [P("Diagrama 2 (camada de aplicação/persistência) e o código-fonte Mermaid completo estão no arquivo diagrama-de-classes.mmd do repositório.", est["caption"]), Spacer(1, 6)]

    # ---------- 5. DESCRIÇÃO DE CLASSES ----------
    e += [P("5. DESCRIÇÃO DE CLASSES, ATRIBUTOS E MÉTODOS", est["h1"])]
    e += tabela(est, [
        ["Classe", "Propósito", "Principais membros"],
        ["Pessoa (abstrata)", "Base de contato (nome, telefone) com validação real", "- _nome, - _telefone; - __validar_telefone(); + telefone_digitos(); + obter_resumo()*"],
        ["Cliente", "Proprietário dos veículos", "- __cpf_cnpj; + id, + veiculos; + adicionar_veiculo(v); + obter_resumo()"],
        ["Mecânico", "Profissional executor com comissão", "- __especialidade, - __taxa_comissao; + calcular_comissao(valor); + obter_resumo()"],
        ["Veículo", "Automóvel atendido com placa normalizada", "- __placa, - __quilometragem; - __formatar_placa(); + atualizar_km(nova)* (bloqueia regressão); + __str__()"],
        ["ItemOS (abstrata)", "Contrato de linha cobrável", "- _descricao, - _quantidade, - _valor_unitario; + calcular_subtotal()*"],
        ["Peça", "Insumo vendido, com custo para lucro real", "- __custo_aquisicao; + codigo_sku; + calcular_subtotal()"],
        ["MãoDeObra", "Serviço executado por um mecânico", "+ mecanico_responsavel; + calcular_subtotal(); + obter_comissao_item()"],
        ["OrdemServico", "Documento agregador (cliente, veículo, mecânico, itens)", "- __desconto; + numero_os, + status; + adicionar_item(); + remover_item(i); + aplicar_desconto()*; + definir_desconto_salvo(); + calcular_total_bruto()/liquido(); + gerar_link_whatsapp()"],
    ], larguras=[26*mm, 44*mm, 100*mm])

    # ---------- 6. BIBLIOTECAS EXTERNAS ----------
    e += [PageBreak(), P("6. BIBLIOTECAS EXTERNAS E CLASSES UTILITÁRIAS", est["h1"])]
    e += tabela(est, [
        ["Biblioteca", "Origem", "Uso no projeto"],
        ["customtkinter", "pip install customtkinter", "Toda a interface gráfica: janela principal, toplevels de atendimento/financeiro/comissões, temas escuros e CTkInputDialog para a KM"],
        ["tkinter.ttk", "Padrão do Python", "Treeviews (tabelas) do Histório de Atendimentos, histórico do veículo, itens da OS e das listas editáveis"],
        ["sqlite3", "Padrão do Python", "Banco local oficinapro.db com foreign keys, transações com commit/rollback e índices AUTOINCREMENT"],
        ["reportlab", "pip install reportlab", "Geração do PDF de orçamento/OS com layout, tabela e assinaturas (lib opcional: o app avisa se não estiver instalada)"],
        ["matplotlib", "pip install matplotlib", "Gráfico de barras (Entradas x Saídas) embutido no painel financeiro"],
        ["PIL (Pillow)", "pip install pillow", "Carregamento do logotipo no cabeçalho da aplicação"],
        ["webbrowser / urllib.parse", "Padrão", "Abertura do link wa.me com a mensagem pré-formatada e url-quoted"],
        ["abc / typing / datetime", "Padrão", "Classes abstratas, anotações de tipo e datas"],
    ], larguras=[32*mm, 42*mm, 96*mm])

    # ---------- 7. CRUD ----------
    e += [P("7. CRUD IMPLEMENTADO", est["h1"]),
          P("O núcleo de persistência é o RepositorioOficina (banco.py). O significado de cada letra do CRUD por entidade:", est["corpo"])]
    e += tabela(est, [
        ["Entidade", "Create", "Read", "Update", "Delete"],
        ["Clientes", "salvar_cliente()", "obter/listar", "— (limitação)", "—"],
        ["Mecânicos", "salvar_mecanico()", "listar/obter", "atualizar_mecanico()", "—"],
        ["Veículos", "salvar_veiculo()", "obter por placa", "atualizar_km_veiculo() (km)", "—"],
        ["Ordens de Serviço", "criar_ordem_servico()", "carregar_ordem_completa(), listar_ordens_painel()", "salvar_itens_e_fechamento_os() (status, desconto, itens)", "—"],
        ["Estoque", "salvar_peca_estoque() (upsert)", "listar/obter dados", "atualizar_peca_estoque()", "—"],
        ["Financeiro", "automático ao finalizar", "resumo_financeiro(), dados do gráfico", "valor da ENTRADA reajustado em re-salvas", "reversão automática se o status voltar atrás"],
    ], larguras=[27*mm, 38*mm, 45*mm, 47*mm, 13*mm])
    e += [P("<b>Decisão de projeto:</b> a letra D (exclusão) não é exposta a nenhuma entidade — registros comerciais (OS, cliente, veículo) constituem trilha de auditoria e, no caso do estoque, a baixa é reversível pelo próprio fluxo da OS. A exclusão de dados irreversíveis foi deliberadamente evitada (limitação assumida na seção 11).", est["corpo_destaque"])]

    # ---------- 8. PERSISTÊNCIA E DOCUMENTOS ----------
    e += [P("8. PERSISTÊNCIA E RASTREABILIDADE DE DOCUMENTOS", est["h1"]),
          P("Os dados salvam em SQLite local e permanecem entre sessões (objetos persistentes). Interrupções de fluxo não corrompem o estado: cada salvamento da OS ocorre em uma única transação que devolve o que estava debitado e valida o saldo atual antes de debitar — um erro de estoque insuficiente desfaz a operação inteira com rollback.", est["corpo"]),
          P("Já os documentos seguem política de versionamento imutável: cada geração produz um arquivo novo em documentos/OS_NNNN_PLACA/ com status e carimbo de data/hora no nome (ex.: ORCAMENTO_0001_IXX4B95_20261031-1045.pdf). O PDF do orçamento aprovado nunca é substituído pelo da OS finalizada — a trilha completa permanece acessível pelo botão 📁. PDFs do formato antigo existentes são migrados automaticamente para o novo padrão na inicialização.", est["corpo"])]

    # ---------- 9. TELAS ----------
    e += [PageBreak(), P("9. TELAS DO SISTEMA (COM SCREENSHOTS)", est["h1"]),
          P("Abaixo, cada tela em uso com sua função. (Os arquivos listados devem ser salvos na pasta prints/ e o script reexecutado.)", est["corpo"])]
    for nome, legenda in PRINTS:
        e += bloco_print(est, nome, legenda)
        e += [Spacer(1, 2)]

    # ---------- 10. TESTES ----------
    e += [P("10. EXEMPLOS DE TESTES", est["h1"]),
          P("Execução: python -m unittest test_dominio -v (23 testes, ~3s, todos verdes no estado de entrega). O arquivo cobre três grupos:", est["corpo"])]
    e += tabela(est, [
        ["Grupo", "O que verifica (exemplos)"],
        ["Domínio", "Herança/polimorfismo (resumos e subtotais), validações (telefone, placa, KM não-regressa), desconto (aceito/rejeitado por limites), remoção de item, comissão sem mecânico = 0"],
        ["Persistência", "Ciclo estoque (debita ao salvar, devolve ao remover), erro de saldo preserva estado, ENTRADA financeira ao finalizar e reversão, atualização do valor em re-salva, upsert do estoque, relatório de comissões, lucro estimado, erro amigável sem ids"],
        ["Documentos", "Versionamento (2 gerações = 2 arquivos na pasta da OS, nada na raiz), colisão de nome sem sobrescrita, migração do formato antigo idempotente e sem duplicar"],
    ], larguras=[26*mm, 144*mm])
    e += [Spacer(1, 4), P("Exemplo real (desconto com limites):", est["h2"]),
          Preformatted("""def test_desconto_aplicado_e_total_liquido(self):
    os_obj = OrdemServico(1, self.veiculo, self.cliente, "30/10/2026", "Orçamento")
    os_obj.adicionar_item(Peca("Filtro de Óleo", 1, 35.00))
    os_obj.adicionar_item(MaoDeObra("Troca de Óleo", 0.5, 80.00, self.mecanico))
    self.assertEqual(os_obj.calcular_total_bruto(), 75.00)
    self.assertTrue(os_obj.aplicar_desconto(10.00))
    self.assertFalse(os_obj.aplicar_desconto(-5.00))    # negativo: rejeitado
    self.assertFalse(os_obj.aplicar_desconto(999.00))   # maior que total: rejeitado
    self.assertEqual(os_obj.calcular_total_liquido(), 65.00)""", est["codigo"]),
          Spacer(1, 4), P("Exemplo real (ciclo de estoque):", est["h2"]),
          Preformatted("""def test_reeditacao_os_finalizada_atualiza_financeiro(self):
    os_obj.adicionar_item(Peca("Peça Imutável", 2, 100.00))  # bruto 200,00
    ...  # finaliza: ENTRADA de 200,00
    os_obj.remover_item(0)
    self.repo.salvar_itens_e_fechamento_os(os_obj)
    self.assertEqual(estoque["Peça Imutável"], 10)   # devolvida
    self.assertAlmostEqual(valor_entrada, 0.00)      # financeiro coerente""", est["codigo"])]

    # ---------- 11. LIMITAÇÕES ----------
    e += [P("11. LIMITAÇÕES E BUGS CONHECIDOS", est["h1"])]
    e += lista(est, [
        "Pastas de documentos legadas (OS_0002 e OS_0003 com duas placas cada) herdadas do formato antigo; novas gerações sempre usam a placa atual da OS.",
        "Não há exclusão de registros (clientes, mecânicos, OS, peças) — decisão de integridade/auditoria, ver seção 7.",
        "Edição de clientes/veículos não implementada (nome/telefone fixos pós-cadastro).",
        "Versões de PDF são identificadas por nome/carimbo; não há tabela de metadados marcando a 'versão aprovada'.",
        "Multiusuário não suportado: SQLite local projeta um único balcão por arquivo de banco.",
        "A quantidade do estoque aceita valores fracionários (ex.: litros de óleo) e a exibição trunca para inteiro no painel de Gerenciar.",
        "Sem backup automático do banco (backup é copiar o oficinapro.db).",
        "Testes automatizados cobrem domínio, persistência e documentos; não há testes de GUI.",
    ])

    # ---------- 12. O QUE FALTA ----------
    e += [P("12. O QUE FALTA FAZER (PLANEJAMENTO ATÉ A ENTREGA FINAL 19/11)", est["h1"])]
    e += tabela(est, [
        ["Tarefa", "Prazo alvo", "Status"],
        ["Capturar os 10 prints da seção 9 e regenerar este PDF", "antes de 05/11", "Em andamento"],
        ["Regenerar o PNG do diagrama UML pelo Mermaid Live (versão corrigida)", "antes de 05/11", "Pronto p/ executar"],
        ["Demonstração em aula (05/11) — roteiro na seção 13", "05/11", "Ensaiar"],
        ["Slides de apresentação (reaproveitando seções 1–10)", "até 19/11", "Não iniciado"],
        ["Evolução candidata: conceito real de 'Pátio' (OS ativas Aprovado/Em Serviço)", "se der tempo", "Ideia registrada"],
        ["Evolução candidata: tabela de metadados de documentos (versão aprovada) e retenção de rascunhos", "se der tempo", "Ideia registrada"],
    ], larguras=[96*mm, 30*mm, 44*mm])

    # ---------- 13. REPOSITÓRIO E DEMO ----------
    e += [P("13. REPOSITÓRIO E ROTEIRO DE DEMONSTRAÇÃO", est["h1"]),
          P(f"<b>Repositório remoto:</b> <font color='#2563EB'><u>{LINK_REPO}</u></font> (branch main)", est["corpo"]),
          P("Estrutura: app.py | banco.py | dominio.py | relatorios.py | seed.py | test_dominio.py | diagrama-de-classes.mmd | gerar_etapa3.py | logo.* | documentos/", est["corpo"]),
          P("Execução: pip install customtkinter matplotlib reportlab pillow  →  python seed.py (banco de demonstração)  →  python app.py. Testes: python -m unittest test_dominio.", est["corpo"]),
          P("<b>Roteiro de 5 passos para a demonstração em aula (05/11):</b>", est["corpo_destaque"])]
    e += lista(est, [
        "Novo Atendimento: buscar placa existente e também cadastrar cliente novo (fluxo rápido) — mostra validações.",
        "Lançar peça com saldo insuficiente (feedback), depois quantidade válida; aplicar desconto; Salvar Estado.",
        "Mudar status para Finalizado: prompt de KM, PDF versionado aberto e link do WhatsApp com o valor correto.",
        "Comissões por mecânico com período + painel Financeiro (cards e gráfico com 3 meses).",
        "Gerenciar: editar mecânico e peça, e mostrar o estoque devolvido ao remover um item (transacionalidade).",
    ])

    return e

def main():
    est = estilos_base()
    doc = SimpleDocTemplate("Etapa3.pdf", pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm)
    doc.build(build(est))
    faltando = [nome for nome, _ in PRINTS if not os.path.exists(os.path.join("prints", nome))]
    print("=== ETAPA3.pdf gerado ===")
    if faltando:
        print(f"Prints pendentes ({len(faltando)}): salve em prints/ e reexecute -", ", ".join(faltando))
    else:
        print("Todos os 10 prints encontrados - documento completo!")

if __name__ == "__main__":
    main()
