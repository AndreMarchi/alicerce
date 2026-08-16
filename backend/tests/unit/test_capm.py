import pytest

from alicerce.capm.capm import (
    BETA_MAXIMO_PLAUSIVEL,
    BETA_MINIMO_PLAUSIVEL,
    TAXA_DESCONTO_MAXIMA,
    TAXA_DESCONTO_MINIMA,
    calcular_capm,
)


def test_caso_normal_dentro_da_faixa():
    # rf=10%, beta=0.5, large cap (size_premium=0%), não estatal.
    # ke = 0.10 + 0.5*0.055 + 0.025 + 0.00 + 0 = 0.1525
    ke = calcular_capm(rf=0.10, beta=0.5, valor_mercado=60_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(0.1525)


def test_estouraria_acima_do_teto_sem_clamp_fica_no_teto():
    # rf=14.5%, beta=1.5, micro cap (size_premium=3.5%), estatal (+2pp).
    # ke bruto = 0.145 + 1.5*0.055 + 0.025 + 0.035 + 0.02 = 0.3075 (30.75%)
    # bem acima de 16% -> clampado exatamente no teto.
    ke = calcular_capm(rf=0.145, beta=1.5, valor_mercado=1_000_000_000, eh_estatal=True)
    assert ke == pytest.approx(TAXA_DESCONTO_MAXIMA)
    assert ke == pytest.approx(0.16)


def test_ficaria_abaixo_do_piso_sem_clamp_fica_no_piso():
    # rf=2%, beta NEGATIVO (-0.5, permitido de propósito, ver docstring),
    # large cap (size_premium=0%), não estatal.
    # ke bruto = 0.02 + (-0.5*0.055) + 0.025 + 0 + 0 = 0.0175 (1.75%)
    # bem abaixo de 10% -> clampado exatamente no piso.
    ke = calcular_capm(rf=0.02, beta=-0.5, valor_mercado=100_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(TAXA_DESCONTO_MINIMA)
    assert ke == pytest.approx(0.10)


def test_eh_estatal_soma_exatamente_2pp_quando_ambos_ficam_sem_clamp():
    comuns = dict(rf=0.08, beta=0.3, valor_mercado=60_000_000_000)
    ke_nao_estatal = calcular_capm(**comuns, eh_estatal=False)
    ke_estatal = calcular_capm(**comuns, eh_estatal=True)
    assert ke_nao_estatal == pytest.approx(0.1215)
    assert ke_estatal == pytest.approx(0.1415)
    assert ke_estatal - ke_nao_estatal == pytest.approx(0.02)


def test_borda_exatamente_no_teto():
    # rf=9.75%, beta=0.5, mid cap >10bi (size_premium=1%), não estatal.
    # ke = 0.0975 + 0.5*0.055 + 0.025 + 0.01 + 0 = 0.16 exato.
    ke = calcular_capm(rf=0.0975, beta=0.5, valor_mercado=15_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(0.16)


def test_borda_exatamente_no_piso():
    # rf=5.5%, beta=0.0, small cap >2bi (size_premium=2%), não estatal.
    # ke = 0.055 + 0 + 0.025 + 0.02 + 0 = 0.10 exato.
    ke = calcular_capm(rf=0.055, beta=0.0, valor_mercado=3_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(0.10)


def test_valor_mercado_nao_positivo_usa_tier_fallback_de_1_5_por_cento():
    # Mesmo comportamento do valuation-tracker (fallback, não bug):
    # valor_mercado <= 0 -> size_premium = 1,5%.
    # ke = 0.08 + 0.2*0.055 + 0.025 + 0.015 + 0 = 0.131
    ke = calcular_capm(rf=0.08, beta=0.2, valor_mercado=0.0, eh_estatal=False)
    assert ke == pytest.approx(0.131)


def test_beta_abaixo_do_piso_plausivel_levanta_erro():
    with pytest.raises(ValueError, match="beta"):
        calcular_capm(rf=0.10, beta=-3.5, valor_mercado=60_000_000_000, eh_estatal=False)


def test_beta_acima_do_teto_plausivel_levanta_erro():
    with pytest.raises(ValueError, match="beta"):
        calcular_capm(rf=0.10, beta=6.0, valor_mercado=60_000_000_000, eh_estatal=False)


def test_beta_exatamente_na_borda_nao_levanta_erro():
    # Borda inclusiva: -3 e 5 exatos são aceitos, só além disso trava.
    assert calcular_capm(rf=0.10, beta=BETA_MINIMO_PLAUSIVEL, valor_mercado=60_000_000_000, eh_estatal=False)
    assert calcular_capm(rf=0.10, beta=BETA_MAXIMO_PLAUSIVEL, valor_mercado=60_000_000_000, eh_estatal=False)


def test_rf_negativo_levanta_erro():
    with pytest.raises(ValueError, match="rf"):
        calcular_capm(rf=-0.01, beta=0.5, valor_mercado=60_000_000_000, eh_estatal=False)


def test_rf_zero_nao_levanta_erro():
    # Zero é diferente de negativo — só valor negativo é bloqueado.
    ke = calcular_capm(rf=0.0, beta=0.5, valor_mercado=60_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(TAXA_DESCONTO_MINIMA)  # 0 + 0.0275 + 0.025 + 0 = 0.0525 -> clamp no piso


def test_caso_normal_ainda_funciona_sem_regressao_apos_as_travas():
    # Mesmo caso de test_caso_normal_dentro_da_faixa, repetido aqui pra
    # travar explicitamente que a trava nova não alterou o comportamento
    # de clamp pra valores plausíveis (não é uma regressão silenciosa).
    ke = calcular_capm(rf=0.10, beta=0.5, valor_mercado=60_000_000_000, eh_estatal=False)
    assert ke == pytest.approx(0.1525)
