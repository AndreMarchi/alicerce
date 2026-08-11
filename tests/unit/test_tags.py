import dataclasses

import pytest

from alicerce.perfis.tags import AtribuicaoTag, TagPerfilEconomico


def test_tags_conhecidas_tem_valores_unicos():
    valores = [tag.value for tag in TagPerfilEconomico]
    assert len(valores) == len(set(valores))
    assert set(valores) == {
        "ddm_only",
        "concessao",
        "estatal_controlada",
        "sotp_obrigatorio",
        "alavancagem_usd",
    }


def test_atribuicao_tag_guarda_tag_e_justificativa():
    atribuicao = AtribuicaoTag(
        tag=TagPerfilEconomico.CONCESSAO,
        justificativa="Concessão regulada, ver CONTEXT.md.",
    )
    assert atribuicao.tag is TagPerfilEconomico.CONCESSAO
    assert "Concessão" in atribuicao.justificativa


def test_atribuicao_tag_e_imutavel():
    atribuicao = AtribuicaoTag(tag=TagPerfilEconomico.DDM_ONLY, justificativa="teste")
    with pytest.raises(dataclasses.FrozenInstanceError):
        atribuicao.justificativa = "outra coisa"


def test_atribuicao_tag_sem_justificativa_levanta_erro():
    with pytest.raises(ValueError):
        AtribuicaoTag(tag=TagPerfilEconomico.SOTP_OBRIGATORIO, justificativa="   ")


def test_ticker_pode_ter_multiplas_tags_compostas():
    atribuicoes = frozenset(
        {
            AtribuicaoTag(tag=TagPerfilEconomico.CONCESSAO, justificativa="a"),
            AtribuicaoTag(tag=TagPerfilEconomico.ESTATAL_CONTROLADA, justificativa="b"),
        }
    )
    tags = frozenset(atribuicao.tag for atribuicao in atribuicoes)
    assert tags == {TagPerfilEconomico.CONCESSAO, TagPerfilEconomico.ESTATAL_CONTROLADA}
