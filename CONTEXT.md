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

## Convenções ao pedir mudanças pro Claude Code

- Caminho de arquivo exato + número de linha quando for correção pontual.
- Testes de regressão baseados em AST, não mockados, quando o bug for de
  lógica de cálculo.
- Checar os dois call-sites relevantes antes de considerar resolvido
  (equivalente a `main.py` + `scanner/trabalhador.py` no projeto anterior —
  mapear os call-sites reais deste projeto aqui conforme forem surgindo).
- `git rebase -i` pra dobrar fixes no commit original antes de dar push.
