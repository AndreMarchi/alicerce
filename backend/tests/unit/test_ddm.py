import pytest

from alicerce.valuation.ddm import calcular_ddm


def test_caso_normal_taee3_like():
    # Números SINTÉTICOS plausíveis, não dados reais — CONTEXT.md do
    # Alicerce não tem os inputs de DDM do TAEE3 registrados (só a
    # justificativa da tag, sem os números). Ordem de grandeza
    # consistente com a faixa de preço real do TAEE3 (Fundamentus,
    # ~R$10-14, ver CONTEXT.md "Calibração do limiar"): dividendo
    # projetado R$1,10/ação, Ke 12%, g 3% -> valor ~R$12,22.
    valor = calcular_ddm(dividendo_projetado=1.10, ke=0.12, g=0.03)
    assert valor == pytest.approx(1.10 / 0.09)
    assert valor == pytest.approx(12.222222, rel=1e-5)


def test_ke_igual_a_g_levanta_erro():
    with pytest.raises(ValueError, match="ke.*maior que g"):
        calcular_ddm(dividendo_projetado=1.10, ke=0.05, g=0.05)


def test_ke_menor_que_g_levanta_erro():
    with pytest.raises(ValueError, match="ke.*maior que g"):
        calcular_ddm(dividendo_projetado=1.10, ke=0.03, g=0.05)


def test_dividendo_projetado_zero_levanta_erro():
    with pytest.raises(ValueError, match="dividendo_projetado"):
        calcular_ddm(dividendo_projetado=0.0, ke=0.12, g=0.03)


def test_dividendo_projetado_negativo_levanta_erro():
    with pytest.raises(ValueError, match="dividendo_projetado"):
        calcular_ddm(dividendo_projetado=-1.0, ke=0.12, g=0.03)


def test_ke_zero_levanta_erro():
    with pytest.raises(ValueError, match="ke precisa ser > 0"):
        calcular_ddm(dividendo_projetado=1.10, ke=0.0, g=-0.01)


def test_ke_negativo_levanta_erro():
    with pytest.raises(ValueError, match="ke precisa ser > 0"):
        calcular_ddm(dividendo_projetado=1.10, ke=-0.02, g=-0.05)


def test_g_negativo_e_permitido_caso_de_borda():
    # Decisão de design documentada em ddm.py: g negativo é
    # matematicamente válido (cenário de declínio de dividendo) e não é
    # travado por precaução — só ke > g importa.
    valor = calcular_ddm(dividendo_projetado=1.0, ke=0.10, g=-0.05)
    assert valor == pytest.approx(1.0 / 0.15)
    assert valor == pytest.approx(6.666667, rel=1e-5)
