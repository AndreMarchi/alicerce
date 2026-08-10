# Alicerce

Motor de valuation para ações da B3, construído para resolver a causa raiz
dos problemas do `valuation-tracker`: pipeline genérico aplicado a perfis
de empresa fundamentalmente diferentes, sem proveniência de dado e sem
sanity check contra o mercado.

Ver `CONTEXT.md` para princípios de arquitetura e `docs/ROADMAP.md` para
o plano de fases completo (Fase 0 a Fase 6).

## Estrutura

```
alicerce/
├── CONTEXT.md              # ponto de entrada — leia antes de mexer em qualquer coisa
├── docs/
│   └── ROADMAP.md           # plano de fases completo
├── src/alicerce/
│   ├── proveniencia/        # Fase 0 — schema de proveniência por campo
│   ├── perfis/               # Fase 1 — motor de perfis compostos
│   ├── pipeline/              # orquestração calculation-pipeline
│   ├── sanity/                # Fase 2 — divergência vs. mercado
│   ├── capm/                  # Fase 3 — CAPM/WACC interno
│   ├── consenso/              # Fase 4 — consenso multi-método
│   ├── backtesting/           # Fase 5
│   └── qualitativo/           # Fase 6 (futuro) — sinais via LLM
├── api/                      # entrypoint FastAPI (a definir)
├── scripts/                  # scripts utilitários (ex: atualização CVM)
└── tests/
    ├── unit/
    ├── regression/
    ├── integration/
    ├── provenance_contract/
    └── sanity/
```

## Status

🚧 Fase 0 em andamento — schema de proveniência (`src/alicerce/proveniencia/schema.py`)
já tem uma primeira versão. Próximo passo: cascata de fontes real
(Fundamentus → Brapi → yfinance → CVM) e carga dos 5 tickers-piloto.

## Tickers-piloto

`TAEE3`, `GEPA4`, `WIZC3`, `ITSA4`, `CPLE3` — já analisados a fundo no
projeto anterior, servem de gabarito de comportamento esperado para o
motor de perfis (Fase 1).
