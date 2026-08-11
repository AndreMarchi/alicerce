import pytest

from alicerce.perfis.motor import TickerSemPerfilError, obter_atribuicoes_tags, obter_perfil, obter_tags
from alicerce.perfis.tags import TagPerfilEconomico


def test_ticker_desconhecido_levanta_erro_explicito():
    with pytest.raises(TickerSemPerfilError):
        obter_perfil("NAOEXISTE3")


def test_obter_tags_de_ticker_desconhecido_tambem_levanta_erro():
    with pytest.raises(TickerSemPerfilError):
        obter_tags("NAOEXISTE3")


@pytest.mark.parametrize(
    "ticker,setor_esperado",
    [
        ("TAEE3", "Energia Elétrica"),
        ("CPLE3", "Energia Elétrica"),
        ("GEPA4", "Energia Elétrica"),
        ("ITSA4", "Holding"),
        ("BEEF3", "Alimentos"),
        ("WIZC3", "Previdência e Seguros"),
    ],
)
def test_obter_perfil_dos_tickers_piloto(ticker, setor_esperado):
    perfil = obter_perfil(ticker)
    assert perfil.ticker == ticker
    assert perfil.setor == setor_esperado


@pytest.mark.parametrize(
    "ticker,tags_esperadas",
    [
        ("TAEE3", {TagPerfilEconomico.DDM_ONLY}),
        ("CPLE3", {TagPerfilEconomico.CONCESSAO, TagPerfilEconomico.ESTATAL_CONTROLADA}),
        ("GEPA4", {TagPerfilEconomico.CONCESSAO}),
        ("ITSA4", {TagPerfilEconomico.SOTP_OBRIGATORIO}),
        ("BEEF3", {TagPerfilEconomico.ALAVANCAGEM_USD}),
        ("WIZC3", set()),
    ],
)
def test_obter_tags_dos_tickers_piloto(ticker, tags_esperadas):
    assert obter_tags(ticker) == frozenset(tags_esperadas)


def test_wizc3_tem_perfil_completo_mas_zero_tags_sem_erro():
    # Caso deliberado (ver CONTEXT.md, Fase 1): ticker CADASTRADO sem
    # nenhuma tag especial não é erro, é frozenset() válido.
    perfil = obter_perfil("WIZC3")
    assert perfil.taxonomia_financeira_especial is True
    assert obter_tags("WIZC3") == frozenset()
    assert obter_atribuicoes_tags("WIZC3") == ()


def test_herda_referencias_do_setor_base_energia_eletrica():
    # TAEE3/CPLE3/GEPA4 não repetem beta/ev-ebitda/fator-nopat no JSON —
    # devem vir do perfil-base "Energia Elétrica" via merge (ver
    # CONTEXT.md, "Herança de setor").
    for ticker in ("TAEE3", "CPLE3", "GEPA4"):
        perfil = obter_perfil(ticker)
        assert perfil.eh_regulado is True
        assert perfil.beta_referencia is not None
        assert perfil.beta_referencia.valor == 0.65
        assert perfil.ev_ebitda_medio_referencia.valor == 7.0
        assert perfil.fator_conversao_nopat_referencia.valor == 0.60


def test_campo_especifico_do_ticker_sobrescreve_o_do_setor_base():
    # TAEE3 tem pct_divida_moeda_estrangeira PRÓPRIO (0.0) — não vem do
    # setor base (que nem define esse campo).
    taee3 = obter_perfil("TAEE3")
    assert taee3.pct_divida_moeda_estrangeira.valor == 0.0

    beef3 = obter_perfil("BEEF3")
    assert beef3.pct_divida_moeda_estrangeira.valor == 0.90


def test_atribuicoes_tags_expoe_justificativa_para_auditoria():
    atribuicoes = obter_atribuicoes_tags("CPLE3")
    tags = {atribuicao.tag for atribuicao in atribuicoes}
    assert tags == {TagPerfilEconomico.CONCESSAO, TagPerfilEconomico.ESTATAL_CONTROLADA}
    assert all(atribuicao.justificativa.strip() for atribuicao in atribuicoes)
