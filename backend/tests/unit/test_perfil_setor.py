from datetime import date

import pytest

from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.proveniencia.schema import CampoComProveniencia


def test_construcao_minima_valida():
    perfil = PerfilSetor(ticker="taee3", setor="Energia Elétrica")
    assert perfil.ticker == "TAEE3"
    assert perfil.setor == "Energia Elétrica"
    assert perfil.eh_regulado is False
    assert perfil.beta_referencia is None


def test_ticker_normalizado_para_upper_strip():
    perfil = PerfilSetor(ticker="  cple3 ", setor="Energia Elétrica")
    assert perfil.ticker == "CPLE3"


def test_ticker_vazio_levanta_erro():
    with pytest.raises(ValueError):
        PerfilSetor(ticker="   ", setor="Energia Elétrica")


def test_setor_vazio_levanta_erro():
    with pytest.raises(ValueError):
        PerfilSetor(ticker="ITSA4", setor="")


def test_campos_numericos_aceitam_campo_com_proveniencia():
    beta = CampoComProveniencia(
        valor=0.65,
        fonte="manual",
        confianca="media",
        data_atualizacao=date(2026, 7, 22),
        motivo_override="teste",
    )
    perfil = PerfilSetor(ticker="GEPA4", setor="Energia Elétrica", beta_referencia=beta)
    assert perfil.beta_referencia is beta
