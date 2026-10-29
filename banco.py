"""
Oficina Pro v1.0 - Camada de Persistência SQLite
Arquivo: banco.py
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from dominio import Cliente, Mecanico, Veiculo, Peca, MaoDeObra, OrdemServico

class GerenciadorBanco:
    def __init__(self, caminho_db: str = "oficinapro.db"):
        self.__caminho_db = caminho_db
        self.__inicializar_tabelas()

    def obter_conexao(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.__caminho_db)
        conn.row_factory = sqlite3.Row
        return conn

    def __inicializar_tabelas(self) -> None:
        with self.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    cpf_cnpj TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS mecanicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    especialidade TEXT NOT NULL,
                    taxa_comissao REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS veiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa TEXT NOT NULL UNIQUE,
                    marca_modelo TEXT NOT NULL,
                    ano INTEGER NOT NULL,
                    quilometragem INTEGER NOT NULL,
                    cliente_id INTEGER NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS ordens_servico (
                    numero_os INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_abertura TEXT NOT NULL,
                    status TEXT NOT NULL,
                    desconto REAL DEFAULT 0.0,
                    veiculo_id INTEGER NOT NULL,
                    cliente_id INTEGER NOT NULL,
                    mecanico_id INTEGER,
                    FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
                );
                CREATE TABLE IF NOT EXISTS itens_os (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_os INTEGER NOT NULL,
                    tipo_item TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    valor_unitario REAL NOT NULL,
                    codigo_sku TEXT,
                    custo_aquisicao REAL,
                    mecanico_id INTEGER,
                    FOREIGN KEY (numero_os) REFERENCES ordens_servico(numero_os) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
                );
                CREATE TABLE IF NOT EXISTS financeiro (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    tipo TEXT NOT NULL,
                    numero_os INTEGER,
                    FOREIGN KEY (numero_os) REFERENCES ordens_servico(numero_os)
                );
                -- ESTRUTURA DO ESTOQUE COM MARGEM DE LUCRO
                CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    quantidade INTEGER NOT NULL DEFAULT 0,
                    preco_custo REAL NOT NULL DEFAULT 0.0,
                    margem_lucro REAL NOT NULL DEFAULT 50.0
                );
            """)
            conn.commit()

class RepositorioOficina:
    def __init__(self, db: GerenciadorBanco):
        self.db = db

    # --- CLIENTES ---
    def salvar_cliente(self, cliente: Cliente) -> int:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO clientes (nome, telefone, cpf_cnpj) VALUES (?, ?, ?)", (cliente.nome, cliente.telefone, cliente.cpf_cnpj))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError("Já existe um cliente cadastrado com este CPF/CNPJ.")

    def obter_cliente_por_id(self, id_cliente: int) -> Optional[Cliente]:
        with self.db.obter_conexao() as conn:
            r = conn.cursor().execute("SELECT * FROM clientes WHERE id = ?", (id_cliente,)).fetchone()
            return Cliente(r["nome"], r["telefone"], r["cpf_cnpj"], r["id"]) if r else None

    # --- MECÂNICOS ---
    def salvar_mecanico(self, mecanico: Mecanico) -> int:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO mecanicos (nome, telefone, especialidade, taxa_comissao) VALUES (?, ?, ?, ?)", (mecanico.nome, mecanico.telefone, mecanico.especialidade, mecanico.taxa_comissao))
            conn.commit()
            return cursor.lastrowid

    def listar_mecanicos(self) -> List[Mecanico]:
        with self.db.obter_conexao() as conn:
            return [Mecanico(r["nome"], r["telefone"], r["especialidade"], r["taxa_comissao"], r["id"]) for r in conn.cursor().execute("SELECT * FROM mecanicos ORDER BY nome").fetchall()]

    def obter_mecanico_por_id(self, id_mec: int) -> Optional[Mecanico]:
        if not id_mec: return None
        with self.db.obter_conexao() as conn:
            r = conn.cursor().execute("SELECT * FROM mecanicos WHERE id = ?", (id_mec,)).fetchone()
            return Mecanico(r["nome"], r["telefone"], r["especialidade"], r["taxa_comissao"], r["id"]) if r else None

    # --- VEÍCULOS ---
    def salvar_veiculo(self, veiculo: Veiculo) -> int:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO veiculos (placa, marca_modelo, ano, quilometragem, cliente_id) VALUES (?, ?, ?, ?, ?)", (veiculo.placa, veiculo.marca_modelo, veiculo.ano, veiculo.quilometragem, veiculo.cliente_id))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError("Já existe um veículo cadastrado com esta placa.")

    def obter_veiculo_por_placa(self, placa: str) -> Optional[Veiculo]:
        placa_limpa = placa.replace("-", "").replace(" ", "").upper()
        with self.db.obter_conexao() as conn:
            r = conn.cursor().execute("SELECT * FROM veiculos WHERE placa = ?", (placa_limpa,)).fetchone()
            return Veiculo(r["placa"], r["marca_modelo"], r["ano"], r["quilometragem"], r["cliente_id"], r["id"]) if r else None

    def historico_manutencoes_veiculo(self, placa: str) -> List[dict]:
        with self.db.obter_conexao() as conn:
            res = conn.cursor().execute("""
                SELECT os.data_abertura, COALESCE(m.nome, 'Não Atribuído') AS mecanico, i.descricao, (i.quantidade * i.valor_unitario) as subtotal
                FROM ordens_servico os JOIN veiculos v ON os.veiculo_id = v.id
                LEFT JOIN mecanicos m ON os.mecanico_id = m.id JOIN itens_os i ON os.numero_os = i.numero_os
                WHERE v.placa = ? ORDER BY os.numero_os DESC
            """, (placa.replace("-", "").replace(" ", "").upper(),))
            return [dict(r) for r in res.fetchall()]

    # --- ORDENS DE SERVIÇO ---
    def criar_ordem_servico(self, os_obj: OrdemServico) -> int:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            mec_id = os_obj.mecanico_principal.id if os_obj.mecanico_principal else None
            cursor.execute("INSERT INTO ordens_servico (data_abertura, status, desconto, veiculo_id, cliente_id, mecanico_id) VALUES (?, ?, ?, ?, ?, ?)", (os_obj.data_abertura, os_obj.status, os_obj.desconto, os_obj.veiculo.id, os_obj.cliente.id, mec_id))
            conn.commit()
            return cursor.lastrowid

    def carregar_ordem_completa(self, numero_os: int) -> Optional[OrdemServico]:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            row_os = cursor.execute("SELECT * FROM ordens_servico WHERE numero_os = ?", (numero_os,)).fetchone()
            if not row_os: return None
            cliente = self.obter_cliente_por_id(row_os["cliente_id"])
            r_v = cursor.execute("SELECT * FROM veiculos WHERE id = ?", (row_os["veiculo_id"],)).fetchone()
            veiculo = Veiculo(r_v["placa"], r_v["marca_modelo"], r_v["ano"], r_v["quilometragem"], r_v["cliente_id"], r_v["id"])
            mecanico = self.obter_mecanico_por_id(row_os["mecanico_id"])
            
            os_obj = OrdemServico(row_os["numero_os"], veiculo, cliente, row_os["data_abertura"], row_os["status"], mecanico)
            os_obj.aplicar_desconto(row_os["desconto"])
            
            for r_item in cursor.execute("SELECT * FROM itens_os WHERE numero_os = ?", (numero_os,)).fetchall():
                if r_item["tipo_item"] == "PECA":
                    item = Peca(r_item["descricao"], r_item["quantidade"], r_item["valor_unitario"], r_item["codigo_sku"] or "GEN", r_item["custo_aquisicao"] or 0.0)
                else:
                    mec_item = self.obter_mecanico_por_id(r_item["mecanico_id"]) or mecanico
                    item = MaoDeObra(r_item["descricao"], r_item["quantidade"], r_item["valor_unitario"], mec_item)
                os_obj.adicionar_item(item)
            return os_obj

    def salvar_itens_e_fechamento_os(self, os_obj: OrdemServico) -> None:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            mec_id = os_obj.mecanico_principal.id if os_obj.mecanico_principal else None
            cursor.execute("UPDATE ordens_servico SET status = ?, desconto = ?, mecanico_id = ? WHERE numero_os = ?", (os_obj.status, os_obj.desconto, mec_id, os_obj.numero_os))
            cursor.execute("DELETE FROM itens_os WHERE numero_os = ?", (os_obj.numero_os,))
            
            for item in os_obj.itens:
                if isinstance(item, Peca):
                    cursor.execute("INSERT INTO itens_os (numero_os, tipo_item, descricao, quantidade, valor_unitario, codigo_sku, custo_aquisicao) VALUES (?, 'PECA', ?, ?, ?, ?, ?)", (os_obj.numero_os, item.descricao, item.quantidade, item.valor_unitario, item.codigo_sku, item.custo_aquisicao))
                else:
                    mec_item_id = item.mecanico_responsavel.id if hasattr(item, 'mecanico_responsavel') and item.mecanico_responsavel else mec_id
                    cursor.execute("INSERT INTO itens_os (numero_os, tipo_item, descricao, quantidade, valor_unitario, mecanico_id) VALUES (?, 'MAO_DE_OBRA', ?, ?, ?, ?)", (os_obj.numero_os, item.descricao, item.quantidade, item.valor_unitario, mec_item_id))
            
            if os_obj.status == "Finalizado":
                ja_existe = cursor.execute("SELECT id FROM financeiro WHERE numero_os = ?", (os_obj.numero_os,)).fetchone()
                if not ja_existe:
                    cursor.execute("INSERT INTO financeiro (data, descricao, valor, tipo, numero_os) VALUES (?, ?, ?, 'ENTRADA', ?)", 
                                   (datetime.now().strftime("%d/%m/%Y"), f"Recebimento OS #{os_obj.numero_os:04d}", os_obj.calcular_total_liquido(), os_obj.numero_os))
            conn.commit()

    def listar_ordens_painel(self, filtro_placa: str = "") -> List[dict]:
        with self.db.obter_conexao() as conn:
            termo = f"%{filtro_placa.replace('-', '').replace(' ', '').upper()}%"
            linhas = conn.cursor().execute("""
                SELECT os.numero_os, os.data_abertura, v.placa, v.marca_modelo, c.nome AS cliente_nome,
                       COALESCE(m.nome, 'Não Atribuído') AS mecanico_nome, os.status, os.desconto,
                       COALESCE(SUM(i.quantidade * i.valor_unitario), 0.0) AS subtotal_bruto
                FROM ordens_servico os JOIN veiculos v ON os.veiculo_id = v.id JOIN clientes c ON os.cliente_id = c.id
                LEFT JOIN mecanicos m ON os.mecanico_id = m.id LEFT JOIN itens_os i ON os.numero_os = i.numero_os
                WHERE v.placa LIKE ? OR c.nome LIKE ? GROUP BY os.numero_os ORDER BY os.numero_os DESC
            """, (termo, f"%{filtro_placa}%")).fetchall()
            return [{
                "numero_os": r["numero_os"], "data": r["data_abertura"], "placa": r["placa"], "veiculo": r["marca_modelo"],
                "cliente": r["cliente_nome"], "mecanico": r["mecanico_nome"], "status": r["status"],
                "total_liquido": max(0.0, r["subtotal_bruto"] - r["desconto"])
            } for r in linhas]

    # --- ESTOQUE COM MARGEM ---
    def salvar_peca_estoque(self, nome: str, qtd: int, preco_custo: float, margem_lucro: float) -> None:
        with self.db.obter_conexao() as conn:
            conn.cursor().execute("INSERT INTO estoque (nome, quantidade, preco_custo, margem_lucro) VALUES (?, ?, ?, ?)", (nome, qtd, preco_custo, margem_lucro))
            conn.commit()

    def listar_estoque(self) -> List[dict]:
        with self.db.obter_conexao() as conn:
            return [dict(r) for r in conn.cursor().execute("SELECT * FROM estoque ORDER BY nome").fetchall()]

    def obter_dados_peca(self, nome_peca: str) -> Optional[dict]:
        with self.db.obter_conexao() as conn:
            r = conn.cursor().execute("SELECT * FROM estoque WHERE nome = ?", (nome_peca,)).fetchone()
            return dict(r) if r else None

    def dar_baixa_estoque(self, nome_peca: str, qtd: int) -> bool:
        with self.db.obter_conexao() as conn:
            cursor = conn.cursor()
            peca = cursor.execute("SELECT id, quantidade FROM estoque WHERE nome = ?", (nome_peca,)).fetchone()
            if not peca or peca["quantidade"] < qtd:
                return False
            cursor.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qtd, peca["id"]))
            conn.commit()
            return True

    # --- FINANCEIRO ---
    def obter_dados_financeiros_grafico(self) -> dict:
        with self.db.obter_conexao() as conn:
            res = conn.cursor().execute("""
                SELECT SUBSTR(data, 4, 7) AS mes_ano, tipo, SUM(valor) as total
                FROM financeiro GROUP BY mes_ano, tipo ORDER BY mes_ano
            """).fetchall()
            dados = {}
            for r in res:
                mes = r["mes_ano"]
                if mes not in dados: dados[mes] = {"ENTRADA": 0.0, "SAIDA": 0.0}
                dados[mes][r["tipo"]] = r["total"]
            return dados