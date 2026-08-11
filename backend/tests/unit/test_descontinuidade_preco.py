from datetime import date

import pytest

from alicerce.proveniencia.descontinuidade_preco import (
    RAZAO_MAX_MIN_52W_SUSPEITA,
    aplicar_deteccao_descontinuidade,
    eh_descontinuidade_suspeita,
    razao_max_min_52_semanas,
)
from alicerce.proveniencia.schema import CampoComProveniencia


def _campo_preco(fonte="fundamentus", confianca="alta", motivo_override=None) -> CampoComProveniencia:
    return CampoComProveniencia(
        valor=12.34,
        fonte=fonte,
        confianca=confianca,
        data_atualizacao=date(2026, 7, 22),
        motivo_override=motivo_override,
    )


def test_razao_max_min_52_semanas_calculo_basico():
    assert razao_max_min_52_semanas(maxima_52_semanas=20.0, minima_52_semanas=10.0) == 2.0


def test_razao_max_min_52_semanas_minima_zero_levanta_erro():
    with pytest.raises(ValueError):
        razao_max_min_52_semanas(maxima_52_semanas=10.0, minima_52_semanas=0.0)


def test_razao_max_min_52_semanas_minima_negativa_levanta_erro():
    with pytest.raises(ValueError):
        razao_max_min_52_semanas(maxima_52_semanas=10.0, minima_52_semanas=-1.0)


def test_caso_limpo_sem_anomalia_nao_e_suspeito():
    # Ticker líquido, comum: preço oscilou de R$8 a R$12 em 52 semanas (1.5x).
    assert eh_descontinuidade_suspeita(maxima_52_semanas=12.0, minima_52_semanas=8.0) is False


def test_caso_limpo_campo_nao_e_alterado():
    campo_original = _campo_preco(confianca="alta")
    resultado = aplicar_deteccao_descontinuidade(
        campo_original, maxima_52_semanas=12.0, minima_52_semanas=8.0
    )
    assert resultado is campo_original
    assert resultado.confianca == "alta"
    assert resultado.motivo_override is None


def test_caso_rvee3_like_e_suspeito():
    # RVEE3 real: R$0,68 a R$31,00 em 52 semanas — razão ~45,59x.
    assert eh_descontinuidade_suspeita(maxima_52_semanas=31.00, minima_52_semanas=0.68) is True


def test_caso_rvee3_like_forca_confianca_baixa_e_preenche_motivo():
    campo_original = _campo_preco(fonte="fundamentus", confianca="alta")
    resultado = aplicar_deteccao_descontinuidade(
        campo_original, maxima_52_semanas=31.00, minima_52_semanas=0.68
    )
    assert resultado.confianca == "baixa"
    assert resultado.motivo_override is not None
    assert "45." in resultado.motivo_override  # razão ~45,59x aparece na mensagem
    assert "grupamento" in resultado.motivo_override.lower()
    # Valor e fonte originais preservados — dado nunca é descartado.
    assert resultado.valor == campo_original.valor
    assert resultado.fonte == campo_original.fonte


def test_caso_borda_exatamente_no_limiar_nao_e_suspeito():
    minima = 10.0
    maxima = minima * RAZAO_MAX_MIN_52W_SUSPEITA  # razão == limiar, exatamente
    assert eh_descontinuidade_suspeita(maxima_52_semanas=maxima, minima_52_semanas=minima) is False

    campo_original = _campo_preco(confianca="alta")
    resultado = aplicar_deteccao_descontinuidade(campo_original, maxima_52_semanas=maxima, minima_52_semanas=minima)
    assert resultado is campo_original
    assert resultado.confianca == "alta"


def test_caso_borda_um_centavo_acima_do_limiar_e_suspeito():
    minima = 10.0
    maxima = minima * RAZAO_MAX_MIN_52W_SUSPEITA + 0.01
    assert eh_descontinuidade_suspeita(maxima_52_semanas=maxima, minima_52_semanas=minima) is True

    campo_original = _campo_preco(confianca="alta")
    resultado = aplicar_deteccao_descontinuidade(campo_original, maxima_52_semanas=maxima, minima_52_semanas=minima)
    assert resultado.confianca == "baixa"
    assert resultado.motivo_override is not None


def test_campo_ja_manual_com_motivo_override_e_sobrescrito_quando_suspeito():
    # fonte=="manual" já exige motivo_override desde a construção (Fase 0) —
    # confirma que a detecção SOBRESCREVE esse motivo, não conflita com ele.
    campo_original = _campo_preco(
        fonte="manual", confianca="media", motivo_override="Override manual anterior, sem relação com preço."
    )
    resultado = aplicar_deteccao_descontinuidade(
        campo_original, maxima_52_semanas=31.00, minima_52_semanas=0.68
    )
    assert resultado.confianca == "baixa"
    assert "Descontinuidade suspeita" in resultado.motivo_override
    assert resultado.fonte == "manual"


def test_limiar_customizado_e_respeitado():
    # Com limiar mais permissivo (50x), a razão do RVEE3 (~45,59x) deixa de ser suspeita.
    assert eh_descontinuidade_suspeita(maxima_52_semanas=31.00, minima_52_semanas=0.68, limiar=50.0) is False
