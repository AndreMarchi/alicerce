from datetime import date, timedelta

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


def test_volume_medio_diario_aceita_proveniencia_completa():
    volume = CampoComProveniencia(
        valor=1_345_810.0,
        fonte="fundamentus",
        confianca="alta",
        data_atualizacao=date(2026, 8, 1),
    )
    perfil = PerfilSetor(ticker="TAEE3", setor="Energia Elétrica", volume_medio_diario=volume)
    assert perfil.volume_medio_diario is volume
    assert perfil.volume_medio_diario.valor == 1_345_810.0
    assert perfil.volume_medio_diario.fonte == "fundamentus"


def test_volume_medio_diario_e_opcional_perfil_continua_valido_sem_ele():
    # Nenhum dos 6 tickers-piloto tem esse dado ainda — precisa continuar
    # um PerfilSetor válido sem ele (não é campo obrigatório).
    perfil = PerfilSetor(ticker="WIZC3", setor="Previdência e Seguros")
    assert perfil.volume_medio_diario is None


def test_volume_medio_diario_reaproveita_esta_desatualizado_existente():
    # Reaproveitamento do mecanismo já existente em CampoComProveniencia
    # (schema.py) — não é uma reimplementação específica pra liquidez.
    volume_recente = CampoComProveniencia(
        valor=500_000.0,
        fonte="fundamentus",
        confianca="alta",
        data_atualizacao=date.today() - timedelta(days=10),
    )
    volume_velho = CampoComProveniencia(
        valor=500_000.0,
        fonte="fundamentus",
        confianca="alta",
        data_atualizacao=date.today() - timedelta(days=200),
    )
    perfil = PerfilSetor(ticker="BEEF3", setor="Alimentos", volume_medio_diario=volume_recente)
    assert perfil.volume_medio_diario.esta_desatualizado is False

    perfil_velho = PerfilSetor(ticker="BEEF3", setor="Alimentos", volume_medio_diario=volume_velho)
    assert perfil_velho.volume_medio_diario.esta_desatualizado is True
