"""
Oficina Pro v1.0 - Interface Operacional Unificada de Balcão
Arquivo: app.py
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
import webbrowser
import os
import platform
from datetime import datetime
from PIL import Image

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_DISPONIVEL = True
except ImportError:
    MATPLOTLIB_DISPONIVEL = False

from dominio import Cliente, Mecanico, Veiculo, Peca, MaoDeObra, OrdemServico
from banco import GerenciadorBanco, RepositorioOficina
from relatorios import EmissorPDF

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COR_FUNDO = "#0F172A"; COR_CARD = "#1E293B"; COR_LARANJA = "#F97316"; COR_LARANJA_HOV = "#EA580C"
COR_VERDE = "#22C55E"; COR_VERDE_HOV = "#16A34A"; COR_TEXTO = "#F8FAFC"; COR_MUTED = "#94A3B8"; COR_BORDA = "#334155"

class AplicacaoOficinaPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Oficina Pro v1.0 - Gestão Integrada de Balcão e Atendimento")
        self.geometry("1240x760"); self.minsize(1100, 700)
        self.configure(fg_color=COR_FUNDO)
        self.db = GerenciadorBanco("oficinapro.db")
        self.repo = RepositorioOficina(self.db)
        self.emissor_pdf = EmissorPDF("documentos")
        self.cliente_ativo = None; self.veiculo_ativo = None; self.os_ativa = None
        self._garantir_dados_iniciais()
        self._construir_interface()
        self._carregar_os_inicial()

    def _garantir_dados_iniciais(self):
        if not self.repo.listar_mecanicos():
            self.repo.salvar_mecanico(Mecanico("Roberto Almeida", "51999991111", "Câmbio e Motor", 0.30))
            self.repo.salvar_mecanico(Mecanico("Lucas Pinheiro", "51999992222", "Freios e Suspensão", 0.25))

    def _carregar_os_inicial(self):
        ordens = self.repo.listar_ordens_painel()
        if ordens: self._abrir_os_pelo_numero(ordens[0]["numero_os"])

    def _construir_interface(self):
        quadro_topo = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA)
        quadro_topo.pack(fill="x", padx=16, pady=(12, 8))

        try:
            img_logo = ctk.CTkImage(Image.open("logo.png"), size=(32, 32))
            lbl_logo = ctk.CTkLabel(quadro_topo, text=" OFICINA PRO", image=img_logo, compound="left", font=ctk.CTkFont(size=18, weight="bold"), text_color=COR_LARANJA)
        except Exception:
            lbl_logo = ctk.CTkLabel(quadro_topo, text="⚙️ OFICINA PRO", font=ctk.CTkFont(size=18, weight="bold"), text_color=COR_LARANJA)
        lbl_logo.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(quadro_topo, text="Placa:", font=ctk.CTkFont(size=13, weight="bold"), text_color=COR_TEXTO).pack(side="left", padx=(10, 4))
        self.ent_busca_placa = ctk.CTkEntry(quadro_topo, placeholder_text="Ex: IXX4B95", width=120)
        self.ent_busca_placa.pack(side="left", padx=4)
        ctk.CTkButton(quadro_topo, text="Buscar", width=80, fg_color=COR_LARANJA, command=self._buscar_veiculo).pack(side="left", padx=6)

        ctk.CTkButton(quadro_topo, text="+ Novo Atendimento", fg_color=COR_VERDE, hover_color=COR_VERDE_HOV, width=160, command=self._janela_novo_atendimento).pack(side="right", padx=16, pady=10)
        ctk.CTkButton(quadro_topo, text="💰 Comissões", fg_color="#334155", hover_color="#475569", width=115, command=self._janela_comissoes).pack(side="right", padx=10)
        ctk.CTkButton(quadro_topo, text="📊 Financeiro", fg_color="#334155", hover_color="#475569", width=120, command=self._janela_financeiro).pack(side="right", padx=10)
        ctk.CTkButton(quadro_topo, text="⚙️ Gerenciar", fg_color="#334155", hover_color="#475569", width=110, command=self._janela_gerenciamento).pack(side="right", padx=10)

        self.area_central = ctk.CTkFrame(self, fg_color="transparent")
        self.area_central.pack(fill="both", expand=True, padx=16, pady=4)

        self.coluna_esq = ctk.CTkFrame(self.area_central, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA, width=460)
        self.coluna_esq.pack(side="left", fill="both", expand=False, padx=(0, 8)); self.coluna_esq.pack_propagate(False)

        ctk.CTkLabel(self.coluna_esq, text="DADOS DO VEÍCULO E CLIENTE", font=ctk.CTkFont(size=13, weight="bold"), text_color=COR_LARANJA).pack(anchor="w", padx=14, pady=(12, 4))
        self.lbl_info_carro = ctk.CTkLabel(self.coluna_esq, text="Nenhum veículo selecionado.", font=ctk.CTkFont(size=12), text_color=COR_MUTED, justify="left")
        self.lbl_info_carro.pack(anchor="w", padx=14, pady=(0, 8))
        ctk.CTkFrame(self.coluna_esq, height=1, fg_color=COR_BORDA).pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(self.coluna_esq, text="HISTÓRICO DESTE CARRO", font=ctk.CTkFont(size=13, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", padx=14, pady=(6, 4))
        
        cols_hist = ("data", "mec", "item", "sub")
        self.tab_hist = ttk.Treeview(self.coluna_esq, columns=cols_hist, show="headings", height=11)
        for c, t, w in zip(cols_hist, ["Data", "Mecânico", "Peça / Serviço", "Valor (R$)"], [80, 100, 180, 75]):
            self.tab_hist.heading(c, text=t); self.tab_hist.column(c, width=w, anchor="center" if c in ["data", "sub"] else "w")
        self.tab_hist.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.coluna_dir = ctk.CTkFrame(self.area_central, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA)
        self.coluna_dir.pack(side="right", fill="both", expand=True, padx=(8, 0))

        quadro_os_topo = ctk.CTkFrame(self.coluna_dir, fg_color="transparent")
        quadro_os_topo.pack(fill="x", padx=14, pady=(10, 4))
        self.lbl_os_titulo = ctk.CTkLabel(quadro_os_topo, text="NENHUMA OS ABERTA", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_TEXTO)
        self.lbl_os_titulo.pack(side="left")

        quadro_config_os = ctk.CTkFrame(self.coluna_dir, fg_color="#182234", corner_radius=8)
        quadro_config_os.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(quadro_config_os, text="Responsável:").grid(row=0, column=0, padx=8, pady=8)
        self.cb_mecanicos = ctk.CTkComboBox(quadro_config_os, width=190); self.cb_mecanicos.grid(row=0, column=1, padx=6, pady=8)
        self._atualizar_combo_mecanicos()
        ctk.CTkLabel(quadro_config_os, text="Status:").grid(row=0, column=2, padx=8, pady=8)
        self.cb_status = ctk.CTkComboBox(quadro_config_os, values=["Orçamento", "Aprovado", "Em Serviço", "Finalizado"], width=130)
        self.cb_status.set("Orçamento"); self.cb_status.grid(row=0, column=3, padx=6, pady=8)
        ctk.CTkButton(quadro_config_os, text="Salvar Estado", width=95, fg_color="#334155", command=self._salvar_estado_os).grid(row=0, column=4, padx=8, pady=8)

        self.quadro_lancar = ctk.CTkFrame(self.coluna_dir, fg_color="#182234", corner_radius=8)
        self.quadro_lancar.pack(fill="x", padx=14, pady=4)
        self.var_tipo_item = ctk.StringVar(value="PECA")
        ctk.CTkRadioButton(self.quadro_lancar, text="Peça", variable=self.var_tipo_item, value="PECA", command=self._alternar_tipo_item).grid(row=0, column=0, padx=8, pady=6)
        ctk.CTkRadioButton(self.quadro_lancar, text="Mão de Obra", variable=self.var_tipo_item, value="SERVICO", command=self._alternar_tipo_item).grid(row=0, column=1, padx=6, pady=6)

        self.ent_item_desc = ctk.CTkComboBox(self.quadro_lancar, values=["Carregando..."], width=260)
        self.ent_item_desc.grid(row=0, column=2, padx=6, pady=6)
        self.ent_item_qtd = ctk.CTkEntry(self.quadro_lancar, placeholder_text="Qtd", width=60)
        self.ent_item_qtd.grid(row=0, column=3, padx=6, pady=6)
        self.ent_item_valor = ctk.CTkEntry(self.quadro_lancar, placeholder_text="Valor R$", width=80)
        self.ent_item_valor.grid(row=0, column=4, padx=6, pady=6)
        ctk.CTkButton(self.quadro_lancar, text="+ Incluir", width=80, fg_color=COR_LARANJA, command=self._adicionar_item_memoria).grid(row=0, column=5, padx=8, pady=6)

        self._atualizar_campo_descricao()

        cols_os = ("tipo", "desc", "qtd", "unit", "sub")
        self.tab_itens_os = ttk.Treeview(self.coluna_dir, columns=cols_os, show="headings", height=8)
        for c, t, w in zip(cols_os, ["Tipo", "Descrição", "Qtd", "Unitário", "Subtotal"], [75, 280, 55, 85, 95]):
            self.tab_itens_os.heading(c, text=t); self.tab_itens_os.column(c, width=w, anchor="e" if c in ["unit", "sub"] else ("center" if c in ["tipo", "qtd"] else "w"))
        self.tab_itens_os.pack(fill="both", expand=True, padx=14, pady=6)

        quadro_fechamento = ctk.CTkFrame(self.coluna_dir, fg_color="transparent")
        quadro_fechamento.pack(fill="x", padx=14, pady=(6, 12))
        ctk.CTkButton(quadro_fechamento, text="− Remover Item", width=115, fg_color="#EF4444", hover_color="#DC2626", command=self._remover_item_os).pack(side="left", padx=4)
        ctk.CTkLabel(quadro_fechamento, text="Desconto (R$):").pack(side="left", padx=4)
        self.ent_desconto = ctk.CTkEntry(quadro_fechamento, width=80); self.ent_desconto.insert(0, "0.00"); self.ent_desconto.pack(side="left", padx=4)
        ctk.CTkButton(quadro_fechamento, text="Aplicar", width=70, fg_color="#334155", command=self._aplicar_desconto).pack(side="left", padx=4)
        self.lbl_total_os = ctk.CTkLabel(quadro_fechamento, text="TOTAL: R$ 0,00", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_VERDE)
        self.lbl_total_os.pack(side="left", padx=16)
        ctk.CTkButton(quadro_fechamento, text="📄 Gerar PDF", width=115, fg_color="#334155", command=self._emitir_pdf).pack(side="right", padx=6)
        ctk.CTkButton(quadro_fechamento, text="📁 Pasta da OS", width=115, fg_color="#334155", command=self._abrir_pasta_documentos).pack(side="right", padx=6)
        ctk.CTkButton(quadro_fechamento, text="💬 WhatsApp", width=145, fg_color=COR_VERDE, command=self._disparar_whatsapp).pack(side="right", padx=6)

        quadro_patio = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA, height=140)
        quadro_patio.pack(fill="x", padx=16, pady=(4, 12)); quadro_patio.pack_propagate(False)
        ctk.CTkLabel(quadro_patio, text="🚗 PÁTIO (2 cliques para carregar)", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_MUTED).pack(anchor="w", padx=14, pady=(6, 2))
        cols_patio = ("num", "data", "placa", "veic", "cli", "status", "tot")
        self.tab_patio = ttk.Treeview(quadro_patio, columns=cols_patio, show="headings", height=3)
        for c, t, w in zip(cols_patio, ["OS Nº", "Data", "Placa", "Veículo", "Cliente", "Status", "Total Líquido"], [60, 85, 85, 190, 180, 95, 100]):
            self.tab_patio.heading(c, text=t); self.tab_patio.column(c, width=w, anchor="e" if c == "tot" else ("center" if c in ["num", "data", "placa", "status"] else "w"))
        self.tab_patio.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.tab_patio.bind("<Double-1>", lambda e: self._selecionar_os_patio())
        self._recarregar_patio()

    def _alternar_tipo_item(self):
        self._atualizar_campo_descricao()

    def _atualizar_campo_descricao(self):
        if hasattr(self, 'ent_item_desc') and self.ent_item_desc.winfo_exists():
            self.ent_item_desc.destroy()

        if self.var_tipo_item.get() == "PECA":
            pecas = [p["nome"] for p in self.repo.listar_estoque()]
            if not pecas: pecas = ["(Estoque Vazio - Cadastre em Gerenciar)"]
            self.ent_item_desc = ctk.CTkComboBox(self.quadro_lancar, values=pecas, width=260, command=self._calcular_preco_venda)
            self.ent_item_desc.set(pecas[0])
        else:
            self.ent_item_desc = ctk.CTkEntry(self.quadro_lancar, placeholder_text="Descrição do Serviço", width=260)
        
        self.ent_item_desc.grid(row=0, column=2, padx=6, pady=6)

    def _calcular_preco_venda(self, nome_peca: str):
        if self.var_tipo_item.get() != "PECA": return
        dados = self.repo.obter_dados_peca(nome_peca)
        if dados:
            custo = dados["preco_custo"]
            margem = dados["margem_lucro"] / 100
            preco_venda = custo * (1 + margem)
            self.ent_item_valor.delete(0, "end")
            self.ent_item_valor.insert(0, f"{preco_venda:.2f}")

    def _atualizar_combo_mecanicos(self):
        mecanicos = self.repo.listar_mecanicos()
        opcoes = [f"{m.id} - {m.nome}" for m in mecanicos] if mecanicos else ["Nenhum cadastrado"]
        self.cb_mecanicos.configure(values=opcoes); self.cb_mecanicos.set(opcoes[0])

    def _buscar_veiculo(self):
        placa = self.ent_busca_placa.get().strip()
        if not placa: return
        veiculo = self.repo.obter_veiculo_por_placa(placa)
        if veiculo:
            self.veiculo_ativo = veiculo
            self.cliente_ativo = self.repo.obter_cliente_por_id(veiculo.cliente_id)
            self._atualizar_ficha_veiculo()
            self._atualizar_tabela_historico(veiculo.placa)
            self._preparar_nova_os_memoria()
        else:
            if messagebox.askyesno("Não Encontrado", f"Placa {placa.upper()} não encontrada.\nDeseja iniciar o cadastro agora?"):
                self._janela_novo_atendimento(placa_padrao=placa)

    def _atualizar_ficha_veiculo(self):
        if self.veiculo_ativo and self.cliente_ativo:
            texto = (f"Veículo: {self.veiculo_ativo.marca_modelo} ({self.veiculo_ativo.ano})\n"
                     f"Placa: {self.veiculo_ativo.placa} | KM: {self.veiculo_ativo.quilometragem:,}\n"
                     f"Cliente: {self.cliente_ativo.nome}\n"
                     f"WhatsApp: {self.cliente_ativo.telefone}")
            self.lbl_info_carro.configure(text=texto, text_color=COR_TEXTO)
        else:
            self.lbl_info_carro.configure(text="Nenhum veículo selecionado.", text_color=COR_MUTED)

    def _atualizar_tabela_historico(self, placa: str):
        for l in self.tab_hist.get_children(): self.tab_hist.delete(l)
        for r in self.repo.historico_manutencoes_veiculo(placa):
            self.tab_hist.insert("", "end", values=(r["data_abertura"], r["mecanico"], r["descricao"], f"R$ {r['subtotal']:.2f}"))

    def _janela_novo_atendimento(self, placa_padrao=""):
        janela = ctk.CTkToplevel(self)
        janela.title("Novo Atendimento"); janela.geometry("420x320")
        janela.configure(fg_color=COR_FUNDO); janela.grab_set()
        janela.attributes("-topmost", True); janela.lift()
        container = ctk.CTkFrame(janela, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        def modo_busca():
            for w in container.winfo_children(): w.destroy()
            ctk.CTkLabel(container, text="Buscar Veículo", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_LARANJA).pack(pady=(10, 10))
            ent_placa_busca = ctk.CTkEntry(container, placeholder_text="Digite a Placa", width=250)
            ent_placa_busca.insert(0, placa_padrao); ent_placa_busca.pack(pady=10)

            def buscar():
                placa = ent_placa_busca.get().strip()
                veiculo = self.repo.obter_veiculo_por_placa(placa)
                if veiculo:
                    self.veiculo_ativo = veiculo
                    self.cliente_ativo = self.repo.obter_cliente_por_id(veiculo.cliente_id)
                    self._atualizar_ficha_veiculo(); self._atualizar_tabela_historico(veiculo.placa)
                    self._preparar_nova_os_memoria(); janela.destroy()
                else:
                    messagebox.showinfo("Não Encontrado", "Placa não cadastrada. Preencha os dados abaixo.")
                    modo_cadastro(placa)

            ctk.CTkButton(container, text="Buscar", fg_color=COR_LARANJA, command=buscar).pack(pady=10)

        def modo_cadastro(placa_ini=""):
            for w in container.winfo_children(): w.destroy()
            ctk.CTkLabel(container, text="Cadastro Rápido", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_VERDE).pack(pady=(5, 5))
            e_nome = ctk.CTkEntry(container, placeholder_text="Nome do Cliente", width=350); e_nome.pack(pady=2)
            e_tel = ctk.CTkEntry(container, placeholder_text="WhatsApp", width=350); e_tel.pack(pady=2)
            e_cpf = ctk.CTkEntry(container, placeholder_text="CPF/CNPJ", width=350); e_cpf.pack(pady=2)
            e_placa = ctk.CTkEntry(container, placeholder_text="Placa", width=350); e_placa.insert(0, placa_ini); e_placa.pack(pady=2)
            e_mod = ctk.CTkEntry(container, placeholder_text="Marca/Modelo", width=350); e_mod.pack(pady=2)
            e_ano = ctk.CTkEntry(container, placeholder_text="Ano", width=350); e_ano.pack(pady=2)
            e_km = ctk.CTkEntry(container, placeholder_text="KM Atual", width=350); e_km.pack(pady=2)

            def salvar_e_iniciar():
                try:
                    cli = Cliente(e_nome.get().strip(), e_tel.get().strip(), e_cpf.get().strip())
                    cli_id = self.repo.salvar_cliente(cli)
                    carro = Veiculo(e_placa.get().strip(), e_mod.get().strip(), int(e_ano.get() or 2000), int(e_km.get() or 0), cliente_id=cli_id)
                    self.repo.salvar_veiculo(carro)
                    self.veiculo_ativo = self.repo.obter_veiculo_por_placa(carro.placa)
                    # Recarrega o cliente do banco para garantir o id persistido
                    # (antes ficava None e o salvamento da OS estourava NOT NULL)
                    self.cliente_ativo = self.repo.obter_cliente_por_id(cli_id)
                    self._atualizar_ficha_veiculo(); self._atualizar_tabela_historico(self.veiculo_ativo.placa)
                    self._preparar_nova_os_memoria(); janela.destroy()
                    messagebox.showinfo("Sucesso", "Cadastro concluído! Orçamento pronto.")
                except ValueError as e: messagebox.showerror("Erro de Cadastro", str(e))

            ctk.CTkButton(container, text="Salvar e Iniciar Orçamento", fg_color=COR_VERDE, command=salvar_e_iniciar).pack(pady=10)

        modo_busca()

    def _preparar_nova_os_memoria(self):
        try:
            mec_id = int(self.cb_mecanicos.get().split(" - ")[0]); mecanico = self.repo.obter_mecanico_por_id(mec_id)
        except Exception: mecanico = None
        self.os_ativa = OrdemServico(0, self.veiculo_ativo, self.cliente_ativo, datetime.now().strftime("%d/%m/%Y"), "Orçamento", mecanico)
        self.lbl_os_titulo.configure(text=f"NOVO ORÇAMENTO - [{self.veiculo_ativo.placa}]")
        self._recarregar_tabela_itens_os()

    def _os_finalizada_imutavel(self) -> bool:
        """OS Finalizada é documento financeiro: só volta a ser editável reabrindo o status e salvando."""
        if self.os_ativa and self.os_ativa.status == "Finalizado":
            messagebox.showerror(
                "OS Finalizada",
                "Uma OS finalizada é um documento financeiro imutável.\n"
                "Mude o status para outro valor e clique em 'Salvar Estado' para voltar a editá-la.")
            return True
        return False

    def _adicionar_item_memoria(self):
        if not self.os_ativa or not self.veiculo_ativo: messagebox.showwarning("Aviso", "Inicie um atendimento primeiro."); return
        if self._os_finalizada_imutavel(): return
        desc = self.ent_item_desc.get().strip(); qtd_s = self.ent_item_qtd.get().strip(); val_s = self.ent_item_valor.get().strip()
        if not desc or not qtd_s or not val_s: messagebox.showwarning("Aviso", "Preencha todos os campos do item."); return

        try:
            qtd = float(qtd_s.replace(",", ".")); val = float(val_s.replace(",", "."))
            if self.var_tipo_item.get() == "PECA":
                # A baixa no estoque acontece ao SALVAR a OS (transacional). Aqui validamos
                # a disponibilidade apenas para dar feedback imediato ao usuário.
                dados = self.repo.obter_dados_peca(desc)
                disponivel = int(dados["quantidade"]) if dados else 0
                if int(qtd) > disponivel:
                    messagebox.showerror("Estoque Insuficiente", f"Disponível: {disponivel} unidade(s) de '{desc}'.")
                    return
                item = Peca(descricao=desc, quantidade=qtd, valor_unitario=val)
            else:
                item = MaoDeObra(descricao=desc, horas=qtd, valor_hora=val, mecanico=self.os_ativa.mecanico_principal)
            self.os_ativa.adicionar_item(item)
            if isinstance(self.ent_item_desc, ctk.CTkEntry): self.ent_item_desc.delete(0, "end")
            self.ent_item_qtd.delete(0, "end"); self.ent_item_valor.delete(0, "end")
            self._recarregar_tabela_itens_os()
        except ValueError: messagebox.showerror("Erro", "Valores inválidos.")

    def _recarregar_tabela_itens_os(self):
        for l in self.tab_itens_os.get_children(): self.tab_itens_os.delete(l)
        if self.os_ativa:
            for item in self.os_ativa.itens:
                t = "PEÇA" if isinstance(item, Peca) else "SERVIÇO"
                self.tab_itens_os.insert("", "end", values=(t, item.descricao, f"{item.quantidade:.1f}", f"R$ {item.valor_unitario:.2f}", f"R$ {item.calcular_subtotal():.2f}"))
            self.lbl_total_os.configure(text=f"TOTAL: R$ {self.os_ativa.calcular_total_liquido():.2f}")

    def _salvar_estado_os(self):
        if not self.os_ativa: return
        if not self.os_ativa.itens and self.os_ativa.numero_os == 0: messagebox.showwarning("Aviso", "Adicione pelo menos um item antes de salvar a OS."); return
        self.os_ativa.status = self.cb_status.get()
        try: self.os_ativa.mecanico_principal = self.repo.obter_mecanico_por_id(int(self.cb_mecanicos.get().split(" - ")[0]))
        except Exception: pass
        if self.os_ativa.numero_os == 0:
            try:
                self.os_ativa.numero_os = self.repo.criar_ordem_servico(self.os_ativa)
            except ValueError as e:
                messagebox.showerror("Erro ao Salvar", f"A OS não foi criada.\n{e}")
                return
        try:
            self.repo.salvar_itens_e_fechamento_os(self.os_ativa)
        except ValueError as e:
            messagebox.showerror("Estoque Insuficiente", f"A OS não foi salva.\n{e}\n\nDica: remova ou reduza a quantidade de peças acima do saldo disponível.")
            return
        self.lbl_os_titulo.configure(text=f"OS #{self.os_ativa.numero_os:04d} - [{self.os_ativa.veiculo.placa}]")
        self._recarregar_patio()
        messagebox.showinfo("Sucesso", "OS salva no sistema!")
        if self.os_ativa.status == "Finalizado":
            self._pedir_km_final()

    def _pedir_km_final(self):
        """Ao finalizar a OS, oferece a atualização da quilometragem do veículo (usa o método do domínio)."""
        if not self.veiculo_ativo: return
        dlg = ctk.CTkInputDialog(
            title="Atualizar Quilometragem",
            text=f"OS finalizada!\n\nVeículo: {self.veiculo_ativo.marca_modelo} ({self.veiculo_ativo.placa})\nKM registrada: {self.veiculo_ativo.quilometragem:,} km\n\nDigite a KM atual do veículo (vazio para não alterar):")
        entrada = (dlg.get_input() or "").strip()
        if not entrada: return
        try:
            nova_km = int(entrada.replace(".", "").replace(",", ""))
            if self.veiculo_ativo.atualizar_km(nova_km):
                self.repo.atualizar_km_veiculo(self.veiculo_ativo.id, nova_km)
                self._atualizar_ficha_veiculo()
                messagebox.showinfo("Sucesso", f"KM atualizada para {nova_km:,} km.")
            else:
                messagebox.showwarning("Aviso", "A KM informada é menor que a registrada. Nada foi alterado.")
        except ValueError:
            messagebox.showwarning("Aviso", "KM inválida. A quilometragem foi mantida.")

    def _aplicar_desconto(self):
        if not self.os_ativa: return
        if self._os_finalizada_imutavel(): return
        try:
            valor = float(self.ent_desconto.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Desconto inválido: digite um número (ex: 25.50).")
            return
        if not self.os_ativa.aplicar_desconto(valor):
            messagebox.showwarning("Desconto inválido", "O desconto não pode ser negativo nem maior que o total bruto da OS.")
            return
        self._recarregar_tabela_itens_os()
        if self.os_ativa.numero_os > 0:
            try:
                self.repo.salvar_itens_e_fechamento_os(self.os_ativa); self._recarregar_patio()
            except ValueError as e:
                messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    def _abrir_os_pelo_numero(self, numero_os: int):
        self.os_ativa = self.repo.carregar_ordem_completa(numero_os)
        if not self.os_ativa: return
        self.veiculo_ativo, self.cliente_ativo = self.os_ativa.veiculo, self.os_ativa.cliente
        self._atualizar_ficha_veiculo(); self._atualizar_tabela_historico(self.veiculo_ativo.placa)
        self.lbl_os_titulo.configure(text=f"OS #{self.os_ativa.numero_os:04d} - [{self.os_ativa.veiculo.placa}]")
        self.cb_status.set(self.os_ativa.status)
        self.ent_desconto.delete(0, "end"); self.ent_desconto.insert(0, f"{self.os_ativa.desconto:.2f}")
        self._recarregar_tabela_itens_os()

    def _selecionar_os_patio(self):
        sel = self.tab_patio.selection()
        if sel: self._abrir_os_pelo_numero(int(self.tab_patio.item(sel[0], "values")[0].replace("#", "")))

    def _recarregar_patio(self):
        for l in self.tab_patio.get_children(): self.tab_patio.delete(l)
        for r in self.repo.listar_ordens_painel():
            self.tab_patio.insert("", "end", values=(f"#{r['numero_os']:04d}", r["data"], r["placa"], r["veiculo"], r["cliente"], r["status"], f"R$ {r['total_liquido']:.2f}"))

    def _remover_item_os(self):
        if not self.os_ativa: return
        if self._os_finalizada_imutavel(): return
        sel = self.tab_itens_os.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um item na tabela para remover."); return
        indice = self.tab_itens_os.index(sel[0])
        removido = self.os_ativa.remover_item(indice)
        if removido:
            self._recarregar_tabela_itens_os()
            if self.os_ativa.numero_os > 0:
                try: self.repo.salvar_itens_e_fechamento_os(self.os_ativa)
                except ValueError as e: messagebox.showerror("Erro", f"Erro ao devolver item ao estoque: {e}")
                self._recarregar_patio()

    def _emitir_pdf(self):
        if not self.os_ativa or self.os_ativa.numero_os == 0: messagebox.showwarning("Aviso", "Salve a OS antes de gerar o PDF."); return
        try:
            conf = {
                "nome": self.repo.obter_config("oficina_nome"),
                "cnpj": self.repo.obter_config("oficina_cnpj"),
                "whatsapp": self.repo.obter_config("oficina_whatsapp"),
                "endereco": self.repo.obter_config("oficina_endereco"),
            }
            dados = conf if any(str(v).strip() for v in conf.values()) else None
            caminho = self.emissor_pdf.gerar_pdf_ordem_servico(self.os_ativa, dados)
            if platform.system() == 'Windows': os.startfile(caminho)
            elif platform.system() == 'Darwin': os.system(f'open "{caminho}"')
            else: os.system(f'xdg-open "{caminho}"')
        except Exception as e: messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")

    def _abrir_pasta_documentos(self):
        """Abre no explorador a pasta de documentos versionados da OS atual."""
        if not self.os_ativa or self.os_ativa.numero_os == 0:
            messagebox.showwarning("Aviso", "Salve a OS antes de acessar seus documentos."); return
        pasta = os.path.join(self.emissor_pdf.pasta_saida, EmissorPDF.nome_pasta_os(self.os_ativa.numero_os, self.os_ativa.veiculo.placa))
        if not os.path.isdir(pasta) or not os.listdir(pasta):
            messagebox.showinfo("Sem Documentos", "Esta OS ainda não tem PDFs gerados.\nClique em 'Gerar PDF' primeiro.")
            return
        if platform.system() == "Windows": os.startfile(pasta)
        elif platform.system() == "Darwin": os.system(f'open "{pasta}"')
        else: os.system(f'xdg-open "{pasta}"')

    def _disparar_whatsapp(self):
        if self.os_ativa: webbrowser.open(self.os_ativa.gerar_link_whatsapp())

    def _janela_financeiro(self):
        if not MATPLOTLIB_DISPONIVEL: messagebox.showerror("Erro", "Instale o matplotlib: pip install matplotlib"); return
        janela = ctk.CTkToplevel(self)
        janela.title("Painel Financeiro"); janela.geometry("900x550"); janela.configure(fg_color=COR_FUNDO)
        janela.attributes("-topmost", True); janela.lift(); janela.focus_force(); janela.grab_set()
        ctk.CTkLabel(janela, text="Fluxo de Caixa (Entradas vs Saídas)", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_TEXTO).pack(pady=10)
        # Cards de resumo (usa custo_aquisicao das peças para o lucro real)
        resumo = self.repo.resumo_financeiro()
        quadro_resumo = ctk.CTkFrame(janela, fg_color="transparent")
        quadro_resumo.pack(fill="x", padx=20, pady=(0, 8))
        cards = [
            ("ENTRADAS", f"R$ {resumo['entradas']:.2f}", COR_VERDE),
            ("SAÍDAS", f"R$ {resumo['saidas']:.2f}", "#EF4444"),
            ("SALDO", f"R$ {resumo['saldo']:.2f}", COR_VERDE if resumo['saldo'] >= 0 else "#EF4444"),
            ("CUSTO DAS PEÇAS", f"R$ {resumo['custo_pecas']:.2f}", COR_LARANJA),
            ("LUCRO ESTIMADO", f"R$ {resumo['lucro_estimado']:.2f}", COR_VERDE if resumo['lucro_estimado'] >= 0 else "#EF4444"),
        ]
        for titulo, valor, cor in cards:
            card = ctk.CTkFrame(quadro_resumo, fg_color=COR_CARD, corner_radius=8, border_width=1, border_color=COR_BORDA)
            card.pack(side="left", expand=True, fill="x", padx=4)
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=10, weight="bold"), text_color=COR_MUTED).pack(pady=(8, 0))
            ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=13, weight="bold"), text_color=cor).pack(pady=(2, 8))
        dados = self.repo.obter_dados_financeiros_grafico()
        if not dados: ctk.CTkLabel(janela, text="Nenhum registro financeiro encontrado.\nFinalize uma OS ou adicione despesas.", text_color=COR_MUTED).pack(pady=50); return
        fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=COR_FUNDO); ax.set_facecolor(COR_CARD)
        meses = list(dados.keys()); entradas = [dados[m]["ENTRADA"] for m in meses]; saidas = [dados[m]["SAIDA"] for m in meses]
        x = range(len(meses)); largura = 0.35
        barras_entrada = ax.bar([i - largura/2 for i in x], entradas, width=largura, color=COR_VERDE, label='Entradas (Faturamento)')
        barras_saida = ax.bar([i + largura/2 for i in x], saidas, width=largura, color="#EF4444", label='Saídas (Despesas)')
        for barra in barras_entrada + barras_saida:
            altura = barra.get_height()
            if altura > 0: ax.annotate(f'R$ {altura:.0f}', xy=(barra.get_x() + barra.get_width() / 2, altura), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', color=COR_TEXTO, fontsize=8)
        ax.set_title("Faturamento vs Despesas por Mês", color=COR_TEXTO, pad=15); ax.set_xticks(x); ax.set_xticklabels(meses, color=COR_TEXTO); ax.tick_params(axis='y', colors=COR_TEXTO)
        ax.spines['bottom'].set_color(COR_MUTED); ax.spines['left'].set_color(COR_MUTED); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.legend(facecolor=COR_CARD, edgecolor=COR_BORDA, labelcolor=COR_TEXTO); ax.margins(x=0.15)
        canvas = FigureCanvasTkAgg(fig, master=janela); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def _janela_comissoes(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Relatório de Comissões"); janela.geometry("720x460"); janela.configure(fg_color=COR_FUNDO)
        janela.attributes("-topmost", True); janela.lift(); janela.focus_force(); janela.grab_set()
        ctk.CTkLabel(janela, text="Comissões por Mecânico", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_TEXTO).pack(pady=10)
        quadro_filtro = ctk.CTkFrame(janela, fg_color="transparent"); quadro_filtro.pack(fill="x", padx=20)
        ctk.CTkLabel(quadro_filtro, text="Período:").pack(side="left", padx=(0, 6))
        opcoes_periodo = {"Últimos 30 dias": 30, "Últimos 60 dias": 60, "Últimos 90 dias": 90, "Todo o histórico": 0}
        cb_periodo = ctk.CTkComboBox(quadro_filtro, values=list(opcoes_periodo.keys()), width=170)
        cb_periodo.set("Últimos 30 dias"); cb_periodo.pack(side="left", padx=4)
        cols_com = ("mec", "qtd", "serv", "taxa", "com")
        tree_com = ttk.Treeview(janela, columns=cols_com, show="headings")
        for c, t, w, a in zip(cols_com, ["Mecânico", "Serviços", "Total M.O. (R$)", "Comissão", "Comissão (R$)"], [180, 80, 130, 90, 120], ["w", "center", "e", "center", "e"]):
            tree_com.heading(c, text=t); tree_com.column(c, width=w, anchor=a)
        tree_com.pack(fill="both", expand=True, padx=20, pady=10)
        lbl_total = ctk.CTkLabel(janela, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_VERDE)
        lbl_total.pack(pady=(0, 12))

        def recarregar():
            for l in tree_com.get_children(): tree_com.delete(l)
            dias = opcoes_periodo.get(cb_periodo.get(), 30)
            linhas = self.repo.relatorio_comissoes(dias)
            total = 0.0
            for r in linhas:
                total += r["comissao"]
                tree_com.insert("", "end", values=(r["mecanico"], r["qtd_servicos"], f"{r['total_servicos']:.2f}", f"{r['taxa_comissao']*100:.0f}%", f"R$ {r['comissao']:.2f}"))
            lbl_total.configure(text=f"TOTAL A PAGAR EM COMISSÕES: R$ {total:.2f}")

        cb_periodo.configure(command=lambda _: recarregar())
        recarregar()

    def _janela_gerenciamento(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Gerenciar Cadastros"); janela.geometry("650x450"); janela.configure(fg_color=COR_FUNDO)
        janela.attributes("-topmost", True); janela.lift(); janela.grab_set()
        tabview = ctk.CTkTabview(janela); tabview.pack(fill="both", expand=True, padx=10, pady=10)
        tab_mec = tabview.add("Mecânicos"); tab_cli = tabview.add("Clientes / Veículos"); tab_est = tabview.add("Estoque de Peças"); tab_ofi = tabview.add("Oficina")

        e_mec_nome = ctk.CTkEntry(tab_mec, placeholder_text="Nome", width=200); e_mec_nome.pack(pady=5)
        e_mec_esp = ctk.CTkEntry(tab_mec, placeholder_text="Especialidade", width=200); e_mec_esp.pack(pady=5)
        e_mec_tel = ctk.CTkEntry(tab_mec, placeholder_text="WhatsApp (DDD+numero)", width=200); e_mec_tel.pack(pady=5)
        e_mec_taxa = ctk.CTkEntry(tab_mec, placeholder_text="Comissão (%) - ex: 20", width=200); e_mec_taxa.insert(0, "20"); e_mec_taxa.pack(pady=5)
        def add_mec():
            try:
                taxa = float(e_mec_taxa.get().replace(",", ".")) / 100
            except ValueError:
                messagebox.showerror("Erro", "Comissão inválida: digite o percentual (ex: 20 para 20%)."); return
            try:
                self.repo.salvar_mecanico(Mecanico(e_mec_nome.get(), e_mec_tel.get(), e_mec_esp.get(), taxa)); self._atualizar_combo_mecanicos(); messagebox.showinfo("Sucesso", "Mecânico cadastrado!")
            except ValueError as e:
                messagebox.showerror("Erro de Cadastro", str(e))
            except Exception as e: messagebox.showerror("Erro", str(e))
        ctk.CTkButton(tab_mec, text="Adicionar Mecânico", command=add_mec).pack(pady=10)

        def atualizar_lista_cli():
            for l in tree_cli.get_children(): tree_cli.delete(l)
            with self.db.sessao() as conn:
                res = conn.cursor().execute("SELECT v.placa, v.marca_modelo, c.nome FROM veiculos v JOIN clientes c ON v.cliente_id = c.id").fetchall()
                for r in res: tree_cli.insert("", "end", values=(r["placa"], r["marca_modelo"], r["nome"]))
        tree_cli = ttk.Treeview(tab_cli, columns=("placa", "mod", "dono"), show="headings"); tree_cli.heading("placa", text="Placa"); tree_cli.heading("mod", text="Modelo"); tree_cli.heading("dono", text="Dono")
        tree_cli.pack(fill="both", expand=True, pady=5); ctk.CTkButton(tab_cli, text="Atualizar Lista", command=atualizar_lista_cli).pack(); atualizar_lista_cli()

        e_est_nome = ctk.CTkEntry(tab_est, placeholder_text="Nome da Peça", width=200); e_est_nome.pack(pady=5)
        e_est_qtd = ctk.CTkEntry(tab_est, placeholder_text="Quantidade", width=200); e_est_qtd.pack(pady=5)
        e_est_custo = ctk.CTkEntry(tab_est, placeholder_text="Preço de Custo (R$)", width=200); e_est_custo.pack(pady=5)
        e_est_margem = ctk.CTkEntry(tab_est, placeholder_text="Margem de Lucro (%)", width=200); e_est_margem.insert(0, "50"); e_est_margem.pack(pady=5)
        
        def add_estoque():
            if not e_est_nome.get().strip():
                messagebox.showerror("Erro", "Informe o nome da peça."); return
            try:
                custo = float(e_est_custo.get().replace(",", ".")); margem = float(e_est_margem.get().replace(",", "."))
                qtd = int(e_est_qtd.get())
                criou_nova = self.repo.salvar_peca_estoque(e_est_nome.get(), qtd, custo, margem)
                preco_venda = custo * (1 + margem/100)
                msg_extra = "\n(Já existia: quantidade somada ao saldo atual)" if not criou_nova else ""
                messagebox.showinfo("Sucesso", f"{'Peça cadastrada' if criou_nova else 'Estoque reposto'}!\nPreço de Venda sugerido: R$ {preco_venda:.2f}{msg_extra}")
                self._atualizar_campo_descricao(); atualizar_lista_est()
            except ValueError: messagebox.showerror("Erro", "Preencha os valores corretamente.")
        
        def atualizar_lista_est():
            for l in tree_est.get_children(): tree_est.delete(l)
            for p in self.repo.listar_estoque():
                preco_venda = p["preco_custo"] * (1 + p["margem_lucro"]/100)
                tree_est.insert("", "end", values=(p["nome"], p["quantidade"], f"R$ {p['preco_custo']:.2f}", f"{p['margem_lucro']:.0f}%", f"R$ {preco_venda:.2f}"))
                
        ctk.CTkButton(tab_est, text="Adicionar ao Estoque", command=add_estoque).pack(pady=10)
        tree_est = ttk.Treeview(tab_est, columns=("nome", "qtd", "custo", "margem", "venda"), show="headings", height=5)
        tree_est.heading("nome", text="Peça"); tree_est.heading("qtd", text="Qtd"); tree_est.heading("custo", text="Custo"); tree_est.heading("margem", text="Margem"); tree_est.heading("venda", text="Preço Venda")
        tree_est.pack(fill="both", expand=True, pady=5); ctk.CTkButton(tab_est, text="Atualizar Estoque", command=atualizar_lista_est).pack(); atualizar_lista_est()

        # --- ABA OFICINA (configurações usadas no PDF) ---
        ctk.CTkLabel(tab_ofi, text="Dados da Oficina (aparecem nos orçamentos PDF)", font=ctk.CTkFont(size=13, weight="bold"), text_color=COR_LARANJA).pack(pady=(10, 6))
        e_ofi_nome = ctk.CTkEntry(tab_ofi, placeholder_text="Nome da Oficina", width=320); e_ofi_nome.insert(0, self.repo.obter_config("oficina_nome")); e_ofi_nome.pack(pady=4)
        e_ofi_cnpj = ctk.CTkEntry(tab_ofi, placeholder_text="CNPJ", width=320); e_ofi_cnpj.insert(0, self.repo.obter_config("oficina_cnpj")); e_ofi_cnpj.pack(pady=4)
        e_ofi_whats = ctk.CTkEntry(tab_ofi, placeholder_text="WhatsApp de Contato", width=320); e_ofi_whats.insert(0, self.repo.obter_config("oficina_whatsapp")); e_ofi_whats.pack(pady=4)
        e_ofi_end = ctk.CTkEntry(tab_ofi, placeholder_text="Endereço", width=320); e_ofi_end.insert(0, self.repo.obter_config("oficina_endereco")); e_ofi_end.pack(pady=4)
        def salvar_oficina():
            self.repo.salvar_config("oficina_nome", e_ofi_nome.get().strip())
            self.repo.salvar_config("oficina_cnpj", e_ofi_cnpj.get().strip())
            self.repo.salvar_config("oficina_whatsapp", e_ofi_whats.get().strip())
            self.repo.salvar_config("oficina_endereco", e_ofi_end.get().strip())
            messagebox.showinfo("Sucesso", "Dados da oficina salvos!")
        ctk.CTkButton(tab_ofi, text="Salvar Configurações", fg_color=COR_VERDE, command=salvar_oficina).pack(pady=12)

if __name__ == "__main__":
    app = AplicacaoOficinaPro()
    app.mainloop()