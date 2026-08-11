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

✅ Fase 0 concluída — schema de proveniência (`src/alicerce/proveniencia/schema.py`).

✅ Fase 1 concluída — motor de perfis (`src/alicerce/perfis/`): `PerfilSetor`
(`perfil_setor.py`), tags de perfil econômico (`tags.py`) e o motor
(`motor.py`, `obter_perfil`/`obter_tags`/`obter_atribuicoes_tags`), com os
6 tickers-piloto cadastrados em `dados/perfis_ticker.json`. 43 testes
passando (`tests/unit`, `tests/provenance_contract`). Ver `CONTEXT.md`,
seção "Fase 1 — Motor de Perfis", para a investigação e decisões por
trás disso.

Próximo passo (Fase 2): sanity checks contra mercado e `RegraPerfil`
(composição de tags em decisão de metodologia).

## Tickers-piloto

`TAEE3`, `GEPA4`, `WIZC3`, `ITSA4`, `CPLE3`, `BEEF3` — já analisados a
fundo no projeto anterior, servem de gabarito de comportamento esperado
para o motor de perfis (Fase 1).
