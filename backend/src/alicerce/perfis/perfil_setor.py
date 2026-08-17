"""
Perfil setorial por ticker — Fase 1 do motor de perfis.

Ver CONTEXT.md, seção "Fase 1 — Motor de Perfis", para a investigação real
no valuation-tracker que fundamenta estes campos
(valuation/perfil_setor.py, wacc.py, sotp.py) e para a decisão de projetar
o perfil por TICKER, não por setor com cascata no schema — a cascata
existe só como mecanismo de carga de dados (ver "Herança de setor" no
CONTEXT.md), não como um conceito do schema em si.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from alicerce.proveniencia.schema import CampoComProveniencia

# Classe de instrumento negociado — não confundir com `setor`/`subsetor`
# (economia do negócio). "acao"/"unit" representam uma empresa real
# (ação ordinária/preferencial ou bundle ON+PN); "fiagro"/"fii" são
# fundos, sem "lucro"/"crescimento" no sentido que DDM/DCF/Graham
# assumem — ver `perfis/classe_ativo.py`.
ClasseAtivo = Literal["acao", "unit", "fiagro", "fii"]


@dataclass
class PerfilSetor:
    """
    Perfil setorial de um ticker. Campos de classificação (`eh_regulado`,
    `eh_ciclico`, `taxonomia_financeira_especial`) são booleanos simples —
    fora do escopo de proveniência da Fase 0, que cobre só "campo de dado
    NUMÉRICO relevante" (ver CONTEXT.md). Campos numéricos de referência
    usam `CampoComProveniencia`: nunca um float cru, sempre com fonte,
    confiança e data — ver `tests/provenance_contract/`.
    """

    ticker: str
    setor: str
    subsetor: Optional[str] = None

    eh_regulado: bool = False
    eh_ciclico: bool = False
    # Bancos/seguradoras/holdings financeiras: EBIT/EBITDA/FCF não são
    # conceitos limpos pro negócio (mesma razão documentada em
    # valuation-tracker/valuation/perfil_setor.py pra bancos/seguradoras).
    taxonomia_financeira_especial: bool = False
    # Perfil patrimonial/imóveis — quarto e último dos 4 perfis de
    # RegraPerfil do docs/ROADMAP.md (auditoria do valuation-tracker;
    # caso real: HBRE3, não um dos 6 pilotos do Alicerce). Bool simples,
    # mesmo padrão dos campos de classificação acima — SÓ identifica o
    # perfil, não decide nem bloqueia nada. Investigado antes de criar
    # (mesmo processo que confirmou reaproveitar
    # `taxonomia_financeira_especial` pro perfil financeiro): nenhum
    # campo existente cobria isso, criado novo. NÃO existe função de
    # cálculo nem de bloqueio associada — a pergunta de qual método de
    # valuation caberia pra esse perfil (P/VP/NAV vs. P/L) é decisão de
    # modelagem financeira EM ABERTO, deliberadamente não respondida
    # aqui — ver CONTEXT.md, "Perfil patrimonial/imóveis", pela
    # especificação completa da pergunta.
    perfil_patrimonial: bool = False
    # Controle estatal (governo, direto ou golden share), consumido
    # diretamente por capm.calcular_capm(eh_estatal=...) — bool simples
    # como os demais campos de classificação acima, não
    # CampoComProveniencia, porque não é um DADO NUMÉRICO (ver docstring
    # da classe). Deliberadamente separado de
    # `TagPerfilEconomico.ESTATAL_CONTROLADA` (tags.py): a tag existe pra
    # composição de metodologia via `RegraPerfil` (ainda não
    # implementado), este campo é o input direto e mais estreito que o
    # CAPM já consome hoje. Ver CONTEXT.md, "TAEE3 — dados reais para
    # DDM+CAPM", pela decisão de eh_estatal=False para TAEE3 apesar da
    # CEMIG (estatal mineira) ser sócia controladora em conjunto com a
    # ISA Brasil — controle é COMPARTILHADO, nenhuma das duas partes tem
    # maioria isolada, e o mercado descreve a TAESA como empresa privada.
    eh_estatal: bool = False

    # Insolvência confirmada (recuperação judicial) — PORTÃO BINÁRIO, não
    # uma decisão de método de valuation (ver docs/ROADMAP.md, Fase 1,
    # perfil de maior prioridade dos 4 encontrados na auditoria: "isso
    # não deveria produzir recomendação de compra, independente do que
    # qualquer método calcule"). Bool simples, mesmo padrão de
    # `eh_estatal`/`eh_regulado` acima — não CampoComProveniencia (não é
    # dado numérico), e deliberadamente NÃO uma `TagPerfilEconomico`
    # nova (tags.py): as tags existentes (`DDM_ONLY`, `CONCESSAO`, etc.)
    # alimentam a composição de METODOLOGIA via `RegraPerfil` (qual
    # método usar); insolvência é ortogonal a isso — é um pré-filtro que
    # bloqueia recomendação ANTES de qualquer método rodar, não mais uma
    # entrada no mesmo conjunto de tags. Ver
    # `perfis/insolvencia.py::ticker_bloqueado_por_insolvencia()` e
    # CONTEXT.md, "Perfil de insolvência confirmada", pela decisão
    # completa. Nenhum dos 6 tickers-piloto está em recuperação judicial
    # hoje (pesquisado, não assumido — ver CONTEXT.md pelas fontes),
    # então o default `False` reflete dado verificado, não um "não
    # investiguei ainda" disfarçado.
    em_recuperacao_judicial: bool = False

    # Classe de ativo real do ticker — `Optional[ClasseAtivo]`, SEM
    # default seguro de propósito (diferente de `eh_estatal`/
    # `em_recuperacao_judicial` acima, cujo `False` reflete dado já
    # verificado pra todos os pilotos). Aqui `None` significa "não
    # classificado", e `perfis/classe_ativo.py` levanta erro explícito
    # nesse caso — nunca assume "compatível" (ação) por ausência de
    # dado, mesmo raciocínio de "ausência não é 'seguro'" já aplicado ao
    # portão de insolvência. NUNCA inferir isso do sufixo do ticker (ver
    # armadilha documentada em `perfis/classe_ativo.py`: `TAEE11` é uma
    # unit de uma empresa real, TAESA — não um fundo, apesar do sufixo
    # "11" que FIAGROs/FIIs também usam).
    classe_ativo: Optional[ClasseAtivo] = None

    # Referências numéricas — todas opcionais: None = "sem override, usa
    # o fallback genérico" de quem consumir isso depois (Fase 2+), nunca
    # um número inventado aqui.
    beta_referencia: Optional[CampoComProveniencia] = None
    ev_ebitda_medio_referencia: Optional[CampoComProveniencia] = None
    psr_medio_referencia: Optional[CampoComProveniencia] = None
    fator_conversao_nopat_referencia: Optional[CampoComProveniencia] = None
    pct_divida_moeda_estrangeira: Optional[CampoComProveniencia] = None
    cap_crescimento_ciclico: Optional[CampoComProveniencia] = None

    # Métrica PRÓPRIA do ticker (não uma referência de fallback setorial
    # como os campos acima — por isso sem o sufixo "_referencia"). Volume
    # financeiro médio diário negociado (R$), sinal de liquidez de
    # mercado. Decisão de design (ver CONTEXT.md, investigação "liquidez:
    # campo vs. tag"): fica aqui, não como TagPerfilEconomico, porque é
    # uma condição de MERCADO que muda com o tempo sem nenhuma mudança na
    # empresa — precisa do mecanismo de staleness que só
    # CampoComProveniencia tem (`esta_desatualizado`, reaproveitado, não
    # duplicado). Opcional: None = liquidez ainda não investigada pra
    # esse ticker, nunca um número inventado.
    volume_medio_diario: Optional[CampoComProveniencia] = None

    # Inputs de DDM (Gordon Growth, valuation/ddm.py::calcular_ddm) —
    # ambos pendentes desde a sessão que implementou a função pura (ver
    # CONTEXT.md, "DDM (Gordon Growth)", seção "Pendente pra quando TAEE3
    # for populado"). Nome `dividendo_projetado` escolhido (não
    # `dpa_projetado`, que era a alternativa em aberto) por consistência
    # direta com o parâmetro de mesmo nome em `calcular_ddm()` — o valor
    # flui de um pro outro sem tradução de nome no meio do caminho.
    dividendo_projetado: Optional[CampoComProveniencia] = None
    taxa_crescimento_perpetuidade_ddm: Optional[CampoComProveniencia] = None

    # Input de CAPM (capm/capm.py::calcular_capm) — tamanho da empresa
    # (R$), usado pro size premium. Mesmo campo que uma cascata de
    # tamanho/liquidez futura reaproveitaria (não duplicar).
    valor_mercado: Optional[CampoComProveniencia] = None

    notas: Optional[str] = None

    def __post_init__(self) -> None:
        self.ticker = self.ticker.upper().strip()
        if not self.ticker:
            raise ValueError("PerfilSetor exige um ticker não-vazio.")
        if not self.setor or not self.setor.strip():
            raise ValueError(
                f"PerfilSetor de '{self.ticker}' exige um setor não-vazio "
                "— ticker sem setor não é um perfil válido."
            )
