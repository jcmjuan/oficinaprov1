"""
Oficina Pro v1.0 - Testes Automatizados
Arquivo: test_dominio.py
Execução: python -m unittest test_dominio -v

Cobrem as regras de negócio centrais: cálculo de subtotais (polimorfismo), desconto, quilometragem, validação de telefone,
ciclo de estoque da OS (debita ao salvar / devolve ao tirar) e relatório de comissões.
"""
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from dominio import Pessoa, Cliente, Mecanico, Veiculo, ItemOS, Peca, MaoDeObra, OrdemServico
from banco import GerenciadorBanco, RepositorioOficina
from relatorios import EmissorPDF, REPORTLAB_DISPONIVEL


class TestDominio(unittest.TestCase):
    """Testes das clases de domínio (sem banco de dados)."""

    def setUp(self):
        self.cliente = Cliente("Maria Silva", "51988887777", "123.456.789-00")
        self.mecanico = Mecanico("Roberto Almeida", "51999991111", "Câmbio e Motor", 0.30)
        self.veiculo = Veiculo("abc-1d23", "Fiat Palio 1.0", 2000, 110000, cliente_id=1)

    def test_heranca_e_polimorfismo(self):
        # Cliente e Mecanico herdam de Pessoa; obter_resumo é polimórfico
        self.assertIsInstance(self.cliente, Pessoa)
        self.assertIsInstance(self.mecanico, Pessoa)
        self.assertIn("Cliente", self.cliente.obter_resumo())
        self.assertIn("Mecânico", self.mecanico.obter_resumo())

    def test_subtotais_polimorficos(self):
        peca = Peca("Pastilha de Freio", 2, 150.00)
        servico = MaoDeObra("Troca de Pastilhas", 1.5, 90.00, self.mecanico)
        # Mesmo contrato (ItemOS), comportamentos especializados
        self.assertIsInstance(peca, ItemOS)
        self.assertEqual(peca.calcular_subtotal(), 300.00)
        self.assertEqual(servico.calcular_subtotal(), 135.00)
        self.assertAlmostEqual(servico.obter_comissao_item(), 135.00 * 0.30)

    def test_comissao_sem_mecanico_retorna_zero(self):
        servico = MaoDeObra("Diagnóstico", 1.0, 100.00, mecanico=None)
        self.assertEqual(servico.obter_comissao_item(), 0.0)

    def test_validacao_telefone_invalido(self):
        with self.assertRaises(ValueError):
            Cliente("João", "123", "000.000.000-00")  # Poucos dígitos

    def test_validacao_nome_vazio(self):
        with self.assertRaises(ValueError):
            Cliente("  ", "51988887777", "000.000.000-00")

    def test_telefone_normalizado_para_whatsapp(self):
        cliente_sujeira = Cliente("Meia Maria", "(51) 98888-7777", "000.000.000-00")
        self.assertEqual(cliente_sujeira.telefone_digitos(), "51988887777")

    def test_placa_formatada(self):
        self.assertEqual(self.veiculo.placa, "ABC1D23")

    def test_km_nao_regressa(self):
        self.assertFalse(self.veiculo.atualizar_km(50000))       # menor que atual
        self.assertEqual(self.veiculo.quilometragem, 110000)      # intacta
        self.assertTrue(self.veiculo.atualizar_km(120000))

    def test_desconto_aplicado_e_total_liquido(self):
        os_obj = OrdemServico(1, self.veiculo, self.cliente, "30/10/2026", "Orçamento")
        os_obj.adicionar_item(Peca("Filtro de Óleo", 1, 35.00))
        os_obj.adicionar_item(MaoDeObra("Troca de Óleo", 0.5, 80.00, self.mecanico))
        self.assertEqual(os_obj.calcular_total_bruto(), 75.00)
        self.assertTrue(os_obj.aplicar_desconto(10.00))
        self.assertFalse(os_obj.aplicar_desconto(-5.00))   # negativo: rejeitado
        self.assertFalse(os_obj.aplicar_desconto(999.00))  # maior que total: rejeitado
        self.assertEqual(os_obj.calcular_total_liquido(), 65.00)

    def test_remover_item(self):
        os_obj = OrdemServico(1, self.veiculo, self.cliente, "30/10/2026")
        os_obj.adicionar_item(Peca("Filtro de Óleo", 1, 35.00))
        removido = os_obj.remover_item(0)
        self.assertEqual(removido.descricao, "Filtro de Óleo")
        self.assertEqual(len(os_obj.itens), 0)
        self.assertIsNone(os_obj.remover_item(5))  # índice inválido


class TestPersistenciaEstoque(unittest.TestCase):
    """Testa o ciclo de estoque: débito só ao salvar, devolução ao tirar peça."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        caminho = os.path.join(self.pasta, "teste.db")
        self.db = GerenciadorBanco(caminho)
        self.repo = RepositorioOficina(self.db)
        # Dados mínimos
        id_cli = self.repo.salvar_cliente(Cliente("Cliente Teste", "51988887777", "000.000.000-00"))
        self.repo.salvar_mecanico(Mecanico("Mecânico Teste", "51999991111", "Motor", 0.25))
        self.repo.salvar_veiculo(Veiculo("TST0A00", "Chevrolet Onix", 2020, 20000, cliente_id=id_cli))
        self.veiculo = self.repo.obter_veiculo_por_placa("TST0A00")
        self.cliente = self.repo.obter_cliente_por_id(id_cli)
        self.mecanico = self.repo.listar_mecanicos()[0]

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _nova_os(self):
        return OrdemServico(0, self.veiculo, self.cliente, datetime.now().strftime("%d/%m/%Y"), "Orçamento", self.mecanico)

    def test_baixa_e_devolucao_de_estoque(self):
        self.repo.salvar_peca_estoque("Vela de Ignição", 10, 18.00, 70.0)
        os_obj = self._nova_os()
        os_obj.adicionar_item(Peca("Vela de Ignição", 4, 45.00))
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        estoque = {p["nome"]: p["quantidade"] for p in self.repo.listar_estoque()}
        self.assertEqual(estoque["Vela de Ignição"], 6)  # 10 - 4 debitadas

        # Remove a peça da OS e reverte
        os_obj.remover_item(0)
        self.repo.salvar_itens_e_fechamento_os(os_obj)  # salvar sem itens... bloqueado na GUI, mas o repositório permite
        estoque = {p["nome"]: p["quantidade"] for p in self.repo.listar_estoque()}
        self.assertEqual(estoque["Vela de Ignição"], 10)  # devolvida ao estoque

    def test_estoque_insuficiente_sustenta_os_salva(self):
        self.repo.salvar_peca_estoque("Correia Dentada", 2, 120.00, 40.0)
        os_obj = self._nova_os()
        os_obj.adicionar_item(Peca("Correia Dentada", 5, 150.00))
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        with self.assertRaises(ValueError):
            self.repo.salvar_itens_e_fechamento_os(os_obj)
        estoque = {p["nome"]: p["quantidade"] for p in self.repo.listar_estoque()}
        self.assertEqual(estoque["Correia Dentada"], 2)  # nada foi debitado

    def test_entrada_financeira_apos_finalizar_e_reversao(self):
        os_obj = self._nova_os()
        os_obj.adicionar_item(MaoDeObra("Troca de Óleo", 0.5, 80.00, self.mecanico))
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        with self.db.sessao() as conn:
            registro = conn.cursor().execute("SELECT tipo FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()
            self.assertIsNone(registro)  # Orçamento não gera entrada financeira
        os_obj.status = "Finalizado"
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        with self.db.sessao() as conn:
            registro = conn.cursor().execute("SELECT valor, tipo FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()
            self.assertEqual(registro["tipo"], "ENTRADA")
            self.assertAlmostEqual(registro["valor"], os_obj.calcular_total_liquido())
        # Volta para "Em Serviço": a entrada é revertida
        os_obj.status = "Em Serviço"
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        with self.db.sessao() as conn:
            registro = conn.cursor().execute("SELECT COUNT(*) FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()
            self.assertEqual(registro[0], 0)

    def test_repor_estoque_soma_quantidade(self):
        novo = self.repo.salvar_peca_estoque("Filtro de Ar", 5, 22.00, 80.0)
        self.assertTrue(novo)
        mesmo_item = self.repo.salvar_peca_estoque("Filtro de Ar", 3, 22.00, 80.0)
        self.assertFalse(mesmo_item)  # atualizou em vez de duplicar
        peca = self.repo.obter_dados_peca("Filtro de Ar")
        self.assertEqual(peca["quantidade"], 8)  # 5 + 3 no mesmo registro

    def test_criar_os_sem_ids_lanca_erro_amigavel(self):
        """Regressão do bug do cadastro rápido: objeto de veículo sem id persistido não chega ao INSERT."""
        veiculo_sem_id = Veiculo("SEM0ID0", "Carro Sem Cadastro", 2020, 1000)
        os_obj = OrdemServico(0, veiculo_sem_id, self.cliente, datetime.now().strftime("%d/%m/%Y"))
        with self.assertRaises(ValueError):
            self.repo.criar_ordem_servico(os_obj)

    def test_reeditacao_os_finalizada_atualiza_financeiro(self):
        """Re-salvar OS finalizada (removendo item) mantém a ENTRADA no financeiro coerente com o total."""
        self.repo.salvar_peca_estoque("Peça Imutável", 10, 20.00, 50.0)
        os_obj = self._nova_os()
        os_obj.adicionar_item(Peca("Peça Imutável", 2, 100.00))  # bruto 200,00
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        os_obj.status = "Finalizado"
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        with self.db.sessao() as conn:
            valor = conn.cursor().execute("SELECT valor FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()["valor"]
            self.assertAlmostEqual(valor, 200.00)

        # Remove o item e re-salva: estoque devolvido e ENTRADA atualizada para 0
        os_obj.remover_item(0)
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        estoque = {p["nome"]: p["quantidade"] for p in self.repo.listar_estoque()}
        self.assertEqual(estoque["Peça Imutável"], 10)
        with self.db.sessao() as conn:
            valor = conn.cursor().execute("SELECT valor FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()["valor"]
            self.assertAlmostEqual(valor, 0.00)

    def test_atualizar_mecanico_e_peca_estoque(self):
        """Edição direta (não upsert) de mecânico e peça, novos na tela de Gerenciar."""
        mec = self.repo.listar_mecanicos()[0]
        self.repo.atualizar_mecanico(mec.id, Mecanico("Nome Novo", "51999991111", "Nova Especialidade", 0.31))
        editado = next(x for x in self.repo.listar_mecanicos() if x.id == mec.id)
        self.assertEqual(editado.nome, "Nome Novo")
        self.assertAlmostEqual(editado.taxa_comissao, 0.31)

        self.repo.salvar_peca_estoque("Filtro de Ar", 5, 22.00, 80.0)
        self.repo.atualizar_peca_estoque("Filtro de Ar", 7, 25.00, 60.0)  # edição absoluta
        d = self.repo.obter_dados_peca("Filtro de Ar")
        self.assertEqual(int(d["quantidade"]), 7)        # substituiu, não somou
        self.assertEqual(d["preco_custo"], 25.00)

    def test_relatorio_comissoes(self):
        os_obj = self._nova_os()
        os_obj.adicionar_item(MaoDeObra("Troca de Óleo", 2.0, 100.00, self.mecanico))
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        relatorio = self.repo.relatorio_comissoes(0)  # todo o histórico
        linha = next(l for l in relatorio if l["mecanico"] == "Mecânico Teste")
        self.assertEqual(linha["total_servicos"], 200.00)
        self.assertAlmostEqual(linha["comissao"], 200.00 * 0.25)

    def test_resumo_financeiro_lucro(self):
        os_obj = self._nova_os()
        # Peça com custo de aquisição informado: 40 de custo vendida por 100
        os_obj.adicionar_item(Peca("Peça Margem", 1, 100.00, custo_aquisicao=40.00))
        os_obj.numero_os = self.repo.criar_ordem_servico(os_obj)
        os_obj.status = "Finalizado"
        self.repo.salvar_itens_e_fechamento_os(os_obj)
        resumo = self.repo.resumo_financeiro()
        self.assertAlmostEqual(resumo["entradas"], 100.00)
        self.assertAlmostEqual(resumo["custo_pecas"], 40.00)
        self.assertAlmostEqual(resumo["lucro_estimado"], 60.00)  # 100 - 40 - 0 despesas


class TestDocumentosPDF(unittest.TestCase):
    """Testa o versionamento de PDFs: pasta por OS, arquivos nunca sobrescritos e migração do formato antigo."""

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.pasta_docs = os.path.join(self.pasta.name, "documentos")
        self.emissor = EmissorPDF(self.pasta_docs)
        self.cliente = Cliente("Maria Silva", "51988887777", "000.000.000-00")
        self.veiculo = Veiculo("TST0A00", "Chevrolet Onix", 2020, 20000)

    def tearDown(self):
        self.pasta.cleanup()

    def _os(self, numero: int, status: str) -> OrdemServico:
        return OrdemServico(numero, self.veiculo, self.cliente, "30/10/2026", status)

    @unittest.skipUnless(REPORTLAB_DISPONIVEL, "reportlab não instalado")
    def test_versionamento_sem_sobrescrita(self):
        os_obj = self._os(7, "Orçamento")
        pdf_orcamento = self.emissor.gerar_pdf_ordem_servico(os_obj)
        os_obj.status = "Finalizado"
        pdf_final = self.emissor.gerar_pdf_ordem_servico(os_obj)

        pasta_os = os.path.join(self.pasta_docs, EmissorPDF.nome_pasta_os(7, "TST0A00"))
        arquivos = os.listdir(pasta_os)
        self.assertEqual(len(arquivos), 2)                     # 2 gerações = 2 arquivos
        self.assertTrue(os.path.exists(pdf_orcamento))
        self.assertTrue(os.path.exists(pdf_final))
        self.assertTrue(os.path.basename(pdf_orcamento).startswith("ORCAMENTO_0007_"))
        self.assertTrue(os.path.basename(pdf_final).startswith("ORDEM_SERVICO_0007_"))
        soltos = [f for f in os.listdir(self.pasta_docs) if f.lower().endswith(".pdf")]
        self.assertEqual(soltos, [])                           # nada solto na raiz de documentos

    @unittest.skipUnless(REPORTLAB_DISPONIVEL, "reportlab não instalado")
    def test_colisao_mesmo_segundo_nao_sobrescreve(self):
        os_obj = self._os(9, "Orçamento")
        primeiro = self.emissor.gerar_pdf_ordem_servico(os_obj)
        # Força o mesmo carimbo: cria arquivo idêntico e pede outra geração imediatamente
        caminho_bloqueado = primeiro[:-4] + "0.pdf"
        with open(caminho_bloqueado, "w") as f: f.write("x")
        segundo = self.emissor.gerar_pdf_ordem_servico(os_obj)
        self.assertTrue(os.path.exists(primeiro))
        self.assertTrue(os.path.exists(segundo))
        self.assertNotEqual(primeiro, segundo)

    def test_migracao_de_pdfs_antigos(self):
        # Solta dois PDFs no formato antigo na raiz de documentos
        for nome in ["OS_0012_TST0A00.pdf", "OS_0104_IXX4B95.pdf"]:
            with open(os.path.join(self.pasta_docs, nome), "w") as f: f.write("pdf antigo")
        self.emissor.migrar_pdfs_antigos()

        pasta_0012 = os.path.join(self.pasta_docs, "OS_0012_TST0A00")
        pasta_0104 = os.path.join(self.pasta_docs, "OS_0104_IXX4B95")
        self.assertTrue(os.path.exists(os.path.join(pasta_0012, "OS_0012_TST0A00.pdf")))
        self.assertTrue(os.path.exists(os.path.join(pasta_0104, "OS_0104_IXX4B95.pdf")))
        self.assertEqual([f for f in os.listdir(self.pasta_docs) if f.endswith(".pdf")], [])

        # Idempotência: nova migração não duplica nada
        self.emissor.migrar_pdfs_antigos()
        todos = [os.path.join(r, f) for r, _, fs in os.walk(self.pasta_docs) for f in fs]
        self.assertEqual(len(todos), 2)

    def test_migracao_nao_sobrescreve_arquivo_existente(self):
        # Pasta já com o arquivo movido antes; o mesmo nome reaparece na raiz -> recebe sufixo _2
        pasta_0012 = os.path.join(self.pasta_docs, "OS_0012_TST0A00")
        os.makedirs(pasta_0012)
        with open(os.path.join(pasta_0012, "OS_0012_TST0A00.pdf"), "w") as f: f.write("versão 1")
        with open(os.path.join(self.pasta_docs, "OS_0012_TST0A00.pdf"), "w") as f: f.write("versão 2")
        self.emissor.migrar_pdfs_antigos()
        self.assertTrue(os.path.exists(os.path.join(pasta_0012, "OS_0012_TST0A00.pdf")))
        self.assertTrue(os.path.exists(os.path.join(pasta_0012, "OS_0012_TST0A00_2.pdf")))
        self.assertEqual([f for f in os.listdir(self.pasta_docs) if f.endswith(".pdf")], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
