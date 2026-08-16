"""
Teste de integração ponta a ponta: CAPM alimentando DDM com dado real de
TAEE3 — primeira vez que os dois métodos de valuation do Alicerce se
conectam no projeto (ver CONTEXT.md, "TAEE3 — dados reais para
DDM+CAPM").

NÃO é wiring de produção: não há endpoint, não há chamada a
`classificar_divergencia()` (Fase 2), e `RegraPerfil` continua não
implementado — este teste só demonstra que `calcular_capm()` ->
`calcular_ddm()` produz um número plausível quando alimentado com dado
real de `PerfilSetor`, prova de conceito da Fase 2/3 conectadas.
"""

import pytest

from alicerce.capm.capm import calcular_capm
from alicerce.perfis.motor import obter_perfil
from alicerce.valuation.ddm import calcular_ddm

# Selic confirmada na 280ª reunião do Copom (04-05/08/2026): 14,00% a.a.
# Valor PONTUAL de uma data específica — não é um mecanismo permanente de
# busca de Selic (não existe no Alicerce ainda, ver CONTEXT.md). Precisa
# ser atualizado manualmente se este teste for revisitado numa sessão
# futura em que a Selic já tenha mudado (Copom se reúne a cada ~45 dias).
SELIC_2026_08_05 = 0.14


def test_capm_alimenta_ddm_ponta_a_ponta_com_dado_real_de_taee3():
    perfil = obter_perfil("TAEE3")

    # Todos os inputs abaixo vêm do PerfilSetor real (CampoComProveniencia
    # com fonte/confiança/data documentadas em perfis_ticker.json), nunca
    # hardcoded soltos aqui — só a Selic (ver comentário acima) foge
    # dessa regra, por não haver mecanismo de busca no Alicerce ainda.
    assert perfil.beta_referencia is not None
    assert perfil.valor_mercado is not None
    assert perfil.dividendo_projetado is not None
    assert perfil.taxa_crescimento_perpetuidade_ddm is not None

    ke = calcular_capm(
        rf=SELIC_2026_08_05,
        beta=perfil.beta_referencia.valor,
        valor_mercado=perfil.valor_mercado.valor,
        eh_estatal=perfil.eh_estatal,
    )
    # ke bruto = 0.14 + 0.96*0.055 + 0.025 + 0.01 (size premium, >R$10bi)
    #          = 0.2278, acima do teto -> clampado em 16%. Selic
    # historicamente alta em 2026 empurra o Ke pro teto do CAPM — o
    # clamp (ver capm.py) está fazendo trabalho real aqui, não é um
    # caso de borda artificial.
    assert ke == pytest.approx(0.16)

    valor_intrinseco = calcular_ddm(
        dividendo_projetado=perfil.dividendo_projetado.valor,
        ke=ke,
        g=perfil.taxa_crescimento_perpetuidade_ddm.valor,
    )
    # 0.99 / (0.16 - 0.035) = 0.99 / 0.125 = 7.92
    assert valor_intrinseco == pytest.approx(7.92)

    # Sanity check de plausibilidade (não é classificar_divergencia() —
    # isso fica pra quando houver preco_mercado real fluindo pro sistema
    # de forma permanente, fora de escopo aqui): positivo e na mesma
    # ordem de grandeza do preço de mercado real do dia em que este
    # teste foi escrito (~R$12,44 em 17/08/2026, statusinvest.com.br) —
    # não precisa bater exatamente, só não pode ser absurdo (negativo,
    # zero, ou ordens de grandeza distante).
    preco_mercado_referencia_17_08_2026 = 12.44
    assert valor_intrinseco > 0
    razao = valor_intrinseco / preco_mercado_referencia_17_08_2026
    assert 0.3 < razao < 3.0, (
        f"valor_intrinseco ({valor_intrinseco}) fora de uma faixa "
        "plausível relativa ao preço de mercado de referência "
        f"({preco_mercado_referencia_17_08_2026}) — razão {razao:.2f}."
    )
