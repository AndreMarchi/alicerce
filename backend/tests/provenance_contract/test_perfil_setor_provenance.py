"""
Contrato: todo campo NUMÉRICO de PerfilSetor (referência setorial ou
métrica própria do ticker, ex: volume_medio_diario) usa
CampoComProveniencia, nunca um float/int cru. Estrutural (via
typing.get_type_hints), não uma checagem campo-a-campo hardcoded — pega
alguém adicionando um campo numérico novo "por descuido" no futuro sem
passar pela Fase 0.
"""

import typing

import pytest

from alicerce.perfis.motor import obter_perfil
from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.proveniencia.schema import CampoComProveniencia

_TICKERS_PILOTO = ("TAEE3", "CPLE3", "GEPA4", "ITSA4", "BEEF3", "WIZC3")

_CAMPOS_NUMERICOS_ESPERADOS = {
    "beta_referencia",
    "ev_ebitda_medio_referencia",
    "psr_medio_referencia",
    "fator_conversao_nopat_referencia",
    "pct_divida_moeda_estrangeira",
    "cap_crescimento_ciclico",
    "volume_medio_diario",
    "dividendo_projetado",
    "taxa_crescimento_perpetuidade_ddm",
    "valor_mercado",
}


def test_nenhum_campo_de_perfil_setor_e_numerico_cru():
    hints = typing.get_type_hints(PerfilSetor)
    for nome, tipo in hints.items():
        tipos_no_hint = typing.get_args(tipo) or (tipo,)
        for candidato in tipos_no_hint:
            assert candidato not in (float, int), (
                f"Campo '{nome}' de PerfilSetor resolve pra {candidato} — "
                "campo numérico cru não é permitido, deve usar "
                "CampoComProveniencia (ver CONTEXT.md, Fases 0 e 1)."
            )


def test_campos_de_referencia_esperados_sao_optional_campo_com_proveniencia():
    hints = typing.get_type_hints(PerfilSetor)
    for nome in _CAMPOS_NUMERICOS_ESPERADOS:
        args = typing.get_args(hints[nome])
        assert CampoComProveniencia in args, (
            f"Campo '{nome}' deveria ser Optional[CampoComProveniencia], "
            f"mas resolveu pra {hints[nome]}."
        )


@pytest.mark.parametrize("ticker", _TICKERS_PILOTO)
def test_valores_carregados_dos_tickers_piloto_respeitam_o_contrato(ticker):
    perfil = obter_perfil(ticker)
    for nome in _CAMPOS_NUMERICOS_ESPERADOS:
        valor = getattr(perfil, nome)
        assert valor is None or isinstance(valor, CampoComProveniencia), (
            f"{ticker}.{nome} = {valor!r} não é None nem CampoComProveniencia."
        )
