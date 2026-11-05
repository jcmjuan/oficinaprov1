# OficinaPro — Guia de Explicação do Projeto (Estudo para Apresentação)

> **Objetivo deste documento:** mapear CADA conceito de Orientação a Objetos exigido pelo professor
> para o lugar exato onde ele acontece no código, com o trecho real e a forma de explicar em voz alta.
> Use-o como "roteiro de defesa": quando o professor apontar para um requisito, você sabe a linha exata.

---

## 1. Visão geral — a história de 60 segundos

> 🔊 **Roteiro de abertura:** "O OficinaPro atende oficinas de bairro que ainda usam caderno: o sistema
> formaliza orçamentos e ordens de serviço, baixa estoque de forma transacional, calcula comissão dos
> mecânicos, emite PDF versionado e manda a Mensagem no WhatsApp. É 100% Python orientado a objetos:
> o domínio é um modelo de classes puro, a persistência é SQLite, e a interface é CustomTkinter."

| Camada | Arquivo | Papel |
|---|---|---|
| Domínio (regras de negócio) | `dominio.py` | 8 classes de POO pura — o coração do projeto |
| Persistência | `banco.py` | `GerenciadorBanco` (transações) + `RepositorioOficina` (CRUD) |
| Documentos | `relatorios.py` | `EmissorPDF` — geração e versionamento de PDFs |
| Interface | `app.py` | GUI CustomTkinter — só orquestra, as regras ficam no domínio |
| Dados de demonstração | `seed.py` | popula o banco para a demo |
| Testes | `test_dominio.py` | 23 testes automatizados (`unittest`) |

**Regra de ouro da arquitetura (fale isso):** a GUI não sabe SQL e o banco não conhece a GUI. A única
ponte entre os mundos são **objetos de domínio** (`Cliente`, `Veiculo`, `OrdemServico`) que entram e
saem do repositório. Isso é responsabilidade única por camada.

Como executar:

```bash
pip install -r requirements.txt
python seed.py                      # (opcional) banco de demonstração
python app.py                       # a aplicação
python -m unittest test_dominio -v  # os 23 testes
```

Repositório: https://github.com/jcmjuan/oficinapro

---

## 2. Requisitos POO → mapa direto para o código

Tabela-mestre para responder "onde está X?" imediatamente:

| Requisito do professor | Onde está no código | Referência |
|---|---|---|
| Classe abstrata | `Pessoa(ABC)` e `ItemOS(ABC)` com `@abstractmethod` | `dominio.py` linhas 9–36 e 108–128 |
| Herança (2 hierarquias) | `Pessoa → Cliente, Mecanico`; `ItemOS → Peca, MaoDeObra` | `dominio.py` 38 e 58; 130 e 144 |
| Polimorfismo | `obter_resumo()` e `calcular_subtotal()` sobrescritos; chamados via classe-mãe | `OrdemServico.calcular_total_bruto()` (linha 190) itera `item.calcular_subtotal()` sem saber o tipo |
| Associação entre classes | `OrdemServico ↔ Cliente/Veiculo/Mecanico/ItemOS`; `MaoDeObra → Mecanico` | `dominio.py` 158–165 e 147 |
| Encapsulamento (método privado) | `Pessoa.__validar_telefone()`; `Veiculo.__formatar_placa()` | `dominio.py` 18 e 88 |
| Encapsulamento (atributo privado) | `__desconto`, `__placa`, `__custo_aquisicao`, `__caminho_db`, etc. | toda a classe `OrdemServico` |
| Getter/comportamento controlado | `@property` em nome, telefone, placa, quilometragem, desconto | `dominio.py` 26–32, 91–97 |
| `main` cria objetos | A GUI cria objetos de TODAS as classes; os testes também demonstram isso de forma determinística | `app.py` / `test_dominio.py` |
| Bibliotecas externas | `customtkinter`, `reportlab`, `matplotlib`, `Pillow` | habitual, ver seção 9 |

---

## 3. Cada classe de domínio em detalhe

### 3.1 `Pessoa` — a classe abstrata base (`dominio.py`, linhas 9–36)

```python
class Pessoa(ABC):
    def __init__(self, nome: str, telefone: str):
        if not nome.strip():
            raise ValueError("Nome não pode ser vazio.")
        self._nome = nome.strip()
        if not self.__validar_telefone(telefone):
            raise ValueError("Telefone inválido. Informe DDD + número (10 ou 11 dígitos).")
        ...

    def __validar_telefone(self, telefone: str) -> bool:   # método PRIVADO
        digitos = "".join(filter(str.isdigit, telefone))
        return len(digitos) in (10, 11)

    @abstractmethod
    def obter_resumo(self) -> str: ...
```

**Explicação:**
- `ABC` (Abstract Base Class, do módulo `abc`) torna `Pessoa` **abstrata**: não dá para instanciar
  `Pessoa("João", "999")` diretamente — o Python levanta `TypeError` porque ela deixa um método
  abstrato sem implementação. Isso **força** toda filha a implementar `obter_resumo()`.
- O construtor já **valida no momento da criação** ("objetos válidos desde o nascimento"): nome vazio
  ou telefone sem 10/11 dígitos interrompem a criação com `ValueError`. Teste: `test_validacao_telefone_invalido`,
  `test_validacao_nome_vazio`.
- `__validar_telefone` é o **método privado** exigido: o duplo sublinhado ativa o *name mangling* do
  Python (na memória vira `_Pessoa__validar_telefone`), que impede o acesso acidental de fora.

> 🔊 **Ideia central:** "`Pessoa` é abstrata porque especialidade e documento fiscal só fazem sentido
> para uma subclasse concreta. Ela garante contrato: qualquer Pessoa SABE se resumir e chega válida."

### 3.2 `Cliente(Pessoa)` e `Mecanico(Pessoa)` — a primeira hierarquia (38–77)

```python
class Cliente(Pessoa):
    def __init__(self, nome: str, telefone: str, cpf_cnpj: str, id_cliente=None):
        super().__init__(nome, telefone)          # reaproveita a validação da mãe
        ...
        self.__cpf_cnpj = cpf_cnpj                # atributo privado
        self.veiculos: List['Veiculo'] = []       # associação 1..* com Veiculo

    def adicionar_veiculo(self, veiculo: 'Veiculo') -> None: ...

    def obter_resumo(self) -> str:                #sobrescrita (override)
        return f"Cliente: {self.nome} | Whats: {self.telefone} ..."
```

**Explicação:**
- `super().__init__` demonstra **reaproveitamento de construtor**: a validação de nome/telefone
  sempre da `Pessoa`, em cliente e mecânico — o mesmo código é executado para os dois.
- Cada filha **adiciona** o que lhe é próprio: `Cliente` tem CPF/CNPJ e a lista de veículos;
  `Mecanico` tem especialidade, taxa de comissão e `calcular_comissao(valor)`.
- As duas **sobrescrevem** `obter_resumo()` — mesmo nome, comportamentos diferentes (polimorfismo).

> 🔊 **Ideia central:** "Cliente e Mecânico compartilham o que é comum (ser pessoa) e cada um
> especializa o que é próprio: o cliente tem veículos, o mecânico tem comissão."

### 3.3 `Veiculo` — encapsulamento de estado mutável (79–106)

```python
class Veiculo:
    def __init__(self, ...):
        self.__placa = self.__formatar_placa(placa)   # normaliza ANTES de guardar
        self.__quilometragem = quilometragem

    def atualizar_km(self, nova_km: int) -> bool:
        if nova_km >= self.__quilometragem:           # trava de não-regressão
            self.__quilometragem = nova_km
            return True
        return False
```

**Explicação:**
- A placa é privada e chega **normalizada** (`ABC-1D23` → `ABC1D23`) por um método privado — o banco
  nunca vê dois formatos da mesma placa.
- `atualizar_km` é o melhor exemplo de **invariante de objeto**: quilometragem de um carro nunca
  diminui. A GUI chama este método ao finalizar a OS; se tentar digitar um KM menor, o método recusa
  (retorna `False`) e o estado fica intacto. Teste: `test_km_nao_regressa`.
- Também sobrescreve `__str__` (método "dunder"): `print(veiculo)` mostra a ficha formatada — é
  polimorfismo com métodos especiais do Python.

### 3.4 `ItemOS` — a segunda hierarquia, o coração financeiro (108–155)

```python
class ItemOS(ABC):
    def __init__(self, descricao, quantidade, valor_unitario):
        ...  # estado comum a toda linha cobrável

    @abstractmethod
    def calcular_subtotal(self) -> float: ...

class Peca(ItemOS):
    def calcular_subtotal(self) -> float:
        return self._quantidade * self._valor_unitario          # qtd × preço

class MaoDeObra(ItemOS):
    def calcular_subtotal(self) -> float:                       # mesma fórmula...
        return self._quantidade * self._valor_unitario
    def obter_comissao_item(self) -> float:                     # ...mais o comportamento próprio
        if not self.mecanico_responsavel:
            return 0.0
        return self.mecanico_responsavel.calcular_comissao(self.calcular_subtotal())
```

**Explicação:**
- O professor pede "5 classes": este desenho resolve *duas* hierarquias de herança no mesmo projeto —
  pessoas (`Pessoa`) e itens cobráveis (`ItemOS`).
- `OrdemServico` guarda `List[ItemOS]`: ela só conhece o **contrato** (`calcular_subtotal`), nunca o
  tipo concreto. Quando um dia entrar um `PacoteServicos` com preço fechado, `calcular_total_bruto`
  continua funcionando sem mudar uma linha — **aberto para extensão, fechado para modificação**.
- `MaoDeObra` demonstra **associação + delegação**: ela aponta para o `Mecanico` responsável e
  **delega** o cálculo a ele (`mecanico.calcular_comissao(...)`). A taxa não fica duplicada no item —
  ela vive no dono da regra. Teste: `test_comissao_sem_mecanico_retorna_zero` (item sem mecânico
  comisiona zero, sem erro).

### 3.5 `OrdemServico` — o agregador (157–225)

```python
class OrdemServico:
    def __init__(self, numero_os, veiculo: Veiculo, cliente: Cliente, ...):
        self.veiculo = veiculo             # associação (referências a objetos inteiros)
        self.cliente = cliente
        self.mecanico_principal = mecanico_principal
        self.itens: List[ItemOS] = []      # agregação 1..*
        self.__desconto: float = 0.0       # atributo PRIVADO, com acesso controlado

    def aplicar_desconto(self, valor: float) -> bool:
        if 0 <= valor <= self.calcular_total_bruto():   # regra de negócio
            self.__desconto = valor
            return True
        return False                                     # recusa desconto inválido

    def calcular_total_bruto(self) -> float:
        return sum(item.calcular_subtotal() for item in self.itens)   # POLIMORFISMO em ação

    def calcular_total_liquido(self) -> float:
        return max(0.0, self.calcular_total_bruto() - self.__desconto)
```

**Explicação:**
- `OrdemServico` é o exemplo clássico de **objeto que agrega**: fecha em si as associações com
  Cliente, Veiculo, Mecanico e uma lista de ItemOS. É a "nota fiscal" do mundo dos objetos.
- `aplicar_desconto` devolve `bool` em vez de lançar exceção: é API pensada para a GUI — a interface
  mostra um aviso quando é recusado. Regras: desconto negativo ou acima do total bruto é recusado.
- O par **privado + property** (`__desconto` só alterável por `aplicar_desconto`/`definir_desconto_salvo`)
  impede que qualquer tela invente um desconto que viole a regra.
- `gerar_link_whatsapp()` (196–225) mostra o domínio produzindo valor real fora do banco de dados:
  monta a mensagem com totais, codifica a URL (`urllib.parse.quote`) e devolve o link `wa.me`.

---

## 4. Relações entre classes (o que o UML mostra)

| Relação | Tipo (UML) | Onde no código | Multiplicidade |
|---|---|---|---|
| `Pessoa` ◄── `Cliente`, `Mecanico` | **herança/especialização** | `class Cliente(Pessoa)` | 1 mãe, N filhas |
| `ItemOS` ◄── `Peca`, `MaoDeObra` | **herança/especialização** | `class Peca(ItemOS)` | 1 mãe, N filhas |
| `Cliente` ── `Veiculo` | **associação 1..*** | `Cliente.veiculos: List[Veiculo]`; `Veiculo.cliente_id` | 1 cliente : 0..* veículos |
| `OrdemServico` ── `Cliente` / `Veiculo` | **associação** | referências `self.cliente`, `self.veiculo` | cada OS: 1 cliente + 1 veículo |
| `OrdemServico` ◇── `ItemOS` | **agregação** (lista) | `self.itens: List[ItemOS]` | 1 OS : 0..* itens |
| `MaoDeObra` → `Mecanico` | **associação/delegação** | `self.mecanico_responsavel` | 0..1 mecânico por item |
| `OrdemServico` → `Mecanico` | **associação opcional** | `self.mecanico_principal` | 0..1 |

**Diferença agregação × composição para citar se questionarem:** os itens existem *juntos* da OS
(não podem ser reutilizados em outra OS depois de fechada), mas no modelo de objetos a OS não é dona
do ciclo de vida no banco — os itens são linhas da tabela `itens_os` ligadas por foreign key
(`ON DELETE CASCADE` no schema é a "composição" no nível de dados). No diagrama do domínio desenhamos
agregação com losango na `OrdemServico`.

> 🔊 **Explicação:** "As setas de herança são 'é-um' (Cliente É-UMA Pessoa, Peça É-UM Item);
> as linhas simples são 'tem-um' (OS TEM-UM cliente, TEM-N itens)."

---

## 5. Os dois conceitos de encapsulamento, lado a lado

| Recurso Python | Exemplo no projeto | Efeito |
|---|---|---|
| `__atributo` (duplo sublinhado) | `Pessoa.__cpf_cnpj`, `OrdemServico.__desconto`, `Veiculo.__placa`, `Peca.__custo_aquisicao`, `GerenciadorBanco.__caminho_db` | *name mangling*: acesso externo direto falha; só entra pela "porta da frente" |
| `@property` | `nome`, `telefone`, `placa`, `quilometragem`, `desconto`, `custo_aquisicao` | getter público de leitura; gravação só por métodos de regra |
| Método privado | `__validar_telefone`, `__formatar_placa` | detalhe de implementação invisível para quem usa a classe |

**Demonstração prática:**
`v = cliente.veiculos[0]; v.__placa` → `AttributeError`; `v.placa` → porta correta, valor formatado.

---

## 6. Fluxo completo do sistema (conta em ordem para a demo)

1. **Cadastro rápido:** cliente preenchido → `Cliente(...)` valida telefone → `repositorio.salvar_cliente()`
   devolve o `id` do banco → o objeto é recarregado do banco com o id ("cliente recarregado" — corrige
   o caso em que um cliente recém-criado ainda não tinha id e a OS não poderia ser gravada).
2. **Abertura da OS:** `OrdemServico(numero, veiculo, cliente, ...)` em memória; itens entram via
   `adicionar_item` (polimórfico: aceita `Peca` e `MaoDeObra` indiferentemente).
   `criar_ordem_servico()` recusa OS sem cliente/veículo persistidos (erro amigável).
3. **Salvamento transacional** — `RepositorioOficina.salvar_itens_e_fechamento_os` (banco.py, 210–258).
   É o método mais importante da persistência; explique os 3 passos:
   - **(1) Restaura:** lê do banco as peças que ESTAVAM debitadas para esta OS e devolve ao estoque;
   - **(2) Debita:** grava a lista atual validando saldo peça a peça — se faltar, `raise ValueError`,
     e o `with` da conexão desfaz TUDO (rollback): nem itens, nem status, nem estoque;
   - **(3) Reconcilia o financeiro:** status `Finalizado` → insere (ou atualiza) a ENTRADA com o
     valor líquido; status voltou atrás → apaga a ENTRADA.
   > 🔊 **Frase pronta:** "Re-salvar uma OS é idempotente: o estoque sai do estado anterior e entra
   no novo estado atomicamente. Nunca se 'vaza' peça nem valor duplicado no caixa."
4. **Finalização:** status muda → prompt de KM (`Veiculo.atualizar_km` com trava) → `EmissorPDF`
   gera o documento em `documentos/OS_NNNN_PLACA/` com **status + timestamp no nome do arquivo**
   (nada é sobrescrito — cada geração é uma versão nova) → `gerar_link_whatsapp()` abre o resumo.
5. **Relatórios:** `relatorio_comissoes` agrupa mão de obra por mecânico com filtro de período;
   `resumo_financeiro` calcula saldo e lucro estimado = entradas − custo de aquisição das peças − saídas.

**Por que a comissão é correta:** o saldo de comissão vem dos `itens_os` do tipo `MAO_DE_OBRA` com o
`mecanico_id` de cada item — a taxa aplicada é a do mecânico **no momento do relatório**, e o valor
base é o subtotal do item (mesma fórmula do domínio: `quantidade × valor_unitario × taxa`).

---

## 7. O que a persistência tem de POO também

`banco.py` não é "SQL solto" — tem desenho orientado a objetos:

- **`GerenciadorBanco`** (10–105): conhece o caminho do arquivo (privado `__caminho_db`) e cria o
  schema. O destaque é o **decorador `@contextmanager`** no método `sessao()` (15–24):

  ```python
  @contextmanager
  def sessao(self):
      conn = sqlite3.connect(self.__caminho_db)
      try:
          with conn:        # commit em sucesso / rollback em exceção
              yield conn
      finally:
          conn.close()      # SEMPRE fecha, mesmo com erro
      ...
  ```

  Isso transforma a conexão em um **contexto transacional reutilizável**: todo método do repositório
  escreve `with self.db.sessao() as conn:` e ganha commit/rollback/close de graça — sem repetir
  try/finally. Vale nomear: é o padrão *Template de recurso* do Python (mesmo espírito de `open`).

- **`RepositorioOficina`** (107–...): o **Repository pattern** — uma classe com métodos de leitura/
  gravação por entidade, que DEVOLVE objetos de domínio (reconstituição): `carregar_ordem_completa`
  (188–208) reconstrói a `OrdemServico` inteira, incluindo o polimorfismo na leitura: se a linha tem
  `tipo_item == 'PECA'` cria `Peca(...)`, senão `MaoDeObra(...)` — o banco guarda o tipo, o objeto
  volta polimórfico.

- **Integridade no schema:** foreign keys (`cliente_id → clientes.id` etc.), `UNIQUE` em placa e
  CPF/CNPJ. Quando o SQLite recusa, o repositório traduz `IntegrityError` em **`ValueError` com
  mensagem amigável** ("Já existe um veículo com esta placa") — tratamento de exceção em duas camadas,
  convertido para a linguagem do usuário.

---

## 8. Bibliotecas externas (a pergunta "por que usou X?")

| Biblioteca | Por que usou (resposta para o professor) |
|---|---|
| `customtkinter` | Interface moderna com tema escuro sobre o tkinter nativo; widgets (`CTkInputDialog`, toplevels) que não existem nativos com esse acabamento |
| `tkinter.ttk` (nativo) | `Treeview` = tabelas clicáveis sem dependência extra |
| `sqlite3` (nativo) | Banco de arquivo único, sem servidor — o dono da oficina copia o `.db` e leva o negócio consigo; suporte a transação e foreign key |
| `reportlab` | Geração de PDF programática (tabelas, margens, assinatura) sem domínio público de template |
| `matplotlib` | Gráfico de barras Entradas × Saídas embutido no painel financeiro |
| `Pillow` | Carrega/redimensiona o logotipo |
| `abc` (nativo) | Classes abstratas + `@abstractmethod` |
| `typing`, `datetime`, `urllib.parse`, `webbrowser` (nativos) | anotações, datas do relatório de comissões, codificação e abertura do link `wa.me` |

---

## 9. CRUD — mapa por entidade (classificado no repositório)

| Entidade | Create | Read | Update | Delete |
|---|---|---|---|---|
| Clientes | `salvar_cliente()` | `obter_cliente_por_id()` | — (limitação) | — |
| Mecânicos | `salvar_mecanico()` | `listar_mecanicos()` / `obter_mecanico_por_id()` | `atualizar_mecanico()` | — |
| Veículos | `salvar_veiculo()` | `obter_veiculo_por_placa()` + `historico_manutencoes_veiculo()` | `atualizar_km_veiculo()` | — |
| Ordens de Serviço | `criar_ordem_servico()` | `carregar_ordem_completa()` / `listar_ordens_painel()` | `salvar_itens_e_fechamento_os()` (status, desconto, itens) | — |
| Estoque | `salvar_peca_estoque()` (soma se já existe) | `listar_estoque()` / `obter_dados_peca()` | `atualizar_peca_estoque()` | — |
| Financeiro | automático ao finalizar | `resumo_financeiro()` + dados do gráfico | ENTRADA reajustada em re-salvas | reversão automática se o status voltar |

> **Justificativa do "sem D":** registros comerciais são trilha de auditoria —
> excluir uma OS apagaria o histórico e o financeiro dele derivado. No estoque, a "exclusão" é o fluxo
> reverso natural: baixar e devolver pela própria OS. A limitação está assumida na seção de limitações.

---

## 10. Os testes: o que cada grupo prova

Execução: `python -m unittest test_dominio -v` → **23 testes em ~3 segundos**.

| Grupo | Nº | O que prova (exemplos com nomes reais dos testes) |
|---|---|---|
| Domínio | 10 | `test_heranca_e_polimorfismo` (filhas respondem ao mesmo método com resultados diferentes), `test_subtotais_polimorficos`, `test_km_nao_regressa`, `test_placa_formatada`, `test_desconto_aplicado_e_total_liquido` (aceito/rejeitado por limites), `test_remover_item` |
| Persistência | 10 | `test_baixa_e_devolucao_de_estoque` (debita ao salvar, devolve ao remover), `test_estoque_insuficiente_sustenta_os_salva` (rollback preserva o estado), `test_entrada_financeira_apos_finalizar_e_reversao`, `test_reeditacao_os_finalizada_atualiza_financeiro`, `test_relatorio_comissoes`, `test_resumo_financeiro_lucro`, `test_criar_os_sem_ids_lanca_erro_amigavel` |
| Documentos | 3 | `test_versionamento_sem_sobrescrita` (2 gerações = 2 arquivos), `test_colisao_mesmo_segundo_nao_sobrescreve`, `test_migracao_de_pdfs_antigos` (+ idempotência) |

**Exemplo de teste que prova o polimorfismo:**

```python
def test_subtotais_polimorficos(self):
    peca = Peca("Filtro", 2, 35.00)                    # 70,00
    mo = MaoDeObra("Mão de obra", 0.5, 80.00, self.mecanico)   # 40,00
    os_obj.adicionar_item(peca); os_obj.adicionar_item(mo)
    self.assertEqual(os_obj.calcular_total_bruto(), 110.00)
```

Duas classes diferentes, mesma chamada `item.calcular_subtotal()`, resultado correto para cada uma —
a OS não faz `if isinstance(...)` para somar. Este é o conceito de polimorfismo *funcionando*, não
declarado.

---

## 11. Perguntas e respostas curtas

**"Por que duas hierarquias de herança?"** — São dois eixos independentes do negócio: quem atende
(pessoas) e o que se cobra (itens). Misturar os dois numa só herança forçaria `Cliente` a ter
subtotal, o que não faz sentido. Cada eixo tem sua abstrata com seu contrato.

**"Onde está o polimorfismo de verdade, não só na teoria?"** — `OrdemServico.calcular_total_bruto()`
(dominio.py, linha 190): soma `item.calcular_subtotal()` para uma `List[ItemOS]`. E as duas
sobrescritas de `obter_resumo()` usadas nas telas via referência `Pessoa`.

**"Qual diferença entre encapsulamento por `__` e por `property`?"** — `__` esconde o dado
(name mangling); `@property` expõe leitura controlada. Juntos: `__placa` escondido + property
`placa` = ninguém escreve placa torta no objeto, porque a normalização (`__formatar_placa`) acontece
dentro da própria classe.

**"Como o sistema evita perder dinheiro se algo der errado no meio do salvamento?"** — Tudo dentro de
UMA transação (`with self.db.sessao()`): restaura estoque antigo, debita validando saldo, grava itens,
reconcilia financeiro. Qualquer exceção = rollback completo (o `with` da conexão SQLite faz isso).

**"Por que os PDFs não são sobrescritos?"** — Orçamento aprovado é documento;
regenerar seria apagar prova. Cada emissão cria arquivo com status e carimbo
`ORCAMENTO_0001_ABC1D23_20261031-1045.pdf` dentro da pasta da OS — histórico completo preservado,
com migração automática dos PDFs do formato antigo na inicialização.

**"O que falta fazer?"** (seção 12 do PDF da entrega) — edição de cliente/veículo, metadados de
"versão aprovada" de PDF, multiusuário/backup automático, testes de GUI. Dizer honestamente que a
ausência de DELETE é decisão, não esquecimento.

---

## 12. Glossário rápido (termo → tradução para o projeto)

- **Abstração** — modelar o essencial: `Peca` tem custo e SKU, não tem cor de embalagem.
- **Classe abstrata** — `Pessoa`/`ItemOS`: definem contrato (o que) sem implementar tudo (o como).
- **Encapsulamento** — dados privados + validação no próprio objeto (KM não regride; desconto tem limite).
- **Herança** — reuso de `Pessoa`/`ItemOS` por duas famílias de subclasses.
- **Polimorfismo** — mesma mensagem (`calcular_subtotal`/`obter_resumo`), comportamentos por tipo.
- **Associação/agregação** — Cliente–Veículo e OS–itens ("tem-um"); o losango do UML marca a agregação.
- **Invariante** — verdade sempre: total líquido ≥ 0; KM crescente; desconto ≤ total bruto.
- **Transação** — `sessao()`: tudo ou nada em `salvar_itens_e_fechamento_os`.
- **Repository** — `RepositorioOficina` isola SQL das regras; troca de banco não toca o domínio.
- **Idempotência** — re-salvar a mesma OS duas vezes deixa estoque e caixa no mesmo estado correto.
