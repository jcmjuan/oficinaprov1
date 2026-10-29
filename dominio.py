"""
Oficina Pro v1.0 - Classes de Domínio (POO)
Arquivo: dominio.py
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import urllib.parse

class Pessoa(ABC):
    def __init__(self, nome: str, telefone: str):
        self._nome = nome
        self._telefone = ""
        if self.__validar_telefone(telefone):
            self._telefone = telefone
        else:
            self._telefone = telefone 

    def __validar_telefone(self, telefone: str) -> bool:
        digitos = "".join(filter(str.isdigit, telefone))
        return len(digitos) in (10, 11)

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def telefone(self) -> str:
        return self._telefone

    @abstractmethod
    def obter_resumo(self) -> str:
        pass

class Cliente(Pessoa):
    def __init__(self, nome: str, telefone: str, cpf_cnpj: str, id_cliente: Optional[int] = None):
        super().__init__(nome, telefone)
        self.id = id_cliente
        if not cpf_cnpj.strip():
            raise ValueError("CPF/CNPJ não pode ser vazio.")
        self.__cpf_cnpj = cpf_cnpj
        self.veiculos: List['Veiculo'] = []

    @property
    def cpf_cnpj(self) -> str:
        return self.__cpf_cnpj

    def adicionar_veiculo(self, veiculo: 'Veiculo') -> None:
        if veiculo not in self.veiculos:
            self.veiculos.append(veiculo)

    def obter_resumo(self) -> str:
        return f"Cliente: {self.nome} | Whats: {self.telefone} | CPF/CNPJ: {self.__cpf_cnpj}"

class Mecanico(Pessoa):
    def __init__(self, nome: str, telefone: str, especialidade: str, taxa_comissao: float, id_mecanico: Optional[int] = None):
        super().__init__(nome, telefone)
        self.id = id_mecanico
        self.__especialidade = especialidade
        self.__taxa_comissao = taxa_comissao

    @property
    def especialidade(self) -> str:
        return self.__especialidade

    @property
    def taxa_comissao(self) -> float:
        return self.__taxa_comissao

    def calcular_comissao(self, valor_servico: float) -> float:
        return valor_servico * self.__taxa_comissao

    def obter_resumo(self) -> str:
        return f"Mecânico: {self.nome} ({self.__especialidade}) | Comissão: {self.__taxa_comissao * 100:.0f}%"

class Veiculo:
    def __init__(self, placa: str, marca_modelo: str, ano: int, quilometragem: int, cliente_id: Optional[int] = None, id_veiculo: Optional[int] = None):
        self.id = id_veiculo
        self.cliente_id = cliente_id
        self.__placa = self.__formatar_placa(placa)
        self.marca_modelo = marca_modelo
        self.ano = ano
        self.__quilometragem = quilometragem

    def __formatar_placa(self, placa: str) -> str:
        return placa.replace("-", "").replace(" ", "").upper()

    @property
    def placa(self) -> str:
        return self.__placa

    @property
    def quilometragem(self) -> int:
        return self.__quilometragem

    def atualizar_km(self, nova_km: int) -> bool:
        if nova_km >= self.__quilometragem:
            self.__quilometragem = nova_km
            return True
        return False

    def __str__(self) -> str:
        return f"{self.__placa} - {self.marca_modelo} ({self.ano}) - {self.__quilometragem:,} km"

class ItemOS(ABC):
    def __init__(self, descricao: str, quantidade: float, valor_unitario: float):
        self._descricao = descricao
        self._quantidade = quantidade
        self._valor_unitario = valor_unitario

    @property
    def descricao(self) -> str:
        return self._descricao

    @property
    def quantidade(self) -> float:
        return self._quantidade

    @property
    def valor_unitario(self) -> float:
        return self._valor_unitario

    @abstractmethod
    def calcular_subtotal(self) -> float:
        pass

class Peca(ItemOS):
    def __init__(self, descricao: str, quantidade: float, valor_unitario: float, codigo_sku: str = "GEN", custo_aquisicao: float = 0.0):
        super().__init__(descricao, quantidade, valor_unitario)
        self.codigo_sku = codigo_sku
        self.__custo_aquisicao = custo_aquisicao

    @property
    def custo_aquisicao(self) -> float:
        # Getter público para respeitar o encapsulamento
        return self.__custo_aquisicao

    def calcular_subtotal(self) -> float:
        return self._quantidade * self._valor_unitario

class MaoDeObra(ItemOS):
    def __init__(self, descricao: str, horas: float, valor_hora: float, mecanico: Mecanico):
        super().__init__(descricao, horas, valor_hora)
        self.mecanico_responsavel: Mecanico = mecanico

    def calcular_subtotal(self) -> float:
        return self._quantidade * self._valor_unitario

    def obter_comissao_item(self) -> float:
        return self.mecanico_responsavel.calcular_comissao(self.calcular_subtotal())

class OrdemServico:
    def __init__(self, numero_os: int, veiculo: Veiculo, cliente: Cliente, data_abertura: str, status: str = "Orçamento", mecanico_principal: Optional[Mecanico] = None):
        self.numero_os = numero_os
        self.veiculo = veiculo
        self.cliente = cliente
        self.data_abertura = data_abertura
        self.status = status
        self.mecanico_principal = mecanico_principal
        self.itens: List[ItemOS] = []
        self.__desconto: float = 0.0

    @property
    def desconto(self) -> float:
        return self.__desconto

    def adicionar_item(self, item: ItemOS) -> None:
        self.itens.append(item)

    def aplicar_desconto(self, valor: float) -> bool:
        if 0 <= valor <= self.calcular_total_bruto():
            self.__desconto = valor
            return True
        return False

    def calcular_total_bruto(self) -> float:
        return sum(item.calcular_subtotal() for item in self.itens)

    def calcular_total_liquido(self) -> float:
        return max(0.0, self.calcular_total_bruto() - self.__desconto)

    def gerar_link_whatsapp(self) -> str:
        tipo_doc = "ORÇAMENTO" if self.status == "Orçamento" else "ORDEM DE SERVIÇO"
        mecanico_txt = f"\n*Responsável Técnico:* {self.mecanico_principal.nome}" if self.mecanico_principal else ""
        
        itens_txt = ""
        for i in self.itens:
            itens_txt += f"\n• {i.descricao} ({i.quantidade:.1f}x) - R$ {i.calcular_subtotal():.2f}"

        msg = (
            f"*OFICINA PRO - {tipo_doc} #{self.numero_os:04d}*\n"
            f"Olá, {self.cliente.nome}!\n"
            f"-----------------------------------------\n"
            f"*Veículo:* {self.veiculo.marca_modelo} (Placa: {self.veiculo.placa})\n"
            f"*KM Atual:* {self.veiculo.quilometragem:,} km"
            f"{mecanico_txt}\n"
            f"*Status:* {self.status.upper()}\n"
            f"-----------------------------------------"
            f"\n*Itens Lançados:*{itens_txt}\n"
            f"-----------------------------------------\n"
            f"Subtotal: R$ {self.calcular_total_bruto():.2f}\n"
            f"Desconto: R$ {self.__desconto:.2f}\n"
            f"*VALOR TOTAL: R$ {self.calcular_total_liquido():.2f}*\n\n"
            f"Poderia nos confirmar a aprovação deste atendimento?"
        )
        msg_cod = urllib.parse.quote(msg)
        return f"https://wa.me/55{self.cliente.telefone}?text={msg_cod}"