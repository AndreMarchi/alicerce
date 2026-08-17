import pytest

from alicerce.perfis.classe_ativo import (
    ClasseAtivoNaoClassificadaError,
    ticker_bloqueado_por_classe_ativo_incompativel,
)
from alicerce.perfis.motor import TickerSemPerfilError
from alicerce.perfis.perfil_setor import PerfilSetor


def _com_perfil(monkeypatch, perfil: PerfilSetor):
    import alicerce.perfis.classe_ativo as modulo

    monkeypatch.setattr(modulo, "obter_perfil", lambda ticker: perfil)


def test_ticker_fiagro_e_bloqueado(monkeypatch):
    # RZAG11 (FIAGRO), caso real de referência do ROADMAP — testado via
    # PerfilSetor construído à mão (RZAG11 não é um dos 6 pilotos do
    # Alicerce, só o caso que motiva o perfil).
    perfil = PerfilSetor(ticker="RZAG11", setor="Fundo Imobiliário", classe_ativo="fiagro")
    _com_perfil(monkeypatch, perfil)

    assert ticker_bloqueado_por_classe_ativo_incompativel("RZAG11") is True


def test_ticker_fii_e_bloqueado(monkeypatch):
    perfil = PerfilSetor(ticker="FICT11", setor="Fundo Imobiliário", classe_ativo="fii")
    _com_perfil(monkeypatch, perfil)

    assert ticker_bloqueado_por_classe_ativo_incompativel("FICT11") is True


def test_armadilha_taee11_unit_nao_e_bloqueada(monkeypatch):
    # ARMADILHA REAL (ver docstring de classe_ativo.py): TAEE11 é a unit
    # da TAESA (bundle TAEE3+TAEE4), termina em "11" como um FIAGRO/FII,
    # mas é uma empresa real, não um fundo. Se a detecção fosse por
    # sufixo de ticker (o que este módulo delibaradamente NÃO faz),
    # TAEE11 seria classificado incorretamente como fundo. TAEE11 não
    # está cadastrado no Alicerce hoje (só TAEE3, a ação ON, é um dos 6
    # pilotos) — testado via PerfilSetor construído à mão, classe_ativo
    # explícito "unit".
    perfil = PerfilSetor(ticker="TAEE11", setor="Energia Elétrica", classe_ativo="unit")
    _com_perfil(monkeypatch, perfil)

    assert ticker_bloqueado_por_classe_ativo_incompativel("TAEE11") is False


@pytest.mark.parametrize("ticker", ["TAEE3", "CPLE3", "GEPA4", "ITSA4", "BEEF3", "WIZC3"])
def test_tickers_piloto_reais_nao_estao_bloqueados(ticker):
    # Todos os 6 tickers-piloto têm classe_ativo="acao" (confirmado, ver
    # CONTEXT.md) — nenhum é fundo.
    assert ticker_bloqueado_por_classe_ativo_incompativel(ticker) is False


def test_classe_ativo_ausente_levanta_erro_explicito_nao_assume_compativel(monkeypatch):
    perfil = PerfilSetor(ticker="FICT3", setor="Energia Elétrica")
    assert perfil.classe_ativo is None
    _com_perfil(monkeypatch, perfil)

    with pytest.raises(ClasseAtivoNaoClassificadaError):
        ticker_bloqueado_por_classe_ativo_incompativel("FICT3")


def test_ticker_desconhecido_levanta_erro_explicito():
    with pytest.raises(TickerSemPerfilError):
        ticker_bloqueado_por_classe_ativo_incompativel("NAOEXISTE3")
