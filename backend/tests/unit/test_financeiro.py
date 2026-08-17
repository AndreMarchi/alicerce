from datetime import date

import pytest

from alicerce.perfis.financeiro import ticker_e_perfil_financeiro
from alicerce.perfis.motor import TickerSemPerfilError
from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.pipeline.ddm_only import StatusValuationDDMOnly, calcular_valor_ddm_only
from alicerce.proveniencia.schema import CampoComProveniencia

SELIC_2026_08_05 = 0.14


@pytest.mark.parametrize(
    "ticker,esperado",
    [
        ("TAEE3", False),
        ("CPLE3", False),
        ("GEPA4", False),
        ("ITSA4", True),  # holding financeira
        ("BEEF3", False),
        ("WIZC3", True),  # corretora de seguros, caso real de referência
    ],
)
def test_tickers_piloto_reais_classificados_corretamente(ticker, esperado):
    assert ticker_e_perfil_financeiro(ticker) is esperado


def test_ticker_desconhecido_levanta_erro_explicito():
    with pytest.raises(TickerSemPerfilError):
        ticker_e_perfil_financeiro("NAOEXISTE3")


def _campo(valor: float) -> CampoComProveniencia:
    return CampoComProveniencia(
        valor=valor, fonte="manual", confianca="media", data_atualizacao=date.today(), motivo_override="teste"
    )


def test_ddm_nao_e_bloqueado_por_perfil_financeiro(monkeypatch):
    # DECISÃO (a) desta tarefa (ver CONTEXT.md, "Perfil
    # financeiro/seguradora"): perfil financeiro/seguradora NÃO bloqueia
    # DDM — só DCF/EV-EBITDA/Graham (nenhum implementado no Alicerce
    # ainda) causavam o problema real no WIZC3. Este teste confirma isso
    # de forma EXECUTÁVEL, não só em comentário: um ticker sintético com
    # taxonomia_financeira_especial=True E tag DDM_ONLY calcula
    # normalmente via calcular_valor_ddm_only(), sem nenhum bloqueio.
    import alicerce.pipeline.ddm_only as modulo_pipeline

    perfil_financeiro_com_ddm_only = PerfilSetor(
        ticker="FICT3",
        setor="Previdência e Seguros",
        taxonomia_financeira_especial=True,
        beta_referencia=_campo(0.85),
        valor_mercado=_campo(1_000_000_000.0),
        dividendo_projetado=_campo(1.0),
        taxa_crescimento_perpetuidade_ddm=_campo(0.03),
    )
    monkeypatch.setattr(
        modulo_pipeline, "obter_tags", lambda ticker: frozenset({modulo_pipeline.TagPerfilEconomico.DDM_ONLY})
    )
    monkeypatch.setattr(modulo_pipeline, "obter_perfil", lambda ticker: perfil_financeiro_com_ddm_only)

    resultado = calcular_valor_ddm_only("FICT3", rf=SELIC_2026_08_05)

    assert resultado.status == StatusValuationDDMOnly.CALCULADO
    assert resultado.metodo == "DDM"
    assert resultado.valor_calculado is not None
