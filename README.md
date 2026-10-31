# real-options-agent

Base Python para pesquisa de avaliação de investimentos e, futuramente, opções
reais. Esta versão implementa DCF (fluxo de caixa descontado/VPL) e análise de
cenários discretos. Os cálculos são executáveis e testados; não há ainda algoritmo
de exercício ótimo nem agente de IA.

## Executar e testar, sem instalar dependências

Requer Python 3.11 ou superior. Não requer API, conta externa, banco de dados,
Docker, GPU ou credenciais. Todos os exemplos usam dados sintéticos.

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
$env:PYTHONPATH = (Join-Path $PWD 'src')
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m real_options_agent
```

Não é necessário ativar o ambiente virtual ou alterar a política de execução do
PowerShell. A variável `PYTHONPATH` vale apenas para o terminal atual.

Em Linux/macOS:

```sh
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m real_options_agent
```

Instalação editável opcional (o pip poderá acessar a internet para obter o
backend de construção indicado em `pyproject.toml`):

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Após essa instalação, o pacote pode ser importado sem configurar `PYTHONPATH`.
Os testes usam `unittest`, incluído no Python; pytest é opcional e não é exigido.

## Uso da biblioteca

```python
from real_options_agent import CashFlow, Scenario, discounted_cash_flow, evaluate_scenarios

result = discounted_cash_flow(
    [CashFlow(time=1, amount=110), CashFlow(time=2, amount=121)],
    discount_rate=0.10,
    initial_investment=150,
)
assert round(result.present_value, 2) == 200.00
assert round(result.npv, 2) == 50.00

analysis = evaluate_scenarios(
    [
        Scenario("downside", 0.25, (CashFlow(1, 80),), 100),
        Scenario("upside", 0.75, (CashFlow(1, 140),), 100),
    ],
    discount_rate=0.10,
)
print(analysis.expected_npv)
print(analysis.probability_of_loss)
```

## Convenções e limites

- `PV = sum(CF_t / (1 + r)**t)` e `NPV = PV - initial_investment`.
- O investimento inicial é um desembolso não negativo em `t=0`. Não o inclua
  novamente nos fluxos de caixa. Demais fluxos podem ter sinal positivo ou negativo.
- `r` é uma taxa efetiva por período, em decimal. Tempos e taxa devem usar o
  mesmo período; tempos fracionários e fluxos em `t=0` são aceitos.
- A taxa deve ser finita e maior que -1; tempos devem ser finitos e não negativos.
  Fluxos podem estar fora de ordem ou compartilhar a mesma data. Uma sequência
  vazia tem PV zero. Valores fora do alcance numérico são rejeitados.
- Valores monetários usam `float`, com soma por `math.fsum`; não há precisão
  contábil em centavos garantida. Não há conversão de moedas, inflação, impostos,
  valor terminal automático ou calibração da taxa de desconto.
- Cenários devem ser mutuamente exclusivos e exaustivos, com nomes únicos e
  probabilidades entre 0 e 1. A soma deve ser 1, com tolerância absoluta de 1e-9;
  pequenos erros aceitos são normalizados e os pesos usados aparecem no resultado.
- A análise retorna VPL esperado, variância populacional ponderada, desvio padrão,
  probabilidade de VPL estritamente negativo e extremos com probabilidade positiva.
  Cenários de probabilidade zero ficam no relatório, mas não afetam esses momentos
  ou extremos. Todos usam a mesma taxa de desconto fornecida pelo chamador.
- Probabilidades são entradas, não estimativas geradas pelo programa. O VPL
  esperado não é um preço de opção e não implica probabilidades neutras ao risco.

O exemplo `python -m real_options_agent` produz VPL esperado de aproximadamente
21,49, desvio padrão de 36,82 e probabilidade de VPL negativo de 25%.

## Estrutura e próximos desenvolvimentos

- `src/real_options_agent/dcf.py`: fluxos datados e cálculo de PV/VPL.
- `src/real_options_agent/scenarios.py`: cenários e distribuição de resultados.
- `src/real_options_agent/__main__.py`: exemplo sintético reproduzível.
- `tests/`: verificações com resultados calculáveis à mão e entradas inválidas.
- `tools/package_code_behaviors.py`: criação de ZIP por lista explícita de arquivos.

Uma extensão futura poderá implementar uma árvore de decisões com opções de
adiamento/abandono e comparar o valor com o DCF sem flexibilidade. Isso exigirá
definir estados, decisões, informações disponíveis em cada data e premissas de
desconto/probabilidade. Monte Carlo, programação dinâmica e integração com LLM
não fazem parte desta versão.

## GitHub privado

O projeto funciona integralmente sem GitHub. Para criar um repositório remoto
privado por linha de comando, instale o GitHub CLI separadamente, autentique sua
conta pelo navegador e execute, dentro deste repositório Git já inicializado:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh repo create real-options-agent --private --source . --remote origin --push
```

Esses comandos são para uma criação nova; não devem ser repetidos se o remoto
já existir. A conta precisa poder criar repositórios privados no destino. A
autenticação de um conector de outro aplicativo não configura automaticamente
o Git local. Não coloque tokens no código, no ZIP ou em mensagens.

Referências: [autenticação do CLI](https://cli.github.com/manual/gh_auth_login),
[criação de repositório](https://cli.github.com/manual/gh_repo_create).

## Pacote de código para Code Behaviors

```powershell
python tools/package_code_behaviors.py
```

O ZIP é gravado na pasta acima do projeto. Somente os arquivos nomeados na lista
do empacotador são incluídos. Histórico `.git`, ambientes virtuais, caches,
credenciais, dados privados e arquivos `AGENTS` não entram no pacote. Ao adicionar
código legítimo, revise e atualize a lista antes de gerar outro pacote. A lista
controla nomes; alterações futuras no conteúdo também precisam de revisão.

Este README é documentação técnica do projeto. Não contém textos prontos de
submissão. Conforme a instrução da Alignerr informada pelo usuário, os textos
submetidos ao Taiga/Labelbox devem ser escritos pelo próprio usuário.

A existência deste projeto novo e privado não comprova elegibilidade no Code
Behaviors. Se as regras vigentes exigirem repositório público/open-source
preexistente, este projeto não atende a essa condição nesta forma. Nenhuma
licença de distribuição open-source foi escolhida nesta versão inicial.
