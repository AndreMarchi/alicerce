"""
Motor de perfis — fonte única de verdade pra perfil setorial e tags de
perfil econômico por ticker (Fase 1). Ver CONTEXT.md, seção "Fase 1 —
Motor de Perfis", para a investigação e decisões que fundamentam este
módulo.

Interface pública — as 3 funções abaixo (`obter_perfil`, `obter_tags`,
`obter_atribuicoes_tags`) são a ÚNICA porta de entrada pra classificação
de ticker no Alicerce. Nenhum módulo de valuation (Fase 2+) deve decidir
metodologia com `if ticker == "X"` hardcoded — sempre consultar
`obter_tags(ticker)` e compor a decisão a partir daí.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.perfis.tags import AtribuicaoTag, TagPerfilEconomico
from alicerce.proveniencia.schema import CampoComProveniencia

_CAMINHO_DADOS = Path(__file__).parent / "dados" / "perfis_ticker.json"


class TickerSemPerfilError(KeyError):
    """
    Ticker não cadastrado no motor de perfis — falha explícita, nunca um
    fallback silencioso pra perfil genérico (ver CONTEXT.md, Fase 1,
    princípio "Fallback é explícito"). Cadastrar o ticker em
    `dados/perfis_ticker.json` é a única forma de resolver isso.
    """


def _campo_de_dict(dado: Optional[dict]) -> Optional[CampoComProveniencia]:
    if dado is None:
        return None
    return CampoComProveniencia(
        valor=dado["valor"],
        fonte=dado["fonte"],
        confianca=dado["confianca"],
        data_atualizacao=date.fromisoformat(dado["data_atualizacao"]),
        motivo_override=dado.get("motivo_override"),
    )


def _mesclar_com_setor_base(setores_base: dict, entrada_ticker: dict) -> dict:
    """
    Herança de setor (ver CONTEXT.md, "Herança de setor"): merge raso
    entre o perfil-base do setor (se existir) e a entrada do ticker —
    campos da entrada do ticker sempre vencem. Setor sem entrada em
    `_setores_base` funciona normalmente (merge com `{}`).
    """
    setor = entrada_ticker.get("setor")
    base = setores_base.get(setor, {}) if setor else {}
    return {**base, **entrada_ticker}


def _ler_json() -> dict:
    with open(_CAMINHO_DADOS, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def _carregar_perfis() -> dict[str, PerfilSetor]:
    bruto = _ler_json()
    setores_base = bruto.get("_setores_base", {})

    perfis: dict[str, PerfilSetor] = {}
    for ticker, entrada in bruto.get("tickers", {}).items():
        dados = _mesclar_com_setor_base(setores_base, entrada)
        perfis[ticker.upper().strip()] = PerfilSetor(
            ticker=ticker,
            setor=dados["setor"],
            subsetor=dados.get("subsetor"),
            eh_regulado=dados.get("eh_regulado", False),
            eh_ciclico=dados.get("eh_ciclico", False),
            taxonomia_financeira_especial=dados.get("taxonomia_financeira_especial", False),
            eh_estatal=dados.get("eh_estatal", False),
            em_recuperacao_judicial=dados.get("em_recuperacao_judicial", False),
            classe_ativo=dados.get("classe_ativo"),
            beta_referencia=_campo_de_dict(dados.get("beta_referencia")),
            ev_ebitda_medio_referencia=_campo_de_dict(dados.get("ev_ebitda_medio_referencia")),
            psr_medio_referencia=_campo_de_dict(dados.get("psr_medio_referencia")),
            fator_conversao_nopat_referencia=_campo_de_dict(dados.get("fator_conversao_nopat_referencia")),
            pct_divida_moeda_estrangeira=_campo_de_dict(dados.get("pct_divida_moeda_estrangeira")),
            cap_crescimento_ciclico=_campo_de_dict(dados.get("cap_crescimento_ciclico")),
            volume_medio_diario=_campo_de_dict(dados.get("volume_medio_diario")),
            dividendo_projetado=_campo_de_dict(dados.get("dividendo_projetado")),
            taxa_crescimento_perpetuidade_ddm=_campo_de_dict(dados.get("taxa_crescimento_perpetuidade_ddm")),
            valor_mercado=_campo_de_dict(dados.get("valor_mercado")),
            notas=dados.get("notas"),
        )
    return perfis


def _carregar_tags() -> dict[str, tuple[AtribuicaoTag, ...]]:
    bruto = _ler_json()

    tags_por_ticker: dict[str, tuple[AtribuicaoTag, ...]] = {}
    for ticker, entrada in bruto.get("tickers", {}).items():
        atribuicoes = tuple(
            AtribuicaoTag(tag=TagPerfilEconomico(item["tag"]), justificativa=item["justificativa"])
            for item in entrada.get("tags", [])
        )
        tags_por_ticker[ticker.upper().strip()] = atribuicoes
    return tags_por_ticker


# Carregado uma única vez no import do módulo — mesmo padrão de
# valuation-tracker/valuation/perfil_dcf.py::_PERFIS_POR_TICKER.
_PERFIS: dict[str, PerfilSetor] = _carregar_perfis()
_TAGS: dict[str, tuple[AtribuicaoTag, ...]] = _carregar_tags()


def obter_perfil(ticker: str) -> PerfilSetor:
    """
    Retorna o `PerfilSetor` cadastrado pro ticker.

    Levanta `TickerSemPerfilError` se o ticker não estiver cadastrado —
    nunca cai num perfil genérico em silêncio.
    """
    chave = ticker.upper().strip()
    try:
        return _PERFIS[chave]
    except KeyError:
        raise TickerSemPerfilError(
            f"Ticker '{ticker}' não cadastrado no motor de perfis "
            f"({_CAMINHO_DADOS.name}). Cadastrar antes de consultar — "
            "nunca inferir um perfil genérico."
        ) from None


def obter_atribuicoes_tags(ticker: str) -> tuple[AtribuicaoTag, ...]:
    """
    Tags do ticker com a justificativa de cada uma — pra auditoria/UI,
    não pra lógica de decisão (ver `obter_tags` pra isso).

    Levanta `TickerSemPerfilError` se o ticker não estiver cadastrado
    (mesma checagem de `obter_perfil`). Ticker cadastrado sem nenhuma tag
    atribuída retorna tupla vazia — estado válido, não erro (ex: WIZC3,
    perfil completo sem nenhuma situação econômica especial).
    """
    obter_perfil(ticker)  # mesma checagem/erro de ticker desconhecido
    return _TAGS.get(ticker.upper().strip(), ())


def obter_tags(ticker: str) -> frozenset[TagPerfilEconomico]:
    """
    Conjunto de tags do ticker, sem justificativa — o que módulos de
    valuation (Fase 2+) devem consultar pra decidir metodologia:

        if TagPerfilEconomico.DDM_ONLY in obter_tags(ticker):
            ...

    Nunca `if ticker == "TAEE3"` hardcoded em outro módulo.
    """
    return frozenset(atribuicao.tag for atribuicao in obter_atribuicoes_tags(ticker))
