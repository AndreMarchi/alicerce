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
   confiança e data. Ver `src/alicerce/proveniencia/schema.py`.
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
núcleo determinístico (Fases 0-3) estar calibrado nos 5 tickers-piloto:
`TAEE3, GEPA4, WIZC3, ITSA4, CPLE3`.

## Estratégia de testes

- `tests/unit` — regra por regra, isolada (`ContextoValuation` de entrada
  → saída esperada).
- `tests/regression` — casos que já quebraram uma vez (ex: WACC capado
  abaixo do Ke, capex undercapture) não podem voltar a quebrar.
- `tests/integration` — pipeline completo, ticker piloto de ponta a ponta.
- `tests/provenance_contract` — nenhum campo sai "mudo" do pipeline.
- `tests/sanity` — divergência calculado-vs-mercado dentro da faixa
  esperada por perfil.

## Convenções ao pedir mudanças pro Claude Code

- Caminho de arquivo exato + número de linha quando for correção pontual.
- Testes de regressão baseados em AST, não mockados, quando o bug for de
  lógica de cálculo.
- Checar os dois call-sites relevantes antes de considerar resolvido
  (equivalente a `main.py` + `scanner/trabalhador.py` no projeto anterior —
  mapear os call-sites reais deste projeto aqui conforme forem surgindo).
- `git rebase -i` pra dobrar fixes no commit original antes de dar push.
