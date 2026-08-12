# CONTEXT.md — Alicerce

Este arquivo é o ponto de entrada pra qualquer sessão de trabalho (humana ou
com Claude Code). Segue o padrão "investigate before implement": antes de
qualquer mudança estrutural, entender o estado atual e o *porquê* das
decisões passadas — não só o *o quê*.

## O que é este projeto

Sucessor do `valuation-tracker`, motivado pela dificuldade em manter um
pipeline genérico aplicado a perfis de empresa muito diferentes (concessão,
estatal, holding, seguradora...). Ver `docs/ROADMAP.md` pra fases completas.

## Princípios de arquitetura (não negociáveis)

1. **Nenhum campo sem proveniência.** Todo valor carregado tem fonte,
   confiança e data. Ver `backend/src/alicerce/proveniencia/schema.py`.
2. **Perfis são tags compostas, não categorias exclusivas.** Uma empresa
   pode ser `["concessao_com_prazo", "estatal_controlada"]` ao mesmo tempo.
   Cada tag contribui uma regra; regras se combinam, não competem.
3. **Fallback é explícito.** `regra_generico_dcf` existe como fallback
   documentado — nunca um `if/else` "default" disfarçado.
4. **Calculation pipeline, não MVC.** Sem camada de "controller" genérica.
   Cada perfil é uma composição de regras (`Protocol RegraPerfil`).
5. **Sanity check contra mercado antes de confiar no resultado.** Fase 2
   não é opcional nem tardia — é o alarme mais barato de implementar.
6. **IA/LLM entra por último (Fase 6), como input estruturado com fonte
   e confiança — nunca como número final direto.**

## Ordem de implementação

Fases 0 → 6, sequenciais. Ver `docs/ROADMAP.md` para entregáveis e
critério de saída de cada uma. Não pular pra sinais qualitativos antes do
núcleo determinístico (Fases 0-3) estar calibrado nos 6 tickers-piloto:
`TAEE3, GEPA4, WIZC3, ITSA4, CPLE3, BEEF3` (BEEF3 adicionado na Fase 1 —
único caso real de alavancagem em moeda estrangeira já documentado).

## Estratégia de testes

Suíte completa mora em `backend/tests/` (ver "Estrutura de monorepo" pra
como rodar):

- `tests/unit` — regra por regra, isolada (`ContextoValuation` de entrada
  → saída esperada).
- `tests/regression` — casos que já quebraram uma vez (ex: WACC capado
  abaixo do Ke, capex undercapture) não podem voltar a quebrar.
- `tests/integration` — pipeline completo, ticker piloto de ponta a ponta.
- `tests/provenance_contract` — nenhum campo sai "mudo" do pipeline.
- `tests/sanity` — divergência calculado-vs-mercado dentro da faixa
  esperada por perfil.

## Stack (confirmado)

Python 3.11+, FastAPI + Pydantic v2 (mesma base do `valuation-tracker`),
pytest. Frontend (React/TypeScript) fica fora de escopo até pelo menos a
Fase 4 — Fases 0-3 são backend puro, sem UI.

## Fase 1 — Motor de Perfis (concluída)

Status: implementada e testada. `backend/src/alicerce/perfis/` tem
`perfil_setor.py` (`PerfilSetor`), `tags.py` (`TagPerfilEconomico`,
`AtribuicaoTag`), `motor.py` (`obter_perfil`/`obter_tags`/
`obter_atribuicoes_tags`, `TickerSemPerfilError`) e
`dados/perfis_ticker.json` com os 6 tickers-piloto. 43 testes passando
(`backend/tests/unit/test_perfil_setor.py`, `test_tags.py`, `test_motor.py`,
`backend/tests/provenance_contract/test_perfil_setor_provenance.py`, + os 7 da
Fase 0). Nenhuma lógica de valuation ou `RegraPerfil` implementada —
fica pra Fase 2, como planejado.

### O que já existe hoje (Fase 0, confirmado lendo o código real)

- `src/alicerce/proveniencia/schema.py`: `CampoComProveniencia(valor: float,
  fonte, confianca, data_atualizacao, motivo_override)` — **tipado só pra
  `float`**. Isso é intencional e não é uma lacuna: o pedido original da
  Fase 0 restringia proveniência a "campo de dado **numérico** relevante"
  — `setor`/`subsetor` (strings) ficam de fora por escopo, não por
  descuido.
- `RegistroAuditoria` (ticker, campo, fonte, contagem de override manual).
- 7 testes unitários passando, `pyproject.toml` corrigido para instalar em
  modo editável (`[tool.setuptools.packages.find] where = ["src"]`).
- `src/alicerce/perfis/` existia só como pacote vazio (`__init__.py`) no
  início desta fase — ver abaixo o que foi implementado.

### Investigação no `valuation-tracker` (fonte dos "9 dicts")

Lido `valuation/perfil_setor.py`, `perfil_dcf.py` + `dados/perfil_dcf.json`,
`risco.py`, `sotp.py` + `dados/sotp_config.json`, `dcf.py`, `wacc.py` e os
trechos relevantes do `CONTEXT.md` de lá. Achados relevantes pra esta fase:

- Os "9 dicts" (`BETA_POR_SETOR`, `EV_EBITDA_MEDIO_SETOR`,
  `PSR_MEDIO_SETOR`, `SETORES_REGULADOS`, `SETORES_CICLICOS` — duplicado em
  2 arquivos —, `FATOR_CONVERSAO_NOPAT`, `CONFIGURACAO_SETORES` com
  substring matching, e o `PERFIL_SETOR` antigo de pesos de score) já
  tinham sido consolidados lá numa dataclass `PerfilSetor`, mas indexada
  por **setor**, com override pontual por **ticker**
  (`PERFIL_SETOR_OVERRIDE_TICKER`, ex: WEGE3 fora de "Máquinas e
  Equipamentos"). Achado da auditoria deles: 30 de 41 setores reais
  (50,2% dos tickers) não tinham entrada em nenhum dos 9 pontos.
- Separado disso, `perfil_dcf.py` + `dados/perfil_dcf.json` guardam o
  perfil de DCF **por ticker** (`perpetuidade_padrao` | `concessao` |
  `multi_fase`) — só GEPA4/GEPA3 estão parametrizados como `concessao`
  hoje; CPLE3/TAEE3/CMIG3/etc. estão listados como "candidatos
  pendentes", ainda em `perpetuidade_padrao` (nunca migrados lá).
- `risco.py::EMPRESAS_CONTROLE_ESTATAL`: lista fixa de tickers com
  controle estatal — CPLE3/CPLE6 confirmados mesmo pós-privatização
  (golden share do Paraná), decisão já tomada e reconfirmada pelo usuário
  no projeto anterior.
- `sotp.py` + `dados/sotp_config.json::ITSA4`: holding pura, segmentos
  avaliados por `valor_participacao` (valor de mercado da fatia, não
  EV/EBITDA) porque o maior ativo é participação num banco (Itaú
  Unibanco) — EV/EBITDA não é conceito limpo pra banco.
- `wacc.py`: `pct_divida_moeda_estrangeira` (0-100) já existia como campo
  real, com dado confirmado — **BEEF3 = 90% da dívida bruta em moeda
  estrangeira** (achado de investigação anterior, gerou spread de WACC de
  ~1,2pp); TAEE3 confirmado em 0%.
- `perfil_setor.py::"Previdência e Seguros"` (não `"Seguradoras"`, que é
  só alias de teste): WIZC3 e outras seguradoras têm
  `taxonomia_financeira_especial=True` — EBIT/EBITDA/FCF não são conceitos
  limpos pro negócio de underwriting, mesma razão de bancos.
- **`DDM_ONLY` não existe em nenhum lugar do `valuation-tracker`** — não
  há módulo de Dividend Discount Model lá. É um conceito **novo** do
  Alicerce, motivado pelo perfil observado de TAEE3 (transmissora, RAP
  contratada, payout historicamente próximo de 100% do lucro regulatório)
  — registrado aqui como decisão de análise, não como algo "recuperado"
  do código antigo.
- **Correção ao pedido original**: o pedido menciona "moeda de referência
  de receita" como exemplo de campo. Não existe isso no
  `valuation-tracker` nem fonte de dado pra isso — a nota de lá é
  explícita: *"composição cambial da RECEITA não existe em taxonomia
  estruturada da CVM"*. O que existe, testado e com dado real, é a moeda
  da **dívida** (`pct_divida_moeda_estrangeira`, é o campo por trás de
  `ALAVANCAGEM_USD`/BEEF3). Proponho usar esse campo real em vez de
  inventar um campo de receita sem fonte.

### Decisão de schema: dataclass, não Pydantic

`PerfilSetor` como `@dataclass`, igual ao padrão já usado em
`proveniencia/schema.py` — não introduzir Pydantic no motor de domínio
agora. Pydantic entra quando a API FastAPI existir de fato (Fase 3+),
consumindo estas dataclasses, não substituindo-as.

### `PerfilSetor` — campos implementados (nível ticker, não setor)

Diferença deliberada frente ao `valuation-tracker`: lá o perfil é por
SETOR com override por ticker (2 camadas). Aqui, pra 6 tickers, a
simplificação é ir direto por TICKER — a camada de "perfil de referência
por setor" pode ser adicionada depois (Lote 2/3 do `ROADMAP.md`) sem
quebrar a interface pública (`obter_perfil(ticker)` continua igual).

```python
@dataclass
class PerfilSetor:
    ticker: str
    setor: str                       # nome canônico (normalização é
                                      # responsabilidade da Fase de ingestão,
                                      # não deste módulo)
    subsetor: Optional[str] = None

    # Classificação de setor (bool — não é "dado numérico", sem proveniência
    # por escopo original da Fase 0; racional registrado em `notas`)
    eh_regulado: bool = False
    eh_ciclico: bool = False
    taxonomia_financeira_especial: bool = False  # bancos/seguradoras/holdings
                                                  # financeiras: EBIT/EBITDA/FCF
                                                  # não são conceitos limpos

    # Referências numéricas — usam CampoComProveniencia (Fase 0).
    # Todos opcionais: None = "usa o fallback genérico", nunca um número
    # inventado.
    beta_referencia: Optional[CampoComProveniencia] = None
    ev_ebitda_medio_referencia: Optional[CampoComProveniencia] = None
    psr_medio_referencia: Optional[CampoComProveniencia] = None
    fator_conversao_nopat_referencia: Optional[CampoComProveniencia] = None
    pct_divida_moeda_estrangeira: Optional[CampoComProveniencia] = None
    cap_crescimento_ciclico: Optional[CampoComProveniencia] = None

    notas: Optional[str] = None      # racional textual, auditável (ex:
                                      # "GEPA4: BPP/DRE zerados na CVM desde
                                      # 2024 — dado de balanço não confiável")
```

### Tags de perfil econômico — `TagPerfilEconomico`

```python
class TagPerfilEconomico(str, Enum):
    DDM_ONLY = "ddm_only"                     # ex: TAEE3
    CONCESSAO = "concessao"                   # ex: GEPA4, CPLE3
    ESTATAL_CONTROLADA = "estatal_controlada" # ex: CPLE3
    SOTP_OBRIGATORIO = "sotp_obrigatorio"     # ex: ITSA4
    ALAVANCAGEM_USD = "alavancagem_usd"       # ex: BEEF3
```

Cada tag só **documenta** a implicação metodológica esperada (ex:
`DDM_ONLY` → "DCF/FCFE devem ficar desligados, DDM é o método principal")
— **não implementa a regra** ainda. Nesta fase, tags são dado puro; a
composição de regras (`RegraPerfil.aplicar()`, já esboçado no
`ROADMAP.md`) fica pra quando os métodos de valuation existirem (Fase 2+),
senão estaríamos implementando decisão de metodologia sem nada pra
decidir.

Tags são atribuídas por ticker com justificativa obrigatória (auditável,
mesmo espírito do `motivo_override` da Fase 0):

```python
@dataclass(frozen=True)
class AtribuicaoTag:
    tag: TagPerfilEconomico
    justificativa: str
```

### Motor de perfis — interface pública (`perfis/motor.py`)

```python
class TickerSemPerfilError(KeyError):
    """Ticker não cadastrado no motor de perfis — falha explícita,
    nunca um fallback silencioso pra perfil genérico."""

def obter_perfil(ticker: str) -> PerfilSetor:
    """Levanta TickerSemPerfilError se o ticker não estiver cadastrado."""

def obter_tags(ticker: str) -> frozenset[TagPerfilEconomico]:
    """Chama obter_perfil() primeiro (mesma checagem de existência).
    Ticker cadastrado sem NENHUMA tag atribuída retorna frozenset() —
    isso é um estado válido (ex: WIZC3 abaixo), não um erro: nem todo
    ticker tem uma situação econômica especial."""

def obter_atribuicoes_tags(ticker: str) -> tuple[AtribuicaoTag, ...]:
    """Mesmo que obter_tags(), mas com a justificativa de cada uma —
    pra auditoria/UI, não pra lógica de decisão."""
```

Importante: `obter_perfil`/`obter_tags` são a ÚNICA porta de entrada.
Nenhum módulo de valuation (Fase 2+) deve checar `if ticker == "TAEE3"` —
deve checar `TagPerfilEconomico.DDM_ONLY in obter_tags(ticker)`.

### Herança de setor (decidido)

**Decisão: (b) herança com override.** Motivo, olhando a distribuição real
dos 6 tickers-piloto por setor:

| Setor | Tickers-piloto |
|---|---|
| Energia Elétrica | TAEE3, CPLE3, GEPA4 (3 de 6) |
| Holding | ITSA4 |
| Alimentos | BEEF3 |
| Previdência e Seguros | WIZC3 |

3 dos 6 tickers-piloto caem no mesmo setor e, confirmado em
`valuation-tracker/valuation/perfil_setor.py::PERFIS_SETOR["Energia
Elétrica"]`, compartilhariam `eh_regulado`, `eh_ciclico`,
`beta_referencia` (0.65), `ev_ebitda_medio_referencia` (7.0) e
`fator_conversao_nopat_referencia` (0.60) idênticos — duplicar isso 3x
manualmente (e de novo a cada novo ticker de Energia Elétrica no Lote 2,
que já lista ~20 candidatos) é exatamente o tipo de duplicação que a Fase
1 existe pra evitar. Os outros 3 tickers-piloto são de setores sem
sobreposição — ficam como registro direto, sem perfil-base, sem inventar
estrutura pra um caso que não se repete ainda.

**Mecanismo**: `_setores_base` no JSON é opcional e só existe pros
setores onde já há sobreposição real (hoje, só "Energia Elétrica"). O
carregamento em `motor.py` faz um merge raso (`dict.update`) — campos
presentes na entrada do ticker sempre vencem os do perfil-base do setor;
campos ausentes nos dois viram o default da dataclass (`None`/`False`).
Ticker de setor sem entrada em `_setores_base` funciona normalmente (o
merge é com `{}`). Isso não é uma segunda hierarquia de classes nem um
mecanismo de resolução complexo — é literalmente `{**base, **ticker}`,
documentado inline em `motor.py`.

### Fonte de dados (Fase 1 — explicitamente provisório)

JSON estático versionado em
`src/alicerce/perfis/dados/perfis_ticker.json`, carregado uma vez no
import do módulo (mesmo padrão usado em `perfil_dcf.py` no projeto
anterior). **Não** uso YAML pra não adicionar `pyyaml` como dependência
nova sem necessidade. Estrutura evolutiva: cada ticker é uma entrada
independente — trocar por fonte dinâmica (CVM, etc.) depois é possível
sem mudar a assinatura de `obter_perfil`/`obter_tags`.

### Os 6 tickers-piloto (dados que entram no JSON)

| Ticker | Setor | Classificação | Tags | Fonte do achado |
|---|---|---|---|---|
| TAEE3 | Energia Elétrica | regulado | `DDM_ONLY` | análise externa (payout ~100% do lucro regulatório, RAP contratada) |
| CPLE3 | Energia Elétrica | regulado, estatal | `CONCESSAO`, `ESTATAL_CONTROLADA` | `risco.py::EMPRESAS_CONTROLE_ESTATAL` (golden share PR) |
| GEPA4 | Energia Elétrica | regulado | `CONCESSAO` | `perfil_dcf.json` (já parametrizado como `concessao`) |
| ITSA4 | Holding | taxonomia financeira especial | `SOTP_OBRIGATORIO` | `sotp_config.json::ITSA4` (7 segmentos via `valor_participacao`) |
| BEEF3 | Alimentos | cíclico | `ALAVANCAGEM_USD` | `wacc.py` (90% dívida em moeda estrangeira, dado real confirmado) |
| WIZC3 | Previdência e Seguros | taxonomia financeira especial | *(nenhuma)* | `perfil_setor.py` — caso de teste de "perfil completo, zero tags especiais" |

WIZC3 é o caso deliberado de "cadastrado, mas sem tags" — exercita a
diferença entre "ticker desconhecido" (erro) e "ticker sem situação
especial" (`frozenset()` válido).

### Testes (implementados, todos passando)

- `backend/tests/unit/test_perfil_setor.py` — construção válida/inválida de
  `PerfilSetor`.
- `backend/tests/unit/test_tags.py` — composição de tags (múltiplas tags por
  ticker), imutabilidade de `AtribuicaoTag`, justificativa obrigatória.
- `backend/tests/unit/test_motor.py` — `obter_perfil`/`obter_tags` dos 6 tickers
  batendo com a tabela acima; ticker desconhecido levanta
  `TickerSemPerfilError`; herança de setor (Energia Elétrica) e override
  por ticker confirmados por teste, não só por inspeção do JSON.
- `backend/tests/provenance_contract/test_perfil_setor_provenance.py` — usa
  `typing.get_type_hints(PerfilSetor)` (contrato estrutural, resiste a
  `from __future__ import annotations`) pra garantir que nenhum campo
  resolve pra `float`/`int` cru, e que os 6 campos de referência são de
  fato `Optional[CampoComProveniencia]` — tanto no schema quanto nos
  valores carregados dos 6 tickers-piloto.

### Decisões confirmadas (revisadas e aprovadas)

1. Troca "moeda de referência de receita" → `pct_divida_moeda_estrangeira`
   — aprovada.
2. `PerfilSetor` por TICKER (não por setor com cascata no schema) —
   aprovada. Refinada pela decisão de "Herança de setor" acima: a
   cascata continua não existindo no *schema* (`PerfilSetor` não tem
   noção de setor-pai), mas existe como mecanismo de *carga de dados*
   (merge raso no JSON) pros 3 tickers de Energia Elétrica — evita
   duplicação sem adiar pra um "Lote 2" que ainda nem começou.
3. Tags ficam só como dado descritivo nesta fase — aprovada. Documentado
   explicitamente nos docstrings de `tags.py`: este módulo responde "o
   quê" (quais tags um ticker tem), nunca "quando aplicar" — isso é
   `RegraPerfil`, Fase 2.

   `RegraPerfil`: investigado numa sessão posterior, implementação
   adiada — depende de existir ao menos um método de valuation real
   (DCF/DDM/FCFE/SOTP) no Alicerce, e hoje nenhum existe (confirma este
   mesmo princípio acima, não uma decisão nova). Quando retomado: CPLE3
   (`CONCESSAO`+`ESTATAL_CONTROLADA` simultâneas) não é um caso de
   conflito real entre regras, é complementar — não é preciso desenhar
   mecanismo de precedência ainda. `dcf_concessao.py` do
   `valuation-tracker` antigo: quando a regra de `CONCESSAO` for
   implementada, só referenciar em docstring/comentário, não portar o
   código diretamente.

## Estrutura de monorepo (concluída)

Status: aprovada e executada. `backend/` (todo o código Python: `src/`,
`tests/`, `api/`, `scripts/`, `pyproject.toml`) e `frontend/`
(`.gitkeep` + `README.md` curto, sem stack decidida) criados com `git
mv` pros arquivos já rastreados no commit `933218b` e `mv` normal pros
arquivos da Fase 1 (sem histórico prévio pra preservar de qualquer
forma). Nenhum conteúdo de `pyproject.toml` mudou (caminhos já eram
relativos). 43 testes rodados a partir de `backend/` num venv limpo
(Python 3.11.6) — todos passando, nenhuma mudança de lógica. `git status`
confirma os moves de arquivo rastreado como rename (`R`), não
delete+add.

### Investigação do estado atual (lendo o repositório real)

- **Achado que muda a execução do plano**: apesar do enunciado desta
  tarefa dizer "Fase 0 e Fase 1 ... commitadas", `git log` mostra só 1
  commit (`933218b primeiro commit`, o esqueleto inicial: `pyproject.toml`,
  os `__init__.py` vazios de cada subpacote, `proveniencia/schema.py`,
  `CONTEXT.md`/`README.md`/`docs/ROADMAP.md` na versão inicial,
  `api/__init__.py`). **Tudo que veio depois — o fix de
  `[tool.setuptools.packages.find]`, `.gitignore`, os testes de
  proveniência, e o motor de perfis inteiro da Fase 1
  (`perfis/motor.py`, `perfis/tags.py`, `perfis/perfil_setor.py`,
  `perfis/dados/`, mais 4 arquivos de teste) — está no working tree,
  nunca commitado** (`git status` confirma: só modificações/arquivos
  novos, nada staged). Isso não muda O QUÊ mover, mas muda COMO: `git mv`
  só existe pra arquivo já rastreado — em arquivo novo/não commitado ele
  falha (`fatal: not under version control`). Não vou commitar nada por
  conta própria (não foi pedido); o plano abaixo usa `git mv` pros
  arquivos que já estão no commit `933218b`, e `mv` normal pros arquivos
  da Fase 1 que ainda não têm histórico nenhum pra preservar — o
  resultado final no working tree é idêntico de qualquer forma (é você
  quem decide quando commitar, e em que agrupamento).
- **Imports confirmados absolutos** (`grep -rn "^from alicerce\|^import
  alicerce" src tests`): todo import é `from alicerce.<modulo> import
  ...` — nenhum `sys.path` manual, nenhum import relativo cross-pasta.
  Isso depende só do pacote `alicerce` estar instalado (`pip install
  -e .`), não de onde o arquivo físico mora — mover a árvore inteira
  (`src/` + `tests/` + `pyproject.toml`) junto não quebra nenhum import.
- **`pyproject.toml` só tem caminhos RELATIVOS**: `[tool.setuptools.
  packages.find] where = ["src"]` e `[tool.pytest.ini_options] testpaths
  = ["tests"]` são relativos à localização do próprio `pyproject.toml`.
  Como o `pyproject.toml` vai mover junto com `src/` e `tests/` (os 3 pra
  dentro de `backend/`), **nenhum valor dentro do arquivo precisa
  mudar** — só a localização do arquivo em si. Simplifica o passo 3 do
  pedido original (não há "caminho interno" pra ajustar, de fato).
- **`.gitignore` já cobre os novos caminhos sem alteração**: os padrões
  existentes (`__pycache__/`, `*.pyc`, `*.egg-info/`, `.venv/`,
  `.pytest_cache/`, `.coverage`, `htmlcov/`) não têm `/` no meio nem no
  início — por semântica do Git, isso já casa em QUALQUER profundidade
  da árvore (`backend/src/.../__pycache__/` incluso), não só na raiz.
  Nenhuma mudança necessária aqui.
- **Nenhum CI/script pra atualizar**: confirmado — sem `.github/workflows`,
  sem `pytest.ini`, sem `conftest.py`. `scripts/` existe mas está vazio
  (0 arquivos, não rastreado no Git — diretório vazio não é versionado).
- **Achado fora do escopo desta tarefa, mas relevante pro plano**: existe
  um `api/__init__.py` (Python, vazio, já commitado no `933218b`) que a
  árvore-alvo do pedido não menciona. Pelo princípio declarado ("tudo que
  hoje é Python vira `backend/`"), a leitura mais direta é mover pra
  `backend/api/__init__.py` — incluído no plano abaixo como extensão da
  árvore pedida, não como mudança de escopo (é só aplicar o mesmo
  princípio a uma pasta que a investigação encontrou e o diagrama do
  pedido não listou explicitamente).
- **`.DS_Store` (3 arquivos, não rastreados, raiz/`src/`/`tests/`)**:
  lixo do Finder do macOS, sem relação com o código. Vou apagá-los (são
  regenerados automaticamente pelo macOS, nunca deveriam ter sido
  criados como conteúdo do projeto) e adicionar `.DS_Store` ao
  `.gitignore` — higiene trivial, feita junto por já estar mexendo nesses
  arquivos, não uma tarefa nova.

### Plano de migração

Árvore final (ajustada frente ao pedido original: `backend/api/` e
`backend/scripts/` adicionados, pelo motivo acima):

```
alicerce/
  backend/
    src/alicerce/          # todo o conteúdo atual de src/alicerce/
    tests/                  # toda a suíte de testes atual
    api/                    # api/__init__.py (achado na investigação)
    scripts/                # vazio hoje, mantido pra scripts futuros (Fase 3+, ex: atualização CVM)
    pyproject.toml           # movido da raiz, SEM alteração de conteúdo
  frontend/
    .gitkeep
    README.md                # 2-3 linhas, sem stack decidida
  docs/
    ROADMAP.md
  CONTEXT.md
  README.md
  .gitignore
```

Comandos planejados (nenhum executado ainda):

```bash
mkdir -p backend frontend
git mv pyproject.toml backend/pyproject.toml
git mv src backend/src
git mv tests backend/tests
git mv api backend/api
mkdir -p backend/scripts   # vazio, não rastreável até ter conteúdo
mv .gitignore .gitignore   # sem mudança de local; só o conteúdo ganha .DS_Store
touch frontend/.gitkeep
# frontend/README.md criado à parte (conteúdo abaixo)
```

Os arquivos da Fase 1 (não rastreados: `perfis/motor.py`, `perfis/
tags.py`, `perfis/perfil_setor.py`, `perfis/dados/*.json`, os 4 testes
novos) viajam automaticamente dentro de `git mv src backend/src` — `git
mv` num diretório move TODO o conteúdo do diretório, rastreado ou não;
só o rastreamento em si (o que aparece no `git log` de cada arquivo) que
difere entre os dois grupos.

### Como rodar (pós-migração)

```bash
cd backend
pip install -e ".[dev]"
pytest
```

Executar `pytest` a partir da raiz do repo deixa de funcionar como antes
(não há mais `pyproject.toml`/`pytest.ini` na raiz pra `pytest` descobrir
`testpaths`) — isso é uma mudança de comportamento real, não um bug;
documentar no `README.md` principal é parte do item 6.

### `frontend/README.md` (conteúdo proposto)

```markdown
# Alicerce — Frontend

Reservado para a fase de frontend do Alicerce (ver `../docs/ROADMAP.md`
— fora de escopo até pelo menos a Fase 4). Nenhuma stack decidida ainda;
Fases 0-3 são backend puro, sem UI.
```

### Aprovação e execução

Plano aprovado sem ressalvas (incluindo a extensão pra `backend/api/` e
`backend/scripts/`, e sem commit prévio — reorganização feita em cima do
mesmo working tree não commitado). Nada de `RegraPerfil`/Fase 2 tocado
nesta tarefa. `git status` pós-migração mostra os arquivos herdados do
commit `933218b` como rename (`R`) — histórico preservado — e os
arquivos novos da Fase 1 como untracked no novo caminho (`??`), exatamente
como esperado, já que nunca tiveram commit.

## Detecção de descontinuidade de preço (extensão da Fase 0, concluída)

Implementa o entregável adicionado ao `docs/ROADMAP.md`, Fase 0, nesta
sessão: detectar quando a razão entre máxima e mínima de 52 semanas é alta
demais pra ser volatilidade orgânica — sinal de evento societário
(grupamento/desdobramento) não ajustado na série histórica de preço.
Caso real motivador: RVEE3 reportando R$0,68 a R$31,00 em 52 semanas
(razão ~45,59x).

### Achado antes de implementar (investigação, ver item 1 do pedido)

O pedido descrevia "call sites" que consomem preço histórico — endpoint
de valuation, cálculo de beta/volatilidade/múltiplos, hook de paridade
DCF entre `/valuation` e `/cenarios`. **Nenhum desses existe no Alicerce
hoje.** `grep` completo em `backend/src` e `backend/api` por
preço/histórico/beta/volatilidade/múltiplo/endpoint não encontrou
nada além de `beta_referencia` (um campo de fallback do `PerfilSetor`,
não uma série de preço). `pipeline/`, `capm/`, `sanity/`, `qualitativo/`,
`backtesting/` continuam pacotes vazios (só `__init__.py` de 0 bytes,
confirmado). Esses call sites e esse hook existem no `valuation-tracker`
antigo, não aqui — o pedido parece ter carregado essa premissa de lá.
**Consequência**: os itens 3 e 4 do pedido original (integrar no ponto de
ingestão, confirmar propagação em "ambos os call sites") não têm alvo
real pra integrar ainda. Implementado como função pura + função de
aplicação, prontas pro estágio de ingestão futuro (Fase 1+ do
`ROADMAP.md`, pasta `pipeline/`) chamar — sem inventar um pipeline que
não foi pedido nem aprovado nesta sessão.

### O que foi implementado

`backend/src/alicerce/proveniencia/descontinuidade_preco.py` (módulo
novo — `proveniencia/schema.py` da Fase 0 **não foi alterado**):

- `RAZAO_MAX_MIN_52W_SUSPEITA = 10.0` — limiar configurável, mesmo padrão
  de constante de `CAPM_CEILING`/`WACC_FLOOR` do `valuation-tracker`.
  **Racional (revisar antes do commit — não calibrado estatisticamente
  contra amostra real da B3)**: grupamentos/desdobramentos na B3 costumam
  ser 1:5, 1:10, 1:20 ou mais agressivos (comum em micro/nanocaps pra
  evitar desenquadramento de preço mínimo) — isso já produz razão ≥5x
  isolado, somado a movimento de preço real do período. Uma ação sem
  evento societário raramente ultrapassa ~5-8x de razão máx/mín em 52
  semanas mesmo em cenário extremo. RVEE3 (~45,6x) fica muito acima da
  margem de 10x, não é caso limítrofe.
- `razao_max_min_52_semanas(maxima, minima)` — cálculo puro, levanta
  `ValueError` se `minima <= 0`.
- `eh_descontinuidade_suspeita(maxima, minima, limiar=...)` — `True`
  quando a razão ULTRAPASSA o limiar (igual ao limiar não é suspeito).
- `aplicar_deteccao_descontinuidade(campo, maxima, minima, limiar=...)` —
  recebe um `CampoComProveniencia` qualquer (não assume nome de campo,
  porque nenhum campo de preço existe em nenhum schema ainda) e, se
  suspeito, retorna uma NOVA instância com `confianca="baixa"` e
  `motivo_override` preenchido automaticamente com a razão calculada e o
  tipo de anomalia — `valor`/`fonte` originais preservados (nunca
  descartado em silêncio, princípio "nenhum campo mudo"). Campo não
  suspeito volta inalterado (mesma instância).

### Testes (11 novos, sem mocks, `CampoComProveniencia` sintético real)

`backend/tests/unit/test_descontinuidade_preco.py`: caso limpo (razão
1.5x, campo inalterado), caso RVEE3-like (razão ~45,6x, `confianca`
forçada e `motivo_override` preenchido), caso de borda exatamente no
limiar (10.0x exato — NÃO suspeito) e um centavo acima (suspeito),
`minima<=0` levanta erro, campo já `fonte="manual"` tem seu
`motivo_override` anterior sobrescrito sem conflito de validação, limiar
customizado é respeitado. **54 testes passando no total** (43 anteriores
+ 11 novos), rodado a partir de `backend/` num venv limpo — nenhum hook
de paridade DCF existe no Alicerce pra rodar (achado acima).

### Call sites cobertos

Nenhum — ver "Achado antes de implementar" acima. Quando o estágio de
ingestão de preço histórico for implementado (Fase 1+), ele deve chamar
`aplicar_deteccao_descontinuidade` sobre o campo de preço correspondente;
até lá, este módulo fica testado e pronto, sem uso real.

### Calibração do limiar (dados reais, sessão separada)

`RAZAO_MAX_MIN_52W_SUSPEITA=10.0` foi testado contra **14 tickers** com
dado real do Fundamentus (primeira fonte da cascata): os 6 tickers-piloto
como grupo de controle (sem evento societário, razão máxima observada
2,18x — BEEF3) e 8 tickers com evento societário confirmado via
notícia/Fato Relevante antes de entrar na amostra, dos quais **2 são
positivos reais** (RVEE3 ~44,12x, TOKY3 ~17,12x) e os outros 6
(SBSP3, DIRR3, AZUL3, VIVR3, ESPA3, AVLL3) não dispararam — achado
relevante: o Fundamentus já ajusta a série de 52 semanas pra maioria dos
eventos societários, então o detector funciona como rede de segurança só
pros casos em que esse ajuste falha (aparentemente concentrados em
microcaps muito ilíquidas com eventos incomuns/múltiplos, o mesmo perfil
de RVEE3 e TOKY3), não como detector geral de "todo evento societário".

**Sem sobreposição observada** entre os dois grupos (controle: ≤2,18x;
positivos reais: ≥17,12x) — 10.0 fica bem no meio, com margem dos dois
lados. **Mas a amostra de positivos é pequena (n=2)** — não há caso real
na amostra entre 3x e 17x que force uma escolha fina do valor exato;
8x, 12x ou 15x separariam os mesmos 2 casos dos 6 controles igualmente
bem. **10.0 não deve ser tratado como valor estatisticamente ótimo, só
como validado contra os casos disponíveis até esta data** (2026-08-11).
Valor não alterado nesta sessão — ver relatório de calibração completo
na conversa; mudar o valor é tarefa separada, com aprovação explícita.

## Liquidez de mercado — campo vs. tag (decidido e implementado)

### Investigação anterior (decisão, resumo — nunca tinha sido registrado aqui)

Pergunta: liquidez (o motivador foi um screening com microcaps ilíquidas —
SOND3, BMKS3, HBTS5, AHEB3, RVEE3 — cujos múltiplos "descontados" ficavam
indistinguíveis de desconto de valor genuíno) deveria entrar como novo
campo em `PerfilSetor` ou como `TagPerfilEconomico` nova
(`LIQUIDEZ_BAIXA`)?

**Decisão: campo em `PerfilSetor`, não tag.** Motivo, encontrado
investigando o código real (não preferência estética):

- 4 das 5 tags existentes (`CONCESSAO`, `ESTATAL_CONTROLADA`,
  `SOTP_OBRIGATORIO`, `DDM_ONLY`) são características **estruturais**
  (só mudam com evento corporativo raro). A única exceção
  (`ALAVANCAGEM_USD`) já não é uma tag autônoma — é a sinalização de um
  limiar sobre um campo numérico que já mora em `PerfilSetor`
  (`pct_divida_moeda_estrangeira`). Esse é o precedente real: número
  primeiro, tag derivada depois — nunca o inverso.
- `AtribuicaoTag` (`tags.py`) não tem `data_atualizacao` nem `confianca`
  — uma tag atribuída fica válida pra sempre até alguém editar o JSON à
  mão. Liquidez muda com o tempo sem nenhuma mudança na empresa — isso
  exigiria inventar um segundo mecanismo de staleness só pra tags, só
  pra esse caso.
- `CampoComProveniencia` (Fase 0) já tem esse mecanismo pronto:
  `esta_desatualizado` (`schema.py:43-46`). Reaproveitável direto, sem
  duplicar nada.
- Precedente interno pareado: `eh_ciclico` (bool) + `cap_crescimento_ciclico`
  (`CampoComProveniencia`) já convivem em `PerfilSetor` — exatamente o
  padrão "classificação derivada + métrica numérica" que liquidez
  precisaria, se um dia ganhar uma tag derivada.

### Implementado nesta sessão

`PerfilSetor.volume_medio_diario: Optional[CampoComProveniencia] = None`
(`perfil_setor.py`) — volume financeiro médio diário negociado (R$),
sinal de liquidez. **Sem sufixo `_referencia`** (diferente dos campos
vizinhos): é a métrica PRÓPRIA do ticker, não um fallback setorial —
distinção que a investigação anterior encontrou e que motivou o nome.
Reaproveita `esta_desatualizado` de `CampoComProveniencia`, sem
mecanismo de staleness próprio. `motor.py::_carregar_perfis()` também
ganhou o mapeamento do JSON pra esse campo (extensão pequena e mecânica
além dos itens pedidos — sem isso o campo nunca seria carregável pela
fonte de dados real, mesmo sem popular nenhum ticker ainda).

**Fora do escopo desta sessão, de propósito** (não esquecer nem
duplicar numa sessão futura):
- `TagPerfilEconomico.LIQUIDEZ_BAIXA` **não foi criada** — só faz
  sentido quando `RegraPerfil` existir de fato (ainda é só pseudocódigo
  em `docs/ROADMAP.md:61-71`, Fase 1/2) pra decidir o limiar de
  derivação, mesmo padrão de `ALAVANCAGEM_USD`.
- Nenhum dos 6 tickers-piloto foi populado com esse dado —
  `volume_medio_diario` continua `None` pra todos no
  `perfis_ticker.json` atual.

Testes: `test_perfil_setor.py` (3 novos — proveniência completa, campo
opcional sem quebrar o perfil, `esta_desatualizado` reaproveitado) e
`test_perfil_setor_provenance.py` (constante renomeada de
`_CAMPOS_REFERENCIA_ESPERADOS` pra `_CAMPOS_NUMERICOS_ESPERADOS` —
já não é só campos com sufixo `_referencia` — com `volume_medio_diario`
incluído). **57 testes passando** (54 anteriores + 3 novos).

## DDM (Gordon Growth) — função pura (concluída)

Primeiro método de valuation implementado no Alicerce (nenhum existia
antes). Investigação anterior confirmou: `DDM_ONLY` é a única
`TagPerfilEconomico` com mapeamento 1:1 já validado (TAEE3, único
ticker-piloto com essa tag); nenhuma fórmula de DDM/FCFE/DCF/SOTP estava
especificada em `CONTEXT.md`/`ROADMAP.md` antes desta sessão; nenhum
campo de entrada de DDM existia em `PerfilSetor`.

### O que foi implementado e onde mora

`backend/src/alicerce/valuation/ddm.py::calcular_ddm(dividendo_projetado,
ke, g) -> float` — Gordon Growth (`dividendo_projetado / (ke - g)`),
função pura, sem estado, sem I/O.

**Localização — `valuation/`, pacote novo.** Verificado antes de criar:
nenhum dos 6 pacotes vazios já existentes é descrito em
`README.md`/`docs/ROADMAP.md` como o lugar dos MÉTODOS de valuation
individuais — `pipeline/` é "orquestração calculation-pipeline"
(orquestra estágios, não é onde a fórmula mora), `capm/` é
especificamente CAPM/WACC (Fase 3), `consenso/` combina métodos já
calculados (Fase 4), `sanity/`/`qualitativo/`/`backtesting/` são outras
fases. Nenhum encaixe real — `valuation/` criado como pacote novo,
mesmo termo já usado em todo o projeto pra "métodos de valuation".

### Decisões de validação (revisar se discordar)

- `dividendo_projetado <= 0` → `ValueError`. `ke <= 0` → `ValueError`.
  `ke <= g` → `ValueError` (perpetuidade diverge).
- **`g` negativo é PERMITIDO, não travado.** É matematicamente válido no
  modelo (declínio de dividendo) e não há critério documentado no
  projeto pra proibir — travar seria precaução não pedida. Só o guard
  `ke > g` cobre o caso patológico.

### `Ke` continua parâmetro, não campo — de propósito

`Ke` (custo de capital próprio) é recebido como argumento direto de
`calcular_ddm()`, nunca calculado internamente — o Alicerce não tem CAPM
ainda (Fase 3, pacote `capm/` continua vazio). Isso é deliberado, não
uma lacuna: adicionar `Ke` como campo de `PerfilSetor` agora seria
antecipar Fase 3 sem necessidade. **Não recriar isso como campo numa
sessão futura antes do CAPM existir de fato.**

### Pendente pra quando TAEE3 for populado (tarefa futura, não desta sessão)

Dois campos que ainda não existem em `PerfilSetor` e precisariam ser
adicionados antes de popular TAEE3 com dado real de DDM — ambos como
`CampoComProveniencia`, mesmo padrão dos campos já existentes:

- `dividendo_projetado` (ou `dpa_projetado`).
- `taxa_crescimento_perpetuidade_ddm`.

Nenhum dos dois foi criado nesta sessão — só a função pura, como pedido.

### `RegraPerfil` continua não implementado

Esta tarefa destrava a peça que faltava (um método real pra `RegraPerfil`
escolher), mas **não implementa o `Protocol` em si** — isso continua
pendente (ver "Decisões confirmadas" da Fase 1, acima). Agora que
`calcular_ddm()` existe, `RegraPerfil` pra `DDM_ONLY` deixa de esbarrar
no bloqueio "nenhum método de valuation existe" — mas ainda precisa ser
implementado numa sessão própria.

### Testes (8 novos, sem mocks)

`backend/tests/unit/test_ddm.py`: caso normal (números SINTÉTICOS
plausíveis — CONTEXT.md não tem os inputs reais de DDM do TAEE3
registrados, só a justificativa da tag, sem os números — ordem de
grandeza consistente com a faixa de preço real do TAEE3 já registrada em
"Calibração do limiar" acima), `ke == g` e `ke < g` levantam erro,
`dividendo_projetado <= 0` levanta erro (zero e negativo), `ke <= 0`
levanta erro (zero e negativo), `g` negativo permitido (caso de borda).
**65 testes passando no total** (57 anteriores + 8 novos).

## Fase 2 — primeira fatia: classificação de divergência (concluída)

Primeira peça da Fase 2 ("Sanity check contra mercado", ver
`docs/ROADMAP.md`). Investigação antes de implementar (pedido: "avançar
pra Fase 2") encontrou o mesmo tipo de lacuna já visto com
`RegraPerfil`: a fase completa (rodar nos 62 tickers, comparando "valor
calculado" real vs. preço de mercado real) está bloqueada — não existe
campo de preço de mercado em `PerfilSetor`, e não existe "valor
calculado" ponta a ponta pra nenhum ticker (DDM existe como função pura,
mas TAEE3 não está populado e `RegraPerfil` não existe). Escopo reduzido
a uma fatia mínima que não depende de nada disso: só a lógica de
classificação.

### O que foi implementado

`backend/src/alicerce/sanity/divergencia.py::classificar_divergencia(
valor_calculado, preco_mercado, limiar_moderada, limiar_severa) ->
ResultadoDivergencia` — função pura, mesmo padrão de
`descontinuidade_preco.py`/`ddm.py`. Retorna `classificacao`
(`"divergencia_severa"` | `"divergencia_moderada"` | `"dentro_da_faixa"`)
e `percentual_divergencia` (com sinal — positivo = valor calculado acima
do mercado). Mora em `sanity/`, que já estava reservado pra isso
(`README.md`: *"sanity/ — Fase 2 — divergência vs. mercado"*).

### Decisão de escopo desta sessão: limiares SEM default

`limiar_moderada`/`limiar_severa` são parâmetros **obrigatórios**, sem
valor default — decisão explícita, diferente do padrão usado em
`RAZAO_MAX_MIN_52W_SUSPEITA` (que tinha um default justificável por
padrões reais de grupamento/desdobramento na B3, calibrado depois contra
dado real). Aqui, `grep` confirmou que **nenhum valor de limiar de
divergência está referenciado em nenhum lugar de `CONTEXT.md` ou
`docs/ROADMAP.md`** — só os nomes das 3 classificações, nunca um
percentual. Inventar um número "razoável" agora seria uma escolha
implícita sem base, exatamente o que a Fase 0/1 do projeto sempre evitou
pra dado numérico. **Calibrar esses valores contra dado real (ou decisão
explícita do usuário) é uma tarefa pendente separada** — mesmo padrão já
usado pro limiar de descontinuidade de preço (implementado primeiro com
racional, calibrado depois contra 14 tickers reais).

Não valida a ordem relativa entre os dois limiares (`limiar_severa`
deveria ser ≥ `limiar_moderada` pra fazer sentido semântico, mas isso não
é forçado em código) — mesmo espírito de "não travar por precaução
excessiva não pedida" já aplicado ao `g` negativo do DDM.

### Testes (11 novos, sem mocks)

`backend/tests/unit/test_divergencia.py`: dentro da faixa, moderada,
severa, divergência negativa classificada pela magnitude (não pelo
sinal), bordas exatas nos dois limiares (não disparam) e logo acima
(disparam), `preco_mercado <= 0` levanta erro, e um teste que trava a
decisão de "sem default" (`TypeError` ao chamar sem os limiares).
**76 testes passando no total** (65 anteriores + 11 novos).

### Fora do escopo desta fatia (pendências explícitas)

- Tolerância derivada automaticamente de `PerfilSetor`/tags (hoje é só
  parâmetro direto).
- Campo de preço de mercado atual em `PerfilSetor` — não existe.
- Dashboard/relatório de maiores divergências.
- Rodar nos 62 tickers (Lote 2) — só os 6 pilotos existem hoje, e
  nenhum tem "valor calculado" ponta a ponta ainda.
- Calibração dos valores de `limiar_moderada`/`limiar_severa` — ver
  decisão acima.

## Frontend — esqueleto (concluído, fora da ordem de fases)

Pedido explícito do usuário pra ter um frontend rodando localmente,
adiantado frente ao `docs/ROADMAP.md` (que marca frontend como Fase 4+,
"Fases 0-3 são backend puro, sem UI"). Confirmado com o usuário antes de
implementar: stack (React + TypeScript + Vite, mesma base do
`valuation-tracker`), escopo (**só esqueleto rodando local, sem dado
real** — não junto com endpoint de API) e uso do `valuation-tracker`
como referência de CONFIGURAÇÃO, não de conteúdo.

### O que existe

`frontend/` deixou de ser só `.gitkeep` + `README.md`: projeto Vite
completo (`npm create vite@latest -- --template react-ts`, versões de
dependência resolvidas pelo scaffolding oficial, não fixadas à mão),
com `App.tsx` mínimo próprio do Alicerce (sem boilerplate de marketing
do template) e CSS mínimo com suporte a light/dark
(`prefers-color-scheme`, sem framework de CSS — nenhuma decisão de
design system foi tomada). `npm install`, `npm run build` e `npm run
lint` confirmados funcionando; servidor de dev testado de verdade no
browser (`npm run dev`, screenshot conferido, console sem erros).

### Decisões de configuração

- **Porta fixa 5180** (não a 5173 padrão do Vite) — o `valuation-tracker`
  antigo já ocupa 5173 localmente; os dois projetos rodam ao mesmo
  tempo sem conflito.
- **Sem proxy `/api`** — diferente do `vite.config.ts` do
  `valuation-tracker` (que aponta pra `localhost:8000`), porque o
  Alicerce não tem nenhum endpoint ainda. Comentário deixado no código
  apontando o padrão a seguir quando existir.
- **`oxlint`** em vez de `eslint` (usado no `valuation-tracker`) — é o
  padrão atual do scaffolding oficial do Vite, mais rápido; optei por
  não reverter pra uma ferramenta mais antiga só pra bater com a
  referência.
- `.claude/launch.json` criado (`npm run dev --prefix frontend`, porta
  5180) pra rodar via preview.

### Fora do escopo desta tarefa (de propósito)

Nenhuma chamada de API, nenhum dado real, nenhum endpoint criado no
backend, nenhuma decisão de design system/CSS framework, nenhum roteador
— tudo isso é Fase 4+ ou tarefa própria futura.

## Convenções ao pedir mudanças pro Claude Code

- Caminho de arquivo exato + número de linha quando for correção pontual.
- Testes de regressão baseados em AST, não mockados, quando o bug for de
  lógica de cálculo.
- Checar os dois call-sites relevantes antes de considerar resolvido
  (equivalente a `main.py` + `scanner/trabalhador.py` no projeto anterior —
  mapear os call-sites reais deste projeto aqui conforme forem surgindo).
- `git rebase -i` pra dobrar fixes no commit original antes de dar push.
