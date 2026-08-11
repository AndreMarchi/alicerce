from datetime import date, timedelta

import pytest

from alicerce.proveniencia.schema import (
    CASCATA_FONTES,
    CampoComProveniencia,
    RegistroAuditoria,
)


def test_campo_com_fonte_automatica_nao_exige_motivo_override():
    campo = CampoComProveniencia(
        valor=12.5,
        fonte="brapi",
        confianca="alta",
        data_atualizacao=date.today(),
    )
    assert campo.motivo_override is None


def test_campo_manual_sem_motivo_override_levanta_erro():
    with pytest.raises(ValueError):
        CampoComProveniencia(
            valor=12.5,
            fonte="manual",
            confianca="alta",
            data_atualizacao=date.today(),
        )


def test_campo_manual_com_motivo_override_e_valido():
    campo = CampoComProveniencia(
        valor=12.5,
        fonte="manual",
        confianca="baixa",
        data_atualizacao=date.today(),
        motivo_override="Fonte automática divergia >30% do relatório trimestral.",
    )
    assert campo.motivo_override is not None


def test_esta_desatualizado_true_acima_de_180_dias():
    campo = CampoComProveniencia(
        valor=1.0,
        fonte="cvm",
        confianca="media",
        data_atualizacao=date.today() - timedelta(days=181),
    )
    assert campo.esta_desatualizado is True


def test_esta_desatualizado_false_dentro_de_180_dias():
    campo = CampoComProveniencia(
        valor=1.0,
        fonte="cvm",
        confianca="media",
        data_atualizacao=date.today() - timedelta(days=30),
    )
    assert campo.esta_desatualizado is False


def test_cascata_fontes_termina_em_manual():
    assert CASCATA_FONTES[-1] == "manual"
    assert len(set(CASCATA_FONTES)) == len(CASCATA_FONTES)


def test_registro_auditoria_construcao_basica():
    registro = RegistroAuditoria(
        ticker="TAEE3",
        campo="receita_liquida",
        fonte_usada="fundamentus",
    )
    assert registro.campos_em_override_manual == 0
