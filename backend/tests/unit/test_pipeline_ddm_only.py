from datetime import date

import pytest

from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.pipeline.ddm_only import (
    CampoObrigatorioAusenteError,
    ResultadoValuationDDMOnly,
    StatusValuationDDMOnly,
    _validar_campos_obrigatorios_ddm_only,
    calcular_valor_ddm_only,
)
from alicerce.proveniencia.schema import CampoComProveniencia

# Selic da 280ª reunião do Copom (05/08/2026) — mesmo valor pontual já
# usado em tests/integration/test_taee3_ddm_capm_e2e.py.
SELIC_2026_08_05 = 0.14


def test_taee3_via_roteamento_bate_exatamente_com_o_teste_de_integracao_manual():
    # Mesmo cenário e mesmos números já validados manualmente em
    # test_taee3_ddm_capm_e2e.py (commit 3b7fdf7): Ke=16% (clampado),
    # valor calculado R$7,92. Este teste confirma que o roteamento
    # automático não introduz NENHUMA diferença de comportamento.
    resultado = calcular_valor_ddm_only("TAEE3", rf=SELIC_2026_08_05)

    assert resultado.status == StatusValuationDDMOnly.CALCULADO
    assert resultado.metodo == "DDM"
    assert resultado.ke == pytest.approx(0.16)
    assert resultado.valor_calculado == pytest.approx(7.92)


def test_ticker_sem_tag_ddm_only_retorna_sinal_explicito_sem_metodo_aplicavel():
    # CPLE3 é um dos 6 tickers-piloto, mas não tem a tag DDM_ONLY (tem
    # concessao + estatal_controlada) — deve sinalizar explicitamente,
    # não None nem erro.
    resultado = calcular_valor_ddm_only("CPLE3", rf=SELIC_2026_08_05)

    assert resultado == ResultadoValuationDDMOnly(
        ticker="CPLE3", status=StatusValuationDDMOnly.SEM_METODO_APLICAVEL
    )
    assert resultado.metodo is None
    assert resultado.valor_calculado is None
    assert resultado.ke is None


def test_ticker_desconhecido_propaga_erro_do_motor_de_perfis():
    from alicerce.perfis.motor import TickerSemPerfilError

    with pytest.raises(TickerSemPerfilError):
        calcular_valor_ddm_only("NAOEXISTE3", rf=SELIC_2026_08_05)


def _campo(valor: float) -> CampoComProveniencia:
    return CampoComProveniencia(
        valor=valor, fonte="manual", confianca="media", data_atualizacao=date.today(), motivo_override="teste"
    )


def test_validacao_de_campos_obrigatorios_passa_com_perfil_completo():
    perfil = PerfilSetor(
        ticker="FICT3",
        setor="Energia Elétrica",
        beta_referencia=_campo(0.9),
        valor_mercado=_campo(1_000_000.0),
        dividendo_projetado=_campo(1.0),
        taxa_crescimento_perpetuidade_ddm=_campo(0.03),
    )
    _validar_campos_obrigatorios_ddm_only(perfil)  # não levanta


def test_validacao_de_campos_obrigatorios_levanta_erro_com_campo_ausente():
    # dividendo_projetado e taxa_crescimento_perpetuidade_ddm ausentes
    # de propósito — não é possível reproduzir isso com um dos 6
    # tickers-piloto reais (TAEE3, o único DDM_ONLY, já está com todos
    # os campos populados), então testado direto contra um PerfilSetor
    # construído à mão.
    perfil = PerfilSetor(
        ticker="FICT3",
        setor="Energia Elétrica",
        beta_referencia=_campo(0.9),
        valor_mercado=_campo(1_000_000.0),
    )
    with pytest.raises(CampoObrigatorioAusenteError, match="dividendo_projetado"):
        _validar_campos_obrigatorios_ddm_only(perfil)


def test_calcular_valor_ddm_only_propaga_erro_de_campo_ausente(monkeypatch):
    # Simula um ticker com tag DDM_ONLY mas PerfilSetor incompleto,
    # substituindo obter_perfil só pra este teste — sem tocar no JSON
    # real de dados (TAEE3, único DDM_ONLY real, está completo).
    import alicerce.pipeline.ddm_only as modulo

    perfil_incompleto = PerfilSetor(
        ticker="FICT3",
        setor="Energia Elétrica",
        beta_referencia=_campo(0.9),
        valor_mercado=_campo(1_000_000.0),
    )
    monkeypatch.setattr(modulo, "obter_tags", lambda ticker: frozenset({modulo.TagPerfilEconomico.DDM_ONLY}))
    monkeypatch.setattr(modulo, "obter_perfil", lambda ticker: perfil_incompleto)

    with pytest.raises(CampoObrigatorioAusenteError):
        calcular_valor_ddm_only("FICT3", rf=SELIC_2026_08_05)
