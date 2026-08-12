import pytest

from alicerce.sanity.divergencia import classificar_divergencia


def test_dentro_da_faixa():
    # valor_calculado 100 vs preco_mercado 95 -> divergência ~5,26%,
    # abaixo dos dois limiares.
    resultado = classificar_divergencia(
        valor_calculado=100.0, preco_mercado=95.0, limiar_moderada=0.10, limiar_severa=0.20
    )
    assert resultado.classificacao == "dentro_da_faixa"
    assert resultado.percentual_divergencia == pytest.approx((100.0 - 95.0) / 95.0)


def test_divergencia_moderada():
    # 100 vs 80 -> divergência 25%, entre 0.10 e 0.20 -> moderada.
    # Ajusta limiares pra esse cenário cair claramente no meio.
    resultado = classificar_divergencia(
        valor_calculado=100.0, preco_mercado=80.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_moderada"
    assert resultado.percentual_divergencia == pytest.approx(0.25)


def test_divergencia_severa():
    # 100 vs 50 -> divergência 100%, bem acima de qualquer limiar razoável.
    resultado = classificar_divergencia(
        valor_calculado=100.0, preco_mercado=50.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_severa"
    assert resultado.percentual_divergencia == pytest.approx(1.0)


def test_divergencia_negativa_classificada_pela_magnitude():
    # valor_calculado ABAIXO do preço de mercado (ação "cara" pelo
    # modelo) -> percentual negativo, mas classificação usa magnitude.
    resultado = classificar_divergencia(
        valor_calculado=50.0, preco_mercado=100.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_severa"
    assert resultado.percentual_divergencia == pytest.approx(-0.5)


def test_borda_exatamente_no_limiar_moderada_nao_dispara():
    # divergência exatamente 10% == limiar_moderada -> ainda dentro da
    # faixa (precisa ultrapassar, não só atingir).
    resultado = classificar_divergencia(
        valor_calculado=110.0, preco_mercado=100.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "dentro_da_faixa"


def test_borda_um_pouco_acima_do_limiar_moderada_dispara():
    resultado = classificar_divergencia(
        valor_calculado=110.01, preco_mercado=100.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_moderada"


def test_borda_exatamente_no_limiar_severa_nao_dispara_severa():
    resultado = classificar_divergencia(
        valor_calculado=130.0, preco_mercado=100.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_moderada"


def test_borda_um_pouco_acima_do_limiar_severa_dispara():
    resultado = classificar_divergencia(
        valor_calculado=130.01, preco_mercado=100.0, limiar_moderada=0.10, limiar_severa=0.30
    )
    assert resultado.classificacao == "divergencia_severa"


def test_preco_mercado_zero_levanta_erro():
    with pytest.raises(ValueError, match="preco_mercado"):
        classificar_divergencia(valor_calculado=100.0, preco_mercado=0.0, limiar_moderada=0.10, limiar_severa=0.30)


def test_preco_mercado_negativo_levanta_erro():
    with pytest.raises(ValueError, match="preco_mercado"):
        classificar_divergencia(valor_calculado=100.0, preco_mercado=-10.0, limiar_moderada=0.10, limiar_severa=0.30)


def test_limiares_sao_obrigatorios_sem_default():
    # Trava a decisão desta sessão: nenhum limiar tem valor default —
    # chamar sem eles precisa falhar, não usar uma constante escondida.
    with pytest.raises(TypeError):
        classificar_divergencia(valor_calculado=100.0, preco_mercado=95.0)  # type: ignore[call-arg]
