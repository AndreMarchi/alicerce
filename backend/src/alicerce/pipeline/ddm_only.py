"""
Roteamento mínimo de perfil -> método de valuation — só o caso DDM_ONLY.

`pipeline/` já estava reservado como "orquestração calculation-pipeline"
(ver README.md, nunca usado até agora — este é o primeiro módulo real do
pacote). Conecta `perfis/motor.py::obter_tags()` aos dois métodos de
valuation já implementados (`capm/capm.py::calcular_capm()`,
`valuation/ddm.py::calcular_ddm()`), reproduzindo automaticamente o que
`tests/integration/test_taee3_ddm_capm_e2e.py` (commit `3b7fdf7`) já
validou manualmente — sem mais precisar saber de antemão, por fora do
sistema, que "TAEE3 usa DDM".

**NÃO é o `RegraPerfil` do `docs/ROADMAP.md` (Fase 1, linha ~61)** —
nome deliberadamente diferente, não uma variação de conveniência.
`RegraPerfil` lá é um `Protocol` (`aplicar(self, contexto:
ContextoValuation) -> ContextoValuation`), parte de um design GERAL de
composição de `N` regras com precedência
(`REGRAS: dict[str, RegraPerfil]`, cobrindo os 4 perfis descritos em
"Fase 1 — Motor de perfis compostos": insolvência, fundo incompatível,
financeiro/seguradora, patrimonial — nenhum implementado ainda). Dois
motivos concretos pra não reaproveitar esse nome/formato aqui:

1. `ContextoValuation` — o tipo que `aplicar()` recebe e devolve — não
   existe em NENHUM lugar do código-fonte, só como pseudocódigo no
   ROADMAP. Implementar o `Protocol` de verdade exigiria inventar esse
   tipo do zero, sem um segundo caso de uso real ainda pra validar o
   desenho dele.
2. Esta tarefa cobre só UM perfil (`DDM_ONLY`) — não há precedência
   possível ainda entre regras, então o mecanismo de composição
   (`REGRAS: dict[...]`, escolha de qual regra vence) que o `Protocol`
   existe pra resolver não tem nada pra resolver aqui.

Escrever isso como `RegraPerfil` agora seria ocupar o nome reservado
pro design geral com uma implementação estreita que não bate com a
assinatura documentada — pior que só escolher outro nome. Se/quando
`RegraPerfil` for retomado de verdade (mais de um perfil precisando de
composição), este módulo é candidato a virar UMA das implementações do
`Protocol`, não o próprio roteador geral.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from alicerce.capm.capm import calcular_capm
from alicerce.perfis.motor import obter_perfil, obter_tags
from alicerce.perfis.perfil_setor import PerfilSetor
from alicerce.perfis.tags import TagPerfilEconomico
from alicerce.valuation.ddm import calcular_ddm

_CAMPOS_OBRIGATORIOS_DDM_ONLY = (
    "dividendo_projetado",
    "taxa_crescimento_perpetuidade_ddm",
    "beta_referencia",
    "valor_mercado",
)


class StatusValuationDDMOnly(str, Enum):
    CALCULADO = "calculado"
    SEM_METODO_APLICAVEL = "sem_metodo_aplicavel"


@dataclass(frozen=True)
class ResultadoValuationDDMOnly:
    """
    Sinal EXPLÍCITO de resultado — nunca `None` silencioso (mesmo
    princípio de "nenhum campo mudo" do resto do projeto, ver
    `proveniencia/schema.py`). Quem chama precisa checar `status`, não
    inferir do valor de `valor_calculado`/`metodo` sozinho — ambos ficam
    `None` quando `status == SEM_METODO_APLICAVEL`, mas o inverso
    (checar só "valor_calculado is not None") seria um jeito silencioso
    de fazer a mesma checagem, exatamente o que se quer evitar aqui.
    """

    ticker: str
    status: StatusValuationDDMOnly
    metodo: Optional[str] = None  # "DDM", só quando status == CALCULADO
    valor_calculado: Optional[float] = None
    ke: Optional[float] = None  # exposto pra auditoria/teste, não só o valor final


class CampoObrigatorioAusenteError(ValueError):
    """
    Ticker com tag `DDM_ONLY` mas `PerfilSetor` sem algum campo
    obrigatório pro cálculo. Erro explícito, mesmo padrão de
    `TickerSemPerfilError` (`perfis/motor.py`) — nunca calcular com um
    valor inventado nem cair num fallback silencioso quando falta dado.
    """


def calcular_valor_ddm_only(ticker: str, rf: float) -> ResultadoValuationDDMOnly:
    """
    Aplica DDM (via CAPM pro `Ke`) se `ticker` tiver a tag
    `TagPerfilEconomico.DDM_ONLY`; sinaliza "sem método aplicável" caso
    contrário — nunca tenta adivinhar outro método.

    `rf` (Selic) é parâmetro explícito do caller, não buscado
    automaticamente — não existe mecanismo de busca de Selic no
    Alicerce ainda (mesma decisão já tomada e documentada em
    `tests/integration/test_taee3_ddm_capm_e2e.py`, ver CONTEXT.md).

    Levanta `TickerSemPerfilError` (propagada de
    `perfis/motor.py::obter_tags()`/`obter_perfil()`) se `ticker` não
    estiver cadastrado no motor de perfis — nunca cai num resultado
    "sem método aplicável" pra ticker desconhecido, que é um caso
    diferente (ticker conhecido, sem essa tag específica).

    Levanta `CampoObrigatorioAusenteError` se `ticker` tiver a tag mas
    `PerfilSetor` estiver sem algum dos campos obrigatórios pro cálculo.
    """
    tags = obter_tags(ticker)
    if TagPerfilEconomico.DDM_ONLY not in tags:
        return ResultadoValuationDDMOnly(ticker=ticker, status=StatusValuationDDMOnly.SEM_METODO_APLICAVEL)

    perfil = obter_perfil(ticker)
    _validar_campos_obrigatorios_ddm_only(perfil)

    ke = calcular_capm(
        rf=rf,
        beta=perfil.beta_referencia.valor,  # type: ignore[union-attr]
        valor_mercado=perfil.valor_mercado.valor,  # type: ignore[union-attr]
        eh_estatal=perfil.eh_estatal,
    )
    valor = calcular_ddm(
        dividendo_projetado=perfil.dividendo_projetado.valor,  # type: ignore[union-attr]
        ke=ke,
        g=perfil.taxa_crescimento_perpetuidade_ddm.valor,  # type: ignore[union-attr]
    )
    return ResultadoValuationDDMOnly(
        ticker=perfil.ticker,
        status=StatusValuationDDMOnly.CALCULADO,
        metodo="DDM",
        valor_calculado=valor,
        ke=ke,
    )


def _validar_campos_obrigatorios_ddm_only(perfil: PerfilSetor) -> None:
    ausentes = [nome for nome in _CAMPOS_OBRIGATORIOS_DDM_ONLY if getattr(perfil, nome) is None]
    if ausentes:
        raise CampoObrigatorioAusenteError(
            f"PerfilSetor de '{perfil.ticker}' tem tag DDM_ONLY mas está "
            f"faltando campo(s) obrigatório(s) pro cálculo: {', '.join(ausentes)}."
        )
