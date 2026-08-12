"""
DDM (Dividend Discount Model) — Gordon Growth, crescimento constante na
perpetuidade. Fórmula pura: `Ke` e `g` são recebidos como PARÂMETROS,
nunca calculados aqui — o Alicerce ainda não tem CAPM (Fase 3), e essa
função não deve criar essa dependência prematuramente (ver CONTEXT.md,
"Investigação — qual método implementar primeiro"). Mesmo padrão de
função pura já usado em `proveniencia/descontinuidade_preco.py`.

Motivação: TAEE3 é o único ticker-piloto com
`TagPerfilEconomico.DDM_ONLY` — transmissora de energia com RAP
(Receita Anual Permitida) contratada e payout historicamente próximo de
100% do lucro regulatório (ver CONTEXT.md, "Fase 1 — Motor de Perfis").

Este módulo mora em `valuation/` — nenhum dos pacotes vazios já
existentes (`pipeline/`, `capm/`, `consenso/`, `sanity/`, `qualitativo/`,
`backtesting/`) é descrito em `README.md`/`docs/ROADMAP.md` como o lugar
dos MÉTODOS de valuation individuais: `pipeline/` é "orquestração
calculation-pipeline" (orquestra estágios, não é onde a fórmula mora),
`capm/` é especificamente CAPM/WACC (Fase 3), `consenso/` combina
métodos já calculados (Fase 4). `valuation/` é pacote novo — mesmo termo
já usado em todo o projeto pra se referir a "métodos de valuation"
(ver `tags.py`, `CONTEXT.md`).
"""

from __future__ import annotations


def calcular_ddm(dividendo_projetado: float, ke: float, g: float) -> float:
    """
    Valor intrínseco por ação via DDM de crescimento constante (Gordon
    Growth): `dividendo_projetado / (ke - g)`.

    Validações (explícitas, nunca um valor inválido em silêncio — mesmo
    princípio de "nenhum campo mudo" do resto do projeto):

    - `dividendo_projetado` (D1, dividendo esperado no próximo período)
      precisa ser > 0 — dividendo zero ou negativo não é um caso válido
      pra este método (uma empresa sem dividendo positivo esperado não
      deveria carregar a tag `DDM_ONLY` pra começo de conversa).
    - `ke` (custo de capital próprio) precisa ser > 0.
    - `ke` precisa ser ESTRITAMENTE MAIOR que `g` — na perpetuidade, um
      crescimento igual ou maior que a taxa de desconto diverge
      (denominador zero ou negativo), sem sentido matemático.

    Decisão de design (revisar se discordar): `g` PODE ser negativo — é
    matematicamente válido no modelo (cenário de declínio de dividendo)
    e não há nenhum critério documentado no projeto pra proibir isso;
    travar por precaução não pedida seria inventar uma regra de negócio
    nova sem base. Só o guard `ke > g` acima cobre o caso patológico
    (e já cobre `g` muito negativo automaticamente, já que isso só
    afasta `ke` de `g`, nunca aproxima).
    """
    if dividendo_projetado <= 0:
        raise ValueError(
            "dividendo_projetado precisa ser > 0 (recebido: "
            f"{dividendo_projetado}) — DDM pressupõe uma empresa "
            "pagadora de dividendos."
        )
    if ke <= 0:
        raise ValueError(f"ke precisa ser > 0 (recebido: {ke}).")
    if ke <= g:
        raise ValueError(
            f"ke ({ke}) precisa ser maior que g ({g}) — na "
            "perpetuidade, crescimento igual ou maior que a taxa de "
            "desconto diverge."
        )
    return dividendo_projetado / (ke - g)
