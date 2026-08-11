"""
Tags de perfil econômico — Fase 1 do motor de perfis.

LIMITE DE RESPONSABILIDADE (ver CONTEXT.md, "Fase 1 — Motor de Perfis"):
este módulo é só o "O QUÊ" — quais tags um ticker tem. Nunca o "QUANDO
APLICAR" cada uma. A composição de regras que traduz tags em decisão de
metodologia (ex: "DDM_ONLY implica desligar DCF/FCFE e usar DDM como
método principal") é responsabilidade de `RegraPerfil`
(`Protocol`, ver docs/ROADMAP.md), ainda não implementado — fica pra
Fase 2, quando houver métodos de valuation de verdade pra essas regras
decidirem entre. Um consumidor futuro faz
`TagPerfilEconomico.DDM_ONLY in obter_tags(ticker)` e decide por conta
própria o que fazer — este módulo não decide nada, só descreve.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TagPerfilEconomico(str, Enum):
    """
    Tag composable de situação econômica especial de um ticker — um
    ticker pode ter zero, uma ou várias tags simultaneamente (ver
    `perfis/motor.py::obter_tags`).

    Confirmadas por investigação real no valuation-tracker (ver
    CONTEXT.md, "Fase 1 — Motor de Perfis"):

    - CONCESSAO: negócio opera sob contrato de concessão com prazo
      definido. Ex: GEPA4 — já parametrizado como `"concessao"` em
      `valuation-tracker/dados/perfil_dcf.json`.
    - ESTATAL_CONTROLADA: controle estatal, mesmo que via golden share
      pós-privatização. Ex: CPLE3 — confirmado em
      `valuation-tracker/valuation/risco.py::EMPRESAS_CONTROLE_ESTATAL`.
    - SOTP_OBRIGATORIO: holding/conglomerado cujo valor deve ser somado
      por segmento/participação (Sum-of-the-Parts), nunca por múltiplo
      consolidado único. Ex: ITSA4 — confirmado em
      `valuation-tracker/dados/sotp_config.json::ITSA4` (7 segmentos via
      `valor_participacao`).
    - ALAVANCAGEM_USD: dívida majoritariamente em moeda estrangeira — o
      custo de dívida (Kd) precisa de spread cambial. Ex: BEEF3, 90% da
      dívida bruta em moeda estrangeira, dado real confirmado em
      `valuation-tracker/valuation/wacc.py`.

    NOVA nesta fase, SEM precedente no valuation-tracker:

    - DDM_ONLY: negócio com payout historicamente próximo de 100% do
      lucro (ex: TAEE3 — transmissora de energia com RAP contratada). Não
      existe módulo de Dividend Discount Model no valuation-tracker; esta
      tag nasce de análise externa ao projeto anterior e é documentada
      pela primeira vez aqui.
    """

    DDM_ONLY = "ddm_only"
    CONCESSAO = "concessao"
    ESTATAL_CONTROLADA = "estatal_controlada"
    SOTP_OBRIGATORIO = "sotp_obrigatorio"
    ALAVANCAGEM_USD = "alavancagem_usd"


@dataclass(frozen=True)
class AtribuicaoTag:
    """
    Uma tag atribuída a um ticker, com justificativa obrigatória —
    auditável, mesmo espírito do `motivo_override` de
    `proveniencia/schema.py` (Fase 0). Imutável: uma atribuição já feita
    não deve ser mutada em memória, só substituída na fonte de dados.
    """

    tag: TagPerfilEconomico
    justificativa: str

    def __post_init__(self) -> None:
        if not self.justificativa or not self.justificativa.strip():
            raise ValueError(
                f"AtribuicaoTag para '{self.tag}' exige justificativa não-vazia "
                "— tag sem justificativa não é auditável."
            )
