# OficinaPro v1.0 — DevSolo Studio

Sistema de gestão para oficinas mecânicas pequenas e mecânicos autônomos:
orçamentos, ordens de serviço, estoque com margem, relatórios financeiros,
comissões por mecânico e documentos em PDF versionados.

Projeto da disciplina de **Programação Orientada a Objetos** — 100% em Python.

## Como executar

```bash
pip install -r requirements.txt
python seed.py        # (opcional) popula o banco com dados de demonstração
python app.py         # abre a interface gráfica
python -m unittest test_dominio -v   # roda os 23 testes automatizados
python gerar_etapa3.py  # gera a documentação (Etapa3.pdf)
```

## Requisitos POO atendidos

| Requisito | Onde |
|---|---|
| ≥ 5 classes | 8 no domínio + 4 de infraestrutura = 12 |
| Herança | `Pessoa → Cliente/Mecanico`, `ItemOS → Peca/MaoDeObra` |
| Polimorfismo | `obter_resumo()`, `calcular_subtotal()` |
| Associação | OS ↔ Cliente/Veículo/Mecânico/Itens |
| Método privado | `__validar_telefone()`, `__formatar_placa()` |
| Atributo privado | `__cpf_cnpj`, `__desconto`, `__placa`, etc. |
| Main cria objetos | Toda a GUI |

## Estrutura

```
dominio.py        # classes de domínio (regras de negócio)
banco.py          # persistência em SQLite (transacional)
relatorios.py     # emissão de PDF versionado (reportlab)
app.py            # interface gráfica (CustomTkinter)
seed.py           # dados de demonstração
test_dominio.py   # testes automatizados
diagrama-de-classes.mmd  # UML (Mermaid)
gerar_etapa3.py   # gerador da documentação da Etapa 3
```
