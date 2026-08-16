"""
CAPM (Capital Asset Pricing Model) — cálculo do custo de capital próprio
(Ke). Fórmula portada de valuation-tracker/backend/valuation/capm.py,
confirmada lendo o arquivo inteiro nesta sessão (ver CONTEXT.md, "CAPM
(Ke) — função pura") — não reconstituída de memória.

Função pura, mesmo padrão de valuation/ddm.py e
proveniencia/descontinuidade_preco.py: recebe `rf`, `beta`,
`valor_mercado` e `eh_estatal` como PARÂMETROS diretos — não busca
setor, `PerfilSetor` nem `TagPerfilEconomico.ESTATAL_CONTROLADA`
internamente. Quem chama decide.
"""

from __future__ import annotations

# Componentes fixos do modelo, confirmados direto no corpo de
# valuation-tracker/backend/valuation/capm.py::calcular_capm() — não a
# constante de módulo PREMIO_RISCO_MERCADO=0.03 de lá, que é código
# morto (nunca lida na função; o ERP realmente usado é o literal inline
# erp=0.055).
EQUITY_RISK_PREMIUM = 0.055  # 5,5%
COUNTRY_RISK_PREMIUM = 0.025  # 2,5%
PREMIO_RISCO_ESTATAL_PP = 0.02  # 2 p.p., quando eh_estatal=True

# Teto/piso de segurança do Ke — DECISÃO CONSCIENTE do Alicerce, NÃO
# cópia fiel do valuation-tracker. Lá, TAXA_DESCONTO_MINIMA/MAXIMA
# existem como constantes de módulo mas `calcular_capm()` nunca as
# aplica ao `taxa_desconto` retornado — código morto, confirmado lendo
# a função inteira (só o WACC, função separada, tem clamp de verdade
# lá). Aplicamos de verdade aqui porque docs/ROADMAP.md do Alicerce já
# documenta essa intenção explicitamente ("WACC com teto/piso — 16%/10%
# CAPM, 20%/8% WACC"), e um Ke sem limite alimenta o bug conhecido do
# WIZC3 (WACC clampado numa faixa fixa, independente do Ke real do
# ticker — ainda NÃO corrigido; WACC nem existe no Alicerce ainda, ver
# CONTEXT.md). NÃO reverter isso achando que é discrepância acidental
# frente ao código-fonte — é proposital.
TAXA_DESCONTO_MINIMA = 0.10  # 10%
TAXA_DESCONTO_MAXIMA = 0.16  # 16%

# Faixas de erro de CHAMADA óbvio — diferente do clamp de saída acima.
# Distinção deliberada (ver docstring de calcular_capm()): o clamp
# absorve valor PLAUSÍVEL-MAS-EXTREMO (ex: beta=1.8 de um ticker
# genuinamente volátil produzindo Ke > 16%) sem reclamar — isso é o
# papel dele. As faixas abaixo pegam o outro tipo de problema: um número
# que não é um beta/rf real de jeito nenhum, sinal de erro de escala em
# quem chama (ex: `rf=14.5` em vez de `rf=0.145`, ou `beta=65` por
# confundir com beta×100) — aí faz mais sentido travar cedo do que deixar
# o clamp mascarar um bug de chamada como se fosse um Ke normal.
BETA_MINIMO_PLAUSIVEL = -3.0
BETA_MAXIMO_PLAUSIVEL = 5.0


def calcular_capm(rf: float, beta: float, valor_mercado: float, eh_estatal: bool) -> float:
    """
    Custo de capital próprio (Ke) via CAPM:

        Ke = rf + beta × EQUITY_RISK_PREMIUM + COUNTRY_RISK_PREMIUM
             + size_premium(valor_mercado) + prêmio_estatal(eh_estatal)

    sempre clampado em [`TAXA_DESCONTO_MINIMA`, `TAXA_DESCONTO_MAXIMA`]
    (ver racional da constante acima).

    `size_premium` por faixa de `valor_mercado` (R$), idêntico ao
    valuation-tracker: > R$50bi → 0%; > R$10bi → 1%; > R$2bi → 2%;
    > R$0 → 3,5%; <= R$0 → 1,5% (fallback pra quando o dado de valor de
    mercado falha, mesmo comportamento de lá — não é bug, é o
    fallback deliberado da fonte original). `valor_mercado` não é
    validado além disso — esse fallback já é o tratamento intencional
    pra `valor_mercado <= 0`, não um erro.

    Duas validações, levantando `ValueError` (mesmo padrão de
    `valuation/ddm.py`) — mas só pra erro de CHAMADA óbvio, não pra
    valor extremo-mas-real (esse continua sendo papel do clamp de saída
    acima, que não muda):

    - `beta` fora de `[BETA_MINIMO_PLAUSIVEL, BETA_MAXIMO_PLAUSIVEL]`
      (`[-3, 5]`, bordas inclusas). Nenhum ativo real do universo do
      Alicerce deveria ter beta nesse extremo (os 3 betas de referência
      já cadastrados em `PerfilSetor` — 0,65/0,90/0,85 — ficam bem
      dentro); um valor assim é sinal de erro de escala na chamada (ex:
      confundir beta com beta×100), não beta real extremo.
    - `rf` negativo (`rf < 0`; `rf == 0.0` é aceito). Taxa livre de
      risco negativa não faz sentido no contexto de Selic/BRL que o
      projeto usa — um `rf` negativo chegando aqui é sinal de erro de
      escala (ex: `rf=14.5` em vez de `rf=0.145`) ou bug em quem chama,
      não um cenário real a suportar silenciosamente.

    Fora dessas duas faixas de erro óbvio, `rf`/`beta` continuam sem
    guard adicional — um beta plausível-mas-extremo (e.g. 1.8) que
    produza Ke > 16% é exatamente o caso que o clamp de saída existe
    pra absorver, não pra travar. Mesmo espírito da decisão de permitir
    `g` negativo em `valuation/ddm.py`: não travar por precaução além
    do que foi identificado como erro real de chamada.
    """
    if beta < BETA_MINIMO_PLAUSIVEL or beta > BETA_MAXIMO_PLAUSIVEL:
        raise ValueError(
            f"beta ({beta}) fora da faixa plausível "
            f"[{BETA_MINIMO_PLAUSIVEL}, {BETA_MAXIMO_PLAUSIVEL}] — sinal de "
            "erro de escala na chamada (ex: beta×100 por engano), não beta "
            "real extremo."
        )
    if rf < 0:
        raise ValueError(
            f"rf ({rf}) não pode ser negativo — sinal de erro de escala na "
            "chamada (ex: rf=14.5 em vez de rf=0.145) ou bug em quem chama."
        )

    if valor_mercado > 50_000_000_000:
        size_premium = 0.00
    elif valor_mercado > 10_000_000_000:
        size_premium = 0.01
    elif valor_mercado > 2_000_000_000:
        size_premium = 0.02
    elif valor_mercado > 0:
        size_premium = 0.035
    else:
        size_premium = 0.015

    premio_estatal = PREMIO_RISCO_ESTATAL_PP if eh_estatal else 0.0

    ke = rf + (beta * EQUITY_RISK_PREMIUM) + COUNTRY_RISK_PREMIUM + size_premium + premio_estatal

    return max(TAXA_DESCONTO_MINIMA, min(ke, TAXA_DESCONTO_MAXIMA))
