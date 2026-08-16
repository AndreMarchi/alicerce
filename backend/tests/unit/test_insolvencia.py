import pytest

from alicerce.perfis.insolvencia import ticker_bloqueado_por_insolvencia
from alicerce.perfis.motor import TickerSemPerfilError


def test_ticker_em_recuperacao_judicial_e_bloqueado(monkeypatch):
    # Nenhum dos 6 tickers-piloto reais está em recuperação judicial
    # hoje (pesquisado, ver CONTEXT.md) — cenário True testado via
    # monkeypatch de obter_perfil, sem inventar um ticker fictício no
    # JSON real nem mudar o cadastro de um ticker real só pro teste.
    import alicerce.perfis.insolvencia as modulo
    from alicerce.perfis.perfil_setor import PerfilSetor

    perfil_insolvente = PerfilSetor(
        ticker="FICT3", setor="Energia Elétrica", em_recuperacao_judicial=True
    )
    monkeypatch.setattr(modulo, "obter_perfil", lambda ticker: perfil_insolvente)

    assert ticker_bloqueado_por_insolvencia("FICT3") is True


@pytest.mark.parametrize("ticker", ["TAEE3", "CPLE3", "GEPA4", "ITSA4", "BEEF3", "WIZC3"])
def test_tickers_piloto_reais_nao_estao_bloqueados(ticker):
    # Todos os 6 tickers-piloto foram pesquisados (ver CONTEXT.md) e
    # nenhum está em recuperação judicial hoje — dado real, não default
    # não-investigado.
    assert ticker_bloqueado_por_insolvencia(ticker) is False


def test_campo_ausente_usa_default_false_nao_bloqueado():
    # PerfilSetor sem em_recuperacao_judicial explícito usa o default
    # da dataclass (False) — comportamento do dataclass, não uma
    # inferência especial deste módulo.
    from alicerce.perfis.perfil_setor import PerfilSetor

    perfil = PerfilSetor(ticker="FICT4", setor="Energia Elétrica")
    assert perfil.em_recuperacao_judicial is False


def test_ticker_desconhecido_levanta_erro_explicito_nao_retorna_false_silencioso():
    # TickerSemPerfilError, não False — ausência de cadastro é um caso
    # diferente de "confirmado seguro" (mesmo princípio de erro
    # explícito já usado em perfis/motor.py).
    with pytest.raises(TickerSemPerfilError):
        ticker_bloqueado_por_insolvencia("NAOEXISTE3")
