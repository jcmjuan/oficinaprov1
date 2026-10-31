"""
Oficina Pro v1.0 - Script para popular o banco de dados com dados de teste robustos.
Arquivo: seed.py
Execução: python seed.py     (depois: python app.py)

Observação: os consumos de peças pelas OS respeitam o saldo inicial do estoque,
pois o repositório agora debita estoque transacionalmente ao salvar cada OS.
"""
import os
from datetime import datetime, timedelta

from dominio import Cliente, Mecanico, Veiculo, Peca, MaoDeObra, OrdemServico
from banco import GerenciadorBanco, RepositorioOficina

# (nome, quantidade inicial, preco custo, margem lucro %, codigo SKU)
ESTOQUE_INICIAL = [
    ("Filtro de Óleo",            40, 15.50, 80, "FIL001"),
    ("Filtro de Ar",              30, 22.00, 70, "FIL002"),
    ("Filtro de Combustível",     20, 28.00, 65, "FIL003"),
    ("Pastilha de Freio",         24, 85.00, 50, "FRE001"),
    ("Disco de Freio",             8, 160.00, 45, "FRE002"),
    ("Fluido de Freio DOT4",      15, 25.00, 60, "FRE003"),
    ("Óleo Motor 5W30 (Litro)",   60, 45.00, 60, "LUB001"),
    ("Correia Dentada",            6, 120.00, 40, "MOT001"),
    ("Vela de Ignição",           48, 18.00, 70, "MOT002"),
    ("Bateria 60Ah",               6, 350.00, 25, "ELE001"),
    ("Amortecedor Dianteiro",      8, 280.00, 35, "SUS001"),
    ("Coifa de Homocinética",     10, 35.00, 55, "SUS002"),
    ("Lâmpada H4",                20, 15.00, 90, "ELE002"),
    ("Palhetas do Limpador",      16, 30.00, 65, "ACE001"),
    ("Aditivo Radiador 1L",       12, 22.00, 60, "REF001"),
]

MECANICOS_INICIAIS = [
    ("Roberto Almeida", "51999991111", "Câmbio e Motor",        0.30),
    ("Lucas Pinheiro",  "51999992222", "Freios e Suspensão",    0.25),
    ("Fernanda Souza",  "51999993333", "Injeção Eletrônica",    0.35),
    ("Marcos Vieira",   "51999994444", "Elétrica Automotiva",   0.28),
    ("Tainá Ferreira",  "51999995555", "Suspensão e Alinhamento", 0.27),
]

CLIENTES_INICIAIS = [
    ("Juan Carlos Matos",    "51988887777", "123.456.789-00"),
    ("Maria Oliveira",       "51977776666", "987.654.321-00"),
    ("Carlos Andrade",       "51966665555", "111.222.333-44"),
    ("Ana Beatriz Costa",    "51955554444", "222.333.444-55"),
    ("Pedro Henrique Souza", "51944443333", "333.444.555-66"),
    ("Lucia Ferreira",       "51933332222", "444.555.666-77"),
]

VEICULOS_INICIAIS = [
    # (placa, marca/modelo, ano, km, indice do cliente em CLIENTES_INICIAIS)
    ("IXX4B95", "GM Corsa GL 1.4",      1995, 145000, 0),
    ("ABC1D23", "Fiat Palio 1.0",       2000, 110000, 1),
    ("XYZ9A88", "VW Gol G5",            2012,  85000, 2),
    ("DEF2E34", "Honda Civic EXL",      2018,  42000, 3),
    ("GHI3F45", "Toyota Corolla XEI",   2020,  30000, 4),
    ("JKL4G56", "Fiat Argo Drive",      2019,  38000, 5),
    ("MNO5H67", "Ford Ka SEL",          2017,  65000, 0),  # segundo carro do Juan
    ("PQR6I78", "VW Saveiro Cross",     2015,  95000, 2),  # segundo carro do Carlos
]

def popular_banco():
    print("--- INICIANDO POPULAÇÃO DO BANCO DE DADOS ---")

    if os.path.exists("oficinapro.db"):
        try:
            os.remove("oficinapro.db")
            print("[OK] Banco de dados antigo removido.")
        except PermissionError:
            print("[ERRO] Feche o app.py antes de rodar este script."); return

    db = GerenciadorBanco("oficinapro.db")
    repo = RepositorioOficina(db)

    # --- MECÂNICOS ---
    print("Inserindo mecânicos (5)...")
    for nome, tel, esp, taxa in MECANICOS_INICIAIS:
        repo.salvar_mecanico(Mecanico(nome, tel, esp, taxa))
    mecanicos = {m.especialidade: m for m in repo.listar_mecanicos()}

    # --- ESTOQUE ---
    print("Inserindo estoque (15 peças, SKUs e margens de mercado)...")
    for nome, qtd, custo, margem, sku in ESTOQUE_INICIAL:
        repo.salvar_peca_estoque(nome, qtd, custo, margem)
    estoque = {p["nome"]: p for p in repo.listar_estoque()}
    skus = {nome: sku for nome, _, _, _, sku in ESTOQUE_INICIAL}

    # --- CLIENTES E VEÍCULOS ---
    print("Inserindo clientes (6) e veículos (8)...")
    ids_clientes = []
    for nome, tel, cpf in CLIENTES_INICIAIS:
        ids_clientes.append(repo.salvar_cliente(Cliente(nome, tel, cpf)))
    placas = {}
    for placa, modelo, ano, km, idx_cli in VEICULOS_INICIAIS:
        repo.salvar_veiculo(Veiculo(placa, modelo, ano, km, cliente_id=ids_clientes[idx_cli]))
        placas[placa] = (repo.obter_veiculo_por_placa(placa), repo.obter_cliente_por_id(ids_clientes[idx_cli]))

    # --- Ajudantes de itens ---
    def peca(nome: str, qtd: float, preco_venda: float) -> Peca:
        """Peça com SKU e custo de aquisição vindos do estoque (para lucro real no financeiro)."""
        d = estoque[nome]
        return Peca(nome, qtd, preco_venda, codigo_sku=skus[nome], custo_aquisicao=d["preco_custo"])

    def mao_de_obra(descricao: str, horas: float, valor_hora: float, especialidade: str) -> MaoDeObra:
        return MaoDeObra(descricao, horas, valor_hora, mecanicos[especialidade])

    def criar_os(placa: str, mecanico: str, dias_atras: int, status: str, itens, desconto: float = 0.0) -> int:
        veiculo, cliente = placas[placa]
        data = (datetime.now() - timedelta(days=dias_atras)).strftime("%d/%m/%Y")
        os_obj = OrdemServico(0, veiculo, cliente, data, status, mecanicos[mecanico])
        for item in itens:
            os_obj.adicionar_item(item)
        if desconto > 0:
            os_obj.aplicar_desconto(desconto)
        os_obj.numero_os = repo.criar_ordem_servico(os_obj)
        repo.salvar_itens_e_fechamento_os(os_obj)
        return os_obj.numero_os

    # --- ORDENS DE SERVIÇO (12, espalhadas em ~3 meses) ---
    print("Inserindo ordens de serviço (12, com peças, serviços e descontos)...")
    criar_os("IXX4B95", "Câmbio e Motor", 85, "Finalizado", [
        peca("Óleo Motor 5W30 (Litro)", 4, 52.00),
        peca("Filtro de Óleo", 1, 27.90),
        mao_de_obra("Troca de Óleo e Filtros", 1.0, 90.00, "Câmbio e Motor"),
    ], desconto=10.0)

    criar_os("ABC1D23", "Freios e Suspensão", 70, "Finalizado", [
        peca("Pastilha de Freio", 1, 140.00),
        peca("Fluido de Freio DOT4", 1, 35.00),
        mao_de_obra("Substituição de Pastilhas", 1.5, 110.00, "Freios e Suspensão"),
    ])

    criar_os("MNO5H67", "Elétrica Automotiva", 55, "Finalizado", [
        peca("Bateria 60Ah", 1, 420.00),
        mao_de_obra("Instalação de Bateria", 0.5, 70.00, "Elétrica Automotiva"),
    ])

    criar_os("XYZ9A88", "Injeção Eletrônica", 55, "Finalizado", [
        peca("Vela de Ignição", 4, 31.50),
        mao_de_obra("Diagnóstico e Troca de Velas", 1.0, 130.00, "Injeção Eletrônica"),
    ])

    criar_os("JKL4G56", "Suspensão e Alinhamento", 40, "Finalizado", [
        peca("Amortecedor Dianteiro", 2, 380.00),
        mao_de_obra("Troca de Amortecedores Dianteiros", 2.0, 140.00, "Suspensão e Alinhamento"),
    ])

    criar_os("DEF2E34", "Injeção Eletrônica", 30, "Finalizado", [
        peca("Filtro de Ar", 1, 38.00),
        peca("Filtro de Óleo", 1, 27.90),
        peca("Óleo Motor 5W30 (Litro)", 3.5, 52.00),
        mao_de_obra("Revisão Preventiva 20.000 km", 1.5, 120.00, "Injeção Eletrônica"),
    ], desconto=20.0)

    criar_os("GHI3F45", "Freios e Suspensão", 25, "Finalizado", [
        peca("Disco de Freio", 2, 290.00),
        peca("Pastilha de Freio", 1, 140.00),
        peca("Fluido de Freio DOT4", 1, 35.00),
        mao_de_obra("Retífica do Sistema de Freios", 2.0, 140.00, "Freios e Suspensão"),
    ])

    criar_os("PQR6I78", "Suspensão e Alinhamento", 20, "Aprovado", [
        peca("Coifa de Homocinética", 1, 55.00),
        mao_de_obra("Substituição de Coifa", 1.2, 130.00, "Suspensão e Alinhamento"),
    ])

    criar_os("ABC1D23", "Elétrica Automotiva", 12, "Finalizado", [
        peca("Lâmpada H4", 2, 28.00),
        peca("Palhetas do Limpador", 1, 48.00),
        mao_de_obra("Troca de Lâmpadas e Palhetas", 0.8, 80.00, "Elétrica Automotiva"),
    ])

    criar_os("DEF2E34", "Injeção Eletrônica", 7, "Aprovado", [
        peca("Correia Dentada", 1, 168.00),
        mao_de_obra("Troca de Correia Dentada", 1.5, 150.00, "Injeção Eletrônica"),
    ], desconto=30.0)

    criar_os("IXX4B95", "Câmbio e Motor", 3, "Em Serviço", [
        peca("Óleo Motor 5W30 (Litro)", 4, 52.00),
        peca("Filtro de Combustível", 1, 46.90),
        mao_de_obra("Manutenção Geral de Motor", 1.0, 95.00, "Câmbio e Motor"),
    ])

    criar_os("XYZ9A88", "Injeção Eletrônica", 0, "Orçamento", [
        peca("Aditivo Radiador 1L", 1, 35.20),
        mao_de_obra("Teste de Pressurização do Sistema de Arrefecimento", 0.8, 90.00, "Injeção Eletrônica"),
    ])

    # --- MOVIMENTOS FINANCEIROS MANUAIS (despesas fixas + entradas avulsas em 3 meses) ---
    print("Inserindo despesas fixas e entradas avulsas (últimos 3 meses)...")
    def data(dias_atras: int) -> str:
        return (datetime.now() - timedelta(days=dias_atras)).strftime("%d/%m/%Y")

    movimentos = [
        # (dias_atras, descricao, valor, tipo)
        (80, "Aluguel",         1800.00, "SAIDA"),
        (78, "Energia Elétrica",  450.00, "SAIDA"),
        (77, "Internet + Telefone", 150.00, "SAIDA"),
        (60, "Serviços Avulsos", 3000.00, "ENTRADA"),

        (50, "Aluguel",         1800.00, "SAIDA"),
        (48, "Energia Elétrica",  480.00, "SAIDA"),
        (47, "Internet + Telefone", 150.00, "SAIDA"),
        (45, "Água e Esgoto",      180.00, "SAIDA"),
        (35, "Serviços Avulsos", 4300.00, "ENTRADA"),

        (20, "Aluguel",         1800.00, "SAIDA"),
        (18, "Energia Elétrica",  465.00, "SAIDA"),
        (17, "Internet + Telefone", 150.00, "SAIDA"),
        (10, "Serviços Avulsos", 2000.00, "ENTRADA"),

        (2,  "Aluguel",         1800.00, "SAIDA"),
        (1,  "Energia Elétrica",  455.00, "SAIDA"),
        (1,  "Internet + Telefone", 150.00, "SAIDA"),
    ]
    with db.sessao() as conn:
        cursor = conn.cursor()
        for dias, descricao, valor, tipo in movimentos:
            cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, ?, ?, ?)",
                           (data(dias), descricao, valor, tipo))

    # --- RESUMO FINAL ---
    print("\n--- POPULAÇÃO CONCLUÍDA COM SUCESSO! ---")
    with db.sessao() as conn:
        cursor = conn.cursor()
        for tabela in ["mecanicos", "clientes", "veiculos", "ordens_servico", "itens_os", "estoque", "financeiro"]:
            n = cursor.execute(f"SELECT COUNT(*) AS n FROM {tabela}").fetchone()["n"]
            print(f"  {tabela:16s}: {n} registros")
        resumo = repo.resumo_financeiro()
        print("\n  Saldo de caixa:           R$ {:,.2f}".format(resumo["saldo"]).replace(",", "X").replace(".", ",").replace("X", "."))
        print("  Lucro estimado (peças):   R$ {:,.2f}".format(resumo["lucro_estimado"]).replace(",", "X").replace(".", ",").replace("X", "."))
        vendas = cursor.execute("SELECT descricao, SUM(quantidade) AS qtd FROM itens_os WHERE tipo_item='PECA' GROUP BY descricao ORDER BY descricao")
        for linha in vendas:
            print("  Peça vendida: {} x{:.1f}".format(linha["descricao"], linha["qtd"]))
        print("\nAgora execute: python app.py")

if __name__ == "__main__":
    popular_banco()
