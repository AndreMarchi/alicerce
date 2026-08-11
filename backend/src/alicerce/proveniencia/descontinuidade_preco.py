"""
Detecção de descontinuidade na série histórica de preço — extensão da
Fase 0 (ver docs/ROADMAP.md, Fase 0, entregável adicionado nesta sessão,
e CONTEXT.md).

Motivação real: RVEE3 reportou variação de 52 semanas de R$0,68 a
R$31,00 (razão ~45,6x) — quase certamente um evento societário
(grupamento/desdobramento) não ajustado corretamente na série histórica
de preço antes de o dado chegar ao pipeline, não volatilidade orgânica.

IMPORTANTE — investigado antes de escrever este módulo (ver CONTEXT.md):
hoje o Alicerce ainda NÃO tem nenhum estágio de ingestão de preço
histórico implementado (`pipeline/`, `capm/`, `sanity/` são pacotes
vazios) nem nenhum campo de preço em `PerfilSetor`. As funções abaixo não
têm nenhum call site real ainda — ficam prontas pro estágio de ingestão
futuro chamar, operando sobre qualquer `CampoComProveniencia` derivado de
preço (não assumem um nome de campo específico, porque esse campo ainda
não existe em nenhum schema do projeto).
"""

from __future__ import annotations

from dataclasses import replace

from alicerce.proveniencia.schema import CampoComProveniencia

# Limiar de razão máxima/mínima de 52 semanas acima do qual a
# descontinuidade é tratada como sinal de evento societário
# (grupamento/desdobramento) não ajustado, não volatilidade legítima.
#
# Por que 10x: grupamentos/desdobramentos na B3 costumam ser 1:5, 1:10,
# 1:20 ou mais agressivos (comuns em micro/nanocaps pra evitar
# desenquadramento de preço mínimo) — qualquer um desses já produz uma
# razão >= 5x isolado, e ainda soma com o movimento de preço real do
# período. Uma ação sem nenhum evento societário raramente sai de ~5-8x
# de razão máx/mín em 52 semanas mesmo em cenários extremos (rali forte
# ou colapso seguido de recuperação parcial) — passar de 10x é raro o
# suficiente pra tratar como suspeito por padrão. RVEE3 (~45,6x) fica
# muito acima da margem, não é um caso limítrofe.
# NÃO calibrado estatisticamente contra uma amostra real da B3 — decisão
# de bom senso, a revisar se algum ticker legítimo (sem evento
# societário) for flagueado incorretamente na prática.
RAZAO_MAX_MIN_52W_SUSPEITA: float = 10.0


def razao_max_min_52_semanas(maxima_52_semanas: float, minima_52_semanas: float) -> float:
    """
    Razão entre a máxima e a mínima de 52 semanas.

    `minima_52_semanas` precisa ser > 0 (preço não pode ser zero ou
    negativo) — levanta `ValueError` se não for, em vez de propagar um
    `ZeroDivisionError`/resultado sem sentido.
    """
    if minima_52_semanas <= 0:
        raise ValueError(
            "minima_52_semanas precisa ser > 0 pra calcular a razão "
            f"(recebido: {minima_52_semanas})."
        )
    return maxima_52_semanas / minima_52_semanas


def eh_descontinuidade_suspeita(
    maxima_52_semanas: float,
    minima_52_semanas: float,
    limiar: float = RAZAO_MAX_MIN_52W_SUSPEITA,
) -> bool:
    """
    True quando a razão máx/mín de 52 semanas ULTRAPASSA `limiar` — ver
    docstring de `RAZAO_MAX_MIN_52W_SUSPEITA` pro racional do valor
    default. Razão exatamente igual ao limiar NÃO é suspeita (é preciso
    ultrapassar, não só atingir — ver `tests/unit/test_descontinuidade_preco.py`
    pro caso de borda).
    """
    return razao_max_min_52_semanas(maxima_52_semanas, minima_52_semanas) > limiar


def aplicar_deteccao_descontinuidade(
    campo: CampoComProveniencia,
    maxima_52_semanas: float,
    minima_52_semanas: float,
    limiar: float = RAZAO_MAX_MIN_52W_SUSPEITA,
) -> CampoComProveniencia:
    """
    Aplica a detecção de descontinuidade a um `CampoComProveniencia`
    (tipicamente um preço derivado da série histórica de 52 semanas).

    Quando a razão máx/mín ultrapassa `limiar`: retorna uma NOVA
    instância com `confianca` forçada pra `"baixa"` e `motivo_override`
    preenchido automaticamente com a razão calculada e o tipo de anomalia
    suspeita — o `valor` do campo é preservado (nunca descartado em
    silêncio, ver CONTEXT.md, princípio "nenhum campo mudo"), só a
    proveniência muda.

    Quando a razão está dentro do limiar (inclusive exatamente igual):
    retorna o `campo` original, sem nenhuma alteração.
    """
    razao = razao_max_min_52_semanas(maxima_52_semanas, minima_52_semanas)
    if razao <= limiar:
        return campo

    motivo = (
        f"Descontinuidade suspeita na série de 52 semanas: razão "
        f"máxima/mínima = {razao:.2f}x (limiar: {limiar:.1f}x; mínima "
        f"informada R${minima_52_semanas:.2f}, máxima R${maxima_52_semanas:.2f}) "
        "— possível evento societário (grupamento/desdobramento) não "
        "ajustado na série histórica de preço. Confiança forçada para "
        "'baixa' automaticamente; revisar a fonte antes de usar este "
        "valor em cálculo."
    )
    return replace(campo, confianca="baixa", motivo_override=motivo)
