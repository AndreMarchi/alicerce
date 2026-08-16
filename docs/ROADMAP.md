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
- Detecção de descontinuidade na série histórica de preço (ex: razão entre
  máxima e mínima de 52 semanas acima de um limiar configurável) — sinal de
  evento societário (grupamento/desdobramento) não ajustado corretamente na
  fonte antes do dado chegar ao pipeline. Caso real que motiva este item:
  RVEE3 reportando variação de 52 semanas de R$0,68 a R$31,00.

**Critério de saída da fase:** os 5 tickers-piloto (TAEE3, GEPA4, WIZC3,
ITSA4, CPLE3) têm todos os campos fundamentais carregados com proveniência
completa, sem nenhum campo "mudo" (sem fonte registrada). Adicionalmente,
nenhum campo de preço com descontinuidade de série detectada (razão
máxima/mínima de 52 semanas acima do limiar configurável) segue adiante na
cascata de fontes sem `confianca="baixa"` e `motivo_override` preenchido —
a detecção força esse estado antes de o dado ser consumido por qualquer
cálculo posterior.

---

## Fase 1 — Motor de perfis compostos (a causa raiz)

**Status: PARCIAL, não concluída — 1 de N casos cobertos.** O motor de
tags (`perfis/motor.py`, `perfis/tags.py`) e o `RegraPerfil`
(`Protocol`) abaixo continuam desenhos separados: o motor de tags está
implementado; `RegraPerfil` em si (a composição de `N` regras com
precedência) continua só pseudocódigo. O que existe hoje é um roteador
mínimo pro caso `DDM_ONLY` isolado
(`pipeline/ddm_only.py::calcular_valor_ddm_only()`, deliberadamente NÃO
nomeado `RegraPerfil` — ver CONTEXT.md, "Roteamento mínimo DDM_ONLY",
pelos dois motivos exatos), sem `ContextoValuation`, sem os outros 3
perfis (insolvência, fundo incompatível, financeiro/seguradora,
patrimonial — todos abaixo, ainda pendentes), sem precedência entre
regras. Pseudocódigo abaixo mantido como estava — é o design GERAL, não
o que foi implementado até agora.

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
- Achado real que motiva priorização dentro de `RegraPerfil` (auditoria
  cruzando 9 tickers reais de prejuízo do usuário contra os bugs/
  pendências já documentados no `valuation-tracker` — evidência
  concreta, não hipótese): aplicar os mesmos métodos de valuation de
  forma genérica produz números estruturalmente errados por CATEGORIA,
  não só por caso pontual mal calibrado. 4 perfis confirmados, nesta
  ordem de prioridade:
  1. **Insolvência confirmada** (maior prioridade). **STATUS: detecção
     implementada, integração com pipeline PENDENTE** (ver CONTEXT.md,
     "Perfil de insolvência confirmada — portão de segurança"):
     `PerfilSetor.em_recuperacao_judicial` (bool, não
     `TagPerfilEconomico` — portão binário, ortogonal à composição de
     metodologia que as tags existentes alimentam) +
     `perfis/insolvencia.py::ticker_bloqueado_por_insolvencia()`, função
     pura sem hardcode de ticker, testada. Ainda NÃO composto com
     `pipeline/ddm_only.py` nem com nenhum resultado de valuation — como
     bloquear de fato (não calcular? calcular e marcar?) fica pra quando
     houver mais de um perfil pra compor de verdade. Caso real: LIGT3
     (Light S.A., recuperação judicial — pedido de encerramento
     protocolado jul/2026, ainda pendente de decisão judicial na data
     da investigação; não é um dos 6 tickers-piloto do Alicerce, só o
     caso que motiva o perfil — os 6 pilotos foram verificados
     individualmente e nenhum está em RJ, ver CONTEXT.md). O
     `valuation-tracker` tem `EMPRESAS_RECUPERACAO_JUDICIAL`, mas é
     lista hardcoded manual (só 4 tickers) com penalização de score
     fraca demais — não impede a empresa de aparecer bem ranqueada;
     o Alicerce não repete esse padrão (dado sempre via `PerfilSetor`,
     nunca lista hardcoded no código). Diferente dos outros 3 perfis
     abaixo: não é uma decisão de "qual método de valuation usar" — é
     um portão binário (isso não deveria aparecer como recomendação de
     compra, independente do score calculado). Mais simples de
     implementar que os outros 3, e o de maior risco se não existir.
  2. **Fundo/classe de ativo incompatível**. Caso real: RZAG11 (FIAGRO
     — fundo de crédito do agronegócio), mais 2 outros tickers
     terminados em "11" identificados na mesma auditoria (provavelmente
     FIIs). Sem tratamento especial, o `valuation-tracker` roda
     DCF/Graham/Bazin (métodos desenhados pra empresa com lucro/
     crescimento) num fundo que distribui quase toda a renda como
     dividendo por lei e não tem "crescimento" no sentido que esses
     métodos assumem. Erro mais grave estruturalmente (classe de ativo
     inteira incompatível, não só setor mal calibrado), mas barato de
     detectar (padrão de ticker/tipo de ativo já costuma vir
     identificado na fonte de dado).
  3. **Financeiro/seguradora**. Caso real: WIZC3 — o caso que motivou
     toda a consolidação de `PerfilSetor` no `valuation-tracker`: setor
     mal classificado rodava DCF/EV-EBITDA/Graham numa corretora de
     seguros, score 8,2 ("Muito Atrativa/Alta Convicção"); depois da
     correção (métodos marcados "Não aplicável" pra esse perfil), caiu
     pra 5,8 ("Neutra"). Já existe precedente resolvido no projeto
     irmão — a lógica de decisão (quais métodos não se aplicam a perfil
     financeiro) pode ser reaproveitada como referência de design, mesmo
     que os números/calibração sejam recalculados do zero no Alicerce.
  4. **Patrimonial/imóveis** (menor prioridade, mais difícil). Caso
     real: HBRE3 (HBR Realty) — o próprio `valuation-tracker` documenta
     isso como pendência não resolvida: fica em perfil genérico
     (fallback), sem calibração própria, com uma pergunta de modelagem
     em aberto (P/VP/NAV deveria ter peso maior que P/L pra esse
     perfil). Diferente dos outros 3 ("não aplicar método X"), esse caso
     exige desenhar uma abordagem de valuation nova (baseada em
     patrimônio, não em lucro) — possivelmente um método que nem existe
     ainda no Alicerce, não só roteamento de `PerfilSetor`.

  **Isso não desbloqueia nem antecipa a implementação de `RegraPerfil`**
  — a decisão de adiar continua valendo até existir mais de um método
  real de valuation no Alicerce (ver CONTEXT.md). É documentação
  antecipada de requisito pra quando `RegraPerfil` for retomado não
  precisar redescobrir isso do zero, não mudança de escopo da fase
  atual.
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
- Decisão de design registrada (não implementada nesta fase — só
  documentada, mesmo padrão de "casos pendentes resolvidos... decisão
  explícita, documentada" da Fase 1): liquidez de mercado (volume médio
  diário, dias negociados no período, free float) entra como novo campo em
  `PerfilSetor` ou como nova `TagPerfilEconomico` (ex: `LIQUIDEZ_BAIXA`) — e
  como isso interage com as tags já existentes (`DDM_ONLY`, `CONCESSAO`,
  `ESTATAL_CONTROLADA`, `SOTP_OBRIGATORIO`, `ALAVANCAGEM_USD`): é uma
  dimensão ortogonal que se combina livremente com qualquer uma delas, ou
  existem combinações que não fazem sentido na prática? Achado real que
  motiva este item: múltiplos "descontados" (P/VP baixo, P/L baixo) de
  microcaps ilíquidas (SOND3, BMKS3, HBTS5, AHEB3, RVEE3) ficam
  indistinguíveis de desconto de valor genuíno sem essa dimensão — o
  sanity check desta fase, sozinho, não resolve isso, porque o preço de
  mercado usado como referência é o próprio preço distorcido pela
  ausência de formação real.

**Critério de saída da fase:** rodando nos 62 tickers, o sistema aponta
divergências grandes — e ao investigar 3-5 delas manualmente, a causa é
identificável (dado ruim, perfil errado, ou divergência legítima de premissa).
A decisão de design sobre liquidez (campo vs. tag, ver Entregáveis) também
precisa estar registrada e documentada antes de fechar a fase, mesmo que a
implementação em si fique para uma fase posterior.

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
- Segregação por tese de investimento: tickers cujas `TagPerfilEconomico`
  representam teses de investimento incompatíveis entre si (ex:
  `SOTP_OBRIGATORIO` — desconto de holding/NAV — vs. um futuro perfil de
  turnaround operacional vs. um futuro perfil de qualidade a múltiplo
  premium) não competem no mesmo ranking/score comparável. O resultado do
  consenso é segregado em rankings separados por tese, ou, no mínimo,
  anotado explicitamente com a tese de origem em cada entrada — qual dos
  dois mecanismos usar é decisão desta fase, mas o requisito de nunca
  misturar teses incompatíveis num único ranking sem sinalização explícita
  é obrigatório desde já. Achado real que motiva este item: um screening
  comparativo colocou lado a lado holding com desconto de NAV (BRAP3),
  turnaround operacional (PFRM3), qualidade a múltiplo premium (RDOR3) e
  desconto por risco regulatório (CSED3) — todos competindo no mesmo score,
  sem segregação por tese.

**Critério de saída da fase:** faixa de valor dos 5 tickers-piloto é
plausível e cada componente do consenso é rastreável até sua fonte. Nenhum
ranking comparável final mistura tickers com `TagPerfilEconomico` de teses
incompatíveis sem segregação ou anotação explícita da tese de origem.

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
