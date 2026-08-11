# Alicerce

Motor de valuation para ações da B3, construído para resolver a causa raiz
dos problemas do `valuation-tracker`: pipeline genérico aplicado a perfis
de empresa fundamentalmente diferentes, sem proveniência de dado e sem
sanity check contra o mercado.

Ver `CONTEXT.md` para princípios de arquitetura e `docs/ROADMAP.md` para
o plano de fases completo (Fase 0 a Fase 6).

## Estrutura

Monorepo desde a Fase 1: `backend/` (todo o código Python) e `frontend/`
(reservado, sem código ainda — ver `frontend/README.md`). `CONTEXT.md`,
`README.md` e `docs/` ficam na raiz por descreverem o projeto como um
todo, não só o backend.

```
alicerce/
├── CONTEXT.md                  # ponto de entrada — leia antes de mexer em qualquer coisa
├── docs/
│   └── ROADMAP.md               # plano de fases completo
├── backend/
│   ├── pyproject.toml
│   ├── src/alicerce/
│   │   ├── proveniencia/        # Fase 0 — schema de proveniência por campo
│   │   ├── perfis/               # Fase 1 — motor de perfis compostos
│   │   ├── pipeline/              # orquestração calculation-pipeline
│   │   ├── sanity/                # Fase 2 — divergência vs. mercado
│   │   ├── capm/                  # Fase 3 — CAPM/WACC interno
│   │   ├── consenso/              # Fase 4 — consenso multi-método
│   │   ├── backtesting/           # Fase 5
│   │   └── qualitativo/           # Fase 6 (futuro) — sinais via LLM
│   ├── api/                      # entrypoint FastAPI (a definir)
│   ├── scripts/                  # scripts utilitários (ex: atualização CVM)
│   └── tests/
│       ├── unit/
│       ├── regression/
│       ├── integration/
│       ├── provenance_contract/
│       └── sanity/
└── frontend/                     # reservado, sem stack decidida ainda
```

## Como rodar (backend)

```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Status

✅ Fase 0 concluída — schema de proveniência (`backend/src/alicerce/proveniencia/schema.py`).

✅ Fase 1 concluída — motor de perfis (`backend/src/alicerce/perfis/`):
`PerfilSetor` (`perfil_setor.py`), tags de perfil econômico (`tags.py`) e
o motor (`motor.py`, `obter_perfil`/`obter_tags`/`obter_atribuicoes_tags`),
com os 6 tickers-piloto cadastrados em `dados/perfis_ticker.json`. 43
testes passando (`backend/tests/unit`, `backend/tests/provenance_contract`).
Ver `CONTEXT.md`, seção "Fase 1 — Motor de Perfis", para a investigação e
decisões por trás disso.

✅ Reorganizado em monorepo (`backend/`/`frontend/`) — ver `CONTEXT.md`,
seção "Estrutura de monorepo". Nenhuma mudança de lógica, só de caminho;
os 43 testes continuam passando a partir de `backend/`.

Próximo passo (Fase 2): sanity checks contra mercado e `RegraPerfil`
(composição de tags em decisão de metodologia).

## Tickers-piloto

`TAEE3`, `GEPA4`, `WIZC3`, `ITSA4`, `CPLE3`, `BEEF3` — já analisados a
fundo no projeto anterior, servem de gabarito de comportamento esperado
para o motor de perfis (Fase 1).
