"""
Classificação de divergência entre valor calculado e preço de mercado —
Fase 2 do roadmap ("Sanity check contra mercado", ver docs/ROADMAP.md).

Função pura, mesmo padrão já usado em `proveniencia/descontinuidade_preco.py`
e `valuation/ddm.py`: recebe os limiares como PARÂMETROS diretos, não
como constante interna. Decisão explícita desta sessão (ver CONTEXT.md,
"Fase 2 — primeira fatia"): diferente do limiar de descontinuidade de
preço (`RAZAO_MAX_MIN_52W_SUSPEITA`, que tinha um valor default
justificável por padrões reais de grupamento na B3), não existe nenhuma
referência a limiares de divergência em `CONTEXT.md`/`docs/ROADMAP.md` —
inventar um valor "razoável" agora seria uma escolha implícita sem base.
A chamadora decide os limiares; esta função só classifica.

Este módulo ainda não tem nenhum call site real — não existe "valor
calculado" ponta a ponta pra nenhum ticker ainda (RegraPerfil não
implementado, TAEE3 não populado com os inputs de DDM). Fica pronto pro
pipeline futuro chamar, mesmo padrão dos módulos anteriores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Classificacao = Literal["divergencia_severa", "divergencia_moderada", "dentro_da_faixa"]


@dataclass(frozen=True)
class ResultadoDivergencia:
    """
    `percentual_divergencia` é a divergência COM SINAL (não o valor
    absoluto): `(valor_calculado - preco_mercado) / preco_mercado`.
    Positivo = valor calculado acima do preço de mercado (ação
    "descontada" pelo modelo); negativo = abaixo (ação "cara" pelo
    modelo). A classificação em `classificacao` usa o valor ABSOLUTO
    dessa divergência contra os limiares — severidade não depende de
    direção, só de magnitude.
    """

    classificacao: Classificacao
    percentual_divergencia: float


def classificar_divergencia(
    valor_calculado: float,
    preco_mercado: float,
    limiar_moderada: float,
    limiar_severa: float,
) -> ResultadoDivergencia:
    """
    Classifica a divergência entre `valor_calculado` (resultado de um
    método de valuation) e `preco_mercado` (cotação atual) em
    `"dentro_da_faixa"`, `"divergencia_moderada"` ou
    `"divergencia_severa"`, com o percentual de divergência explícito.

    `limiar_moderada`/`limiar_severa` são frações (0.15 = 15%), mesma
    convenção usada em outros campos fracionários do projeto (ex:
    `pct_divida_moeda_estrangeira`, `cap_crescimento_ciclico`).
    OBRIGATÓRIOS, sem default — ver docstring do módulo pro porquê.

    Limiar exatamente atingido NÃO dispara a classificação mais severa
    (é preciso ultrapassar) — mesma convenção de borda já usada em
    `descontinuidade_preco.py::eh_descontinuidade_suspeita`.

    `limiar_moderada > limiar_severa` (limiares invertidos) levanta
    `ValueError` — decisão revisada (ver CONTEXT.md): limiares
    invertidos não produzem um resultado "conservador", produzem uma
    classificação sem sentido (ex: magnitude 12% cairia em
    "divergencia_severa" com limiar_severa=10% mas nunca passaria por
    "divergencia_moderada" se limiar_moderada=20% > limiar_severa) —
    mesmo padrão de erro explícito já usado em `calcular_ddm()`
    (`Ke <= g`) e nas travas de `calcular_capm()` (beta/rf fora de faixa
    plausível).
    """
    if preco_mercado <= 0:
        raise ValueError(f"preco_mercado precisa ser > 0 (recebido: {preco_mercado}).")
    if limiar_moderada > limiar_severa:
        raise ValueError(
            f"limiar_moderada ({limiar_moderada}) não pode ser maior que "
            f"limiar_severa ({limiar_severa}) — limiares invertidos "
            "produzem classificação sem sentido."
        )

    percentual_divergencia = (valor_calculado - preco_mercado) / preco_mercado
    magnitude = abs(percentual_divergencia)

    if magnitude > limiar_severa:
        classificacao: Classificacao = "divergencia_severa"
    elif magnitude > limiar_moderada:
        classificacao = "divergencia_moderada"
    else:
        classificacao = "dentro_da_faixa"

    return ResultadoDivergencia(classificacao=classificacao, percentual_divergencia=percentual_divergencia)
