import pytest

from alicerce.perfis.motor import TickerSemPerfilError
from alicerce.perfis.patrimonial import ticker_e_perfil_patrimonial
from alicerce.perfis.perfil_setor import PerfilSetor


@pytest.mark.parametrize("ticker", ["TAEE3", "CPLE3", "GEPA4", "ITSA4", "BEEF3", "WIZC3"])
def test_tickers_piloto_reais_nao_sao_patrimoniais(ticker):
    # Confirmado (não assumido) que nenhum dos 6 pilotos opera no setor
    # imobiliário/patrimonial — ver CONTEXT.md pela confirmação por
    # ticker.
    assert ticker_e_perfil_patrimonial(ticker) is False


def test_ticker_patrimonial_sintetico_e_classificado_corretamente(monkeypatch):
    # HBRE3 (HBR Realty, caso real de referência do ROADMAP) não é um
    # dos 6 pilotos do Alicerce — testado via PerfilSetor construído à
    # mão, mesmo padrão já usado nos perfis anteriores pra casos sem
    # dado real cadastrado.
    import alicerce.perfis.patrimonial as modulo

    perfil = PerfilSetor(ticker="HBRE3", setor="Exploração de Imóveis", perfil_patrimonial=True)
    monkeypatch.setattr(modulo, "obter_perfil", lambda ticker: perfil)

    assert ticker_e_perfil_patrimonial("HBRE3") is True


def test_ticker_desconhecido_levanta_erro_explicito():
    with pytest.raises(TickerSemPerfilError):
        ticker_e_perfil_patrimonial("NAOEXISTE3")
