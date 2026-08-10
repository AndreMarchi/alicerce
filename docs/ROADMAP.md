# Roadmap — Novo Projeto de Valuation (B3)

Estrutura em fases, pensada pra evitar herdar os problemas do projeto atual
(pipeline genérico, dado sem proveniência, falta de sanity check contra mercado).

Princípio geral: **cada fase precisa estar sólida e testada antes de avançar
para a próxima.** Resistir à tentação de pular pra sinais qualitativos/IA
antes do núcleo determinístico estar calibrado.

---

## Fase 0 — Fundação de dados (antes de qualquer cálculo)

**Objetivo:** ter uma base de dados com proveniência desde o primeiro commit.
Reformatar dado histórico depois é retrabalho caro (você já viveu isso com o
`PerfilSetor`).

**Entregáveis:**
- Schema de proveniência por campo:
  ```python
  @dataclass
  class CampoComProveniencia:
      valor: float
      fonte: Literal["manual", "cvm", "brapi", "yfinance"]
      confianca: Literal["alta", "media", "baixa"]
      data_atualizacao: date
      motivo_override: Optional[str] = None  # obrigatório se fonte == "manual"
  ```
- Cascata de fontes explícita (Fundamentus → Brapi → yfinance → CVM → manual),
  registrando qual fonte respondeu por campo, não só o valor final.
- Endpoint/CLI simples para override manual (`PUT /empresa/{ticker}/campo/{nome}`)
  exigindo `motivo_override`.
- Tabela de auditoria: quantos campos por ticker estão em override manual
  (sinal de fonte automática falha para aquele perfil).

**Critério de saída da fase:** os 5 tickers-piloto (TAEE3, GEPA4, WIZC3,
ITSA4, CPLE3) têm todos os campos fundamentais carregados com proveniência
completa, sem nenhum campo "mudo" (sem fonte registrada).

---

## Fase 1 — Motor de perfis compostos (a causa raiz)

**Objetivo:** substituir "um pipeline pra todos" por perfis como tags que
se combinam, cada uma contribuindo uma regra de cálculo.

**Entregáveis:**
```python
empresa.perfis: list[str]  # ex: ["concessao_com_prazo", "estatal_controlada"]

class RegraPerfil(Protocol):
    def aplicar(self, contexto: ContextoValuation) -> ContextoValuation: ...

REGRAS: dict[str, RegraPerfil] = {
    "regulatorio_payout_alto": RegraPayoutAlto(),   # → força DDM, desliga FCFE
    "concessao_com_prazo": RegraConcessao(),         # → terminal value probabilístico
    "holding": RegraHolding(),                       # → força SOTP
    "estatal_controlada": RegraEstatal(),            # → +2pp WACC
    "seguros": RegraSeguros(),                       # → novo, do WIZC3
    "generico_dcf": RegraFallback(),                 # → fallback explícito, não default disfarçado
}
```
- Classificação dos ~62 tickers existentes em perfis (não mais só setor).
  Esperado: 5-8 perfis cobrem ~90% dos casos.
- Casos pendentes (Educação, Exploração de Imóveis) resolvidos como perfil
  novo ou confirmados como exceção genuína — decisão explícita, documentada.
- Testes unitários por perfil: dado um `ContextoValuation` de entrada, a
  regra aplica exatamente o que se espera (ex: perfil `holding` nunca chama
  DCF direto).

**Critério de saída da fase:** os 5 tickers-piloto rodam pelo motor novo e
produzem o método/ajuste esperado (documentado manualmente antes, como
"gabarito" de comportamento — não de valor final).

---

## Fase 2 — Sanity check contra mercado

**Objetivo:** o alarme mais barato de implementar e o que teria pego
CPLE3/WIZC3 mais cedo.

**Entregáveis:**
- Comparação automática: valor calculado vs. preço de mercado atual, com
  faixa de tolerância configurável por perfil (regulatórias toleram menos
  divergência que cíclicas, por exemplo).
- Alerta estruturado (não só log): `divergencia_severa`, `divergencia_moderada`,
  `dentro_da_faixa` — com o percentual de divergência explícito.
- Dashboard/relatório simples: lista de tickers com maior divergência, pra
  revisão manual priorizada (você não vai revisar 327 tickers manualmente,
  mas os top 10 divergentes sim).

**Critério de saída da fase:** rodando nos 62 tickers, o sistema aponta
divergências grandes — e ao investigar 3-5 delas manualmente, a causa é
identificável (dado ruim, perfil errado, ou divergência legítima de premissa).

---

## Fase 3 — CAPM/WACC interno (portar, não reconstruir)

**Objetivo:** você já tem boa parte disso funcionando hoje (`capm.py`,
`divergencia_beta`, `aviso_beta`). Esta fase é mais migração e limpeza do
que construção do zero.

**Entregáveis:**
- Port do cálculo de beta interno + comparação com beta de mercado
  (Yahoo Finance), mantendo o `aviso_beta` quando diverge ≥0.35.
- WACC com teto/piso (16%/10% CAPM, 20%/8% WACC) e prêmio de governança
  (+2pp) como regra do perfil `estatal_controlada` (Fase 1), não hardcoded
  solto no cálculo.
- Garantir que WACC nunca fica capado abaixo do Ke próprio (bug do WIZC3)
  — teste de regressão específico pra esse caso.

**Critério de saída da fase:** WACC/CAPM dos 5 tickers-piloto batem com os
valores que você já validou manualmente no projeto atual.

---

## Fase 4 — Consenso multi-método

**Objetivo:** só faz sentido depois que os métodos individuais já são
confiáveis por perfil (Fases 1-3). Consenso de métodos ruins mascara o
problema.

**Entregáveis:**
- Por perfil, lista explícita de métodos aplicáveis e peso relativo
  (ex: `regulatorio_payout_alto` → DDM peso 0.7, Graham peso 0.3, FCFE
  peso 0).
- Cálculo de faixa (não ponto único): mínimo, máximo, mediana entre os
  métodos ponderados.
- Registro de qual método "puxou" o resultado final, pra rastreabilidade.

**Critério de saída da fase:** faixa de valor dos 5 tickers-piloto é
plausível e cada componente do consenso é rastreável até sua fonte.

---

## Fase 5 — Backtesting

**Objetivo:** depende de histórico acumulado — mas o *schema* de log
precisa nascer na Fase 0/1, senão você só começa a acumular dado útil
daqui um ano.

**Entregáveis:**
- Log de toda predição com timestamp, perfil aplicado, faixa de valor,
  preço de mercado no momento (já deve estar sendo gravado desde a Fase 2).
- Métrica de erro histórico por perfil: "modelo com perfil X erra em média
  Y% pra mais/menos, desvio padrão Z" — isso quantifica a banda de
  incerteza real do seu framework.
- Relatório periódico (mensal?) comparando predição passada vs. preço
  realizado.

**Critério de saída da fase:** pelo menos um ciclo completo de comparação
predição-vs-realizado rodado, com métrica de erro por perfil documentada.

---

## Fase 6 (futura, opcional) — Sinais qualitativos via busca/LLM

**Objetivo:** deixado por último de propósito — é a peça mais arriscada
(alucinação, verificação de fonte) e a que menos resolve a causa raiz atual.
Só entra quando o núcleo (Fases 0-5) já está estável e você tem backtesting
rodando pra medir se isso realmente ajuda ou só adiciona ruído.

**Entregáveis (quando chegar a hora):**
- Sinais como input estruturado, nunca como número final direto:
  ```python
  sinal_qualitativo = {
      "tipo": "guidance_capex" | "risco_regulatorio" | "sentimento_analistas",
      "valor": ...,
      "fonte_url": "...",
      "data_publicacao": "...",
      "confianca": "alta" | "media" | "baixa",
  }
  ```
- Regra explícita de como o sinal afeta o cálculo (ex: "se
  `risco_regulatorio` ativo, desconto de X% no valor final") — nunca um
  modelo de ML decidindo isso de forma opaca.
- Exigência de cruzamento com pelo menos 2 fontes antes de virar input
  confiável; abaixo disso, vira alerta pra revisão manual, não input direto.

**Critério de saída:** comparar backtesting com e sem o sinal qualitativo
ligado — só mantém se mensuravelmente reduzir o erro médio.

---

## Ordem de migração de tickers

1. **Piloto (5 tickers):** TAEE3, GEPA4, WIZC3, ITSA4, CPLE3 — já
   analisados a fundo, servem de caso de teste pro motor novo.
2. **Lote 2:** os outros ~57 tickers já classificados no `PerfilSetor`
   atual, migrados perfil a perfil (todos os `holding` primeiro, depois
   `concessao_com_prazo`, etc.) — não tudo de uma vez.
3. **Lote 3:** os ~265 tickers restantes do universo de 327, à medida que
   o `auditoria_setorial.py` (ou equivalente no projeto novo) for
   revelando quais perfis eles precisam.

---

## O que fica fora do escopo (lembrete)

- Rede neural / modelo de ML treinado para prever valor final — descartado
  pelas razões discutidas (poucos dados, sem y verdadeiro, caixa-preta).
- "Preço objetivo independente da cotação" como meta — substituído por
  "faixa de valor justificável + comparação honesta com o mercado".
- Sinais qualitativos no MVP — adiado para Fase 6.
