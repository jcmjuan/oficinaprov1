"""
Oficina Pro v1.0 - Script para popular o banco de dados com dados de teste.
Arquivo: seed.py
Execução: python seed.py
"""
import os
from datetime import datetime, timedelta
from dominio import Cliente, Mecanico, Veiculo, Peca, MaoDeObra, OrdemServico
from banco import GerenciadorBanco, RepositorioOficina

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

    print("Inserindo mecânicos...")
    repo.salvar_mecanico(Mecanico("Roberto Almeida", "51999991111", "Câmbio e Motor", 0.30))
    repo.salvar_mecanico(Mecanico("Lucas Pinheiro", "51999992222", "Freios e Suspensão", 0.25))
    repo.salvar_mecanico(Mecanico("Fernanda Souza", "51999993333", "Injeção Eletrônica", 0.35))
    mecanicos = repo.listar_mecanicos()

    print("Inserindo peças no estoque com margens de mercado...")
    pecas_estoque = [
        ("Filtro de Óleo", 20, 15.50, 80.0),
        ("Filtro de Ar", 15, 22.00, 80.0),
        ("Pastilha de Freio", 10, 85.00, 50.0),
        ("Óleo Motor 5W30 (Litro)", 30, 45.00, 60.0),
        ("Correia Dentada", 5, 120.00, 40.0),
        ("Vela de Ignição", 40, 18.00, 70.0),
        ("Bateria 60Ah", 4, 350.00, 25.0)
    ]
    for nome, qtd, custo, margem in pecas_estoque:
        repo.salvar_peca_estoque(nome, qtd, custo, margem)

    print("Inserindo clientes e veículos...")
    c1 = Cliente("Juan Carlos Matos", "51988887777", "123.456.789-00")
    id_c1 = repo.salvar_cliente(c1)
    v1 = Veiculo("IXX4B95", "GM Corsa GL 1.4", 1995, 145000, cliente_id=id_c1)
    repo.salvar_veiculo(v1)

    c2 = Cliente("Maria Oliveira", "51977776666", "987.654.321-00")
    id_c2 = repo.salvar_cliente(c2)
    v2 = Veiculo("ABC1D23", "Fiat Palio 1.0", 2000, 110000, cliente_id=id_c2)
    repo.salvar_veiculo(v2)

    c3 = Cliente("Carlos Andrade", "51966665555", "111.222.333-44")
    id_c3 = repo.salvar_cliente(c3)
    v3 = Veiculo("XYZ9A88", "VW Gol G5", 2012, 85000, cliente_id=id_c3)
    repo.salvar_veiculo(v3)

    veiculo1 = repo.obter_veiculo_por_placa("IXX4B95")
    cliente1 = repo.obter_cliente_por_id(id_c1)
    veiculo2 = repo.obter_veiculo_por_placa("ABC1D23")
    cliente2 = repo.obter_cliente_por_id(id_c2)
    veiculo3 = repo.obter_veiculo_por_placa("XYZ9A88")
    cliente3 = repo.obter_cliente_por_id(id_c3)

    print("Inserindo ordens de serviço...")
    os1 = OrdemServico(0, veiculo1, cliente1, (datetime.now() - timedelta(days=40)).strftime("%d/%m/%Y"), "Finalizado", mecanicos[0])
    os1.adicionar_item(Peca("Filtro de Óleo", 1, 35.00))
    os1.adicionar_item(MaoDeObra("Troca de Óleo", 0.5, 80.00, mecanicos[0]))
    os1.aplicar_desconto(10.0)
    num_os1 = repo.criar_ordem_servico(os1)
    os1.numero_os = num_os1
    repo.salvar_itens_e_fechamento_os(os1)

    os2 = OrdemServico(0, veiculo2, cliente2, (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y"), "Em Serviço", mecanicos[1])
    os2.adicionar_item(Peca("Pastilha de Freio", 1, 150.00))
    os2.adicionar_item(MaoDeObra("Troca de Pastilhas", 1.5, 90.00, mecanicos[1]))
    num_os2 = repo.criar_ordem_servico(os2)
    os2.numero_os = num_os2
    repo.salvar_itens_e_fechamento_os(os2)

    os3 = OrdemServico(0, veiculo3, cliente3, datetime.now().strftime("%d/%m/%Y"), "Orçamento", mecanicos[2])
    os3.adicionar_item(Peca("Vela de Ignição", 4, 45.00))
    os3.adicionar_item(MaoDeObra("Diagnóstico de Injeção", 1.0, 120.00, mecanicos[2]))
    num_os3 = repo.criar_ordem_servico(os3)
    os3.numero_os = num_os3
    repo.salvar_itens_e_fechamento_os(os3)

    data_passada = (datetime.now().replace(day=1) - timedelta(days=5)).strftime("%d/%m/%Y")
    os4 = OrdemServico(0, veiculo1, cliente1, data_passada, "Finalizado", mecanicos[0])
    os4.adicionar_item(Peca("Bateria 60Ah", 1, 550.00))
    os4.adicionar_item(MaoDeObra("Instalação de Bateria", 0.3, 50.00, mecanicos[0]))
    num_os4 = repo.criar_ordem_servico(os4)
    os4.numero_os = num_os4
    repo.salvar_itens_e_fechamento_os(os4)

    print("Inserindo despesas e receitas manuais...")
    with db.obter_conexao() as conn:
        cursor = conn.cursor()
        data_mes_2 = (datetime.now().replace(day=1) - timedelta(days=60)).strftime("%d/%m/%Y")
        data_mes_1 = (datetime.now().replace(day=1) - timedelta(days=30)).strftime("%d/%m/%Y")
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, 'Aluguel', 2500.00, 'SAIDA')", (data_mes_2,))
        cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, 'Energia', 450.00, 'SAIDA')", (data_mes_1,))
        cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, 'Aluguel', 2500.00, 'SAIDA')", (data_hoje,))
        cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, 'Serviços Avulsos', 1200.00, 'ENTRADA')", (data_mes_2,))
        cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo) VALUES (?, 'Serviços Avulsos', 3500.00, 'ENTRADA')", (data_mes_1,))
        conn.commit()

    print("\n--- POPULAÇÃO CONCLUÍDA COM SUCESSO! ---")
    print("Agora execute: python app.py")

if __name__ == "__main__":
    popular_banco()