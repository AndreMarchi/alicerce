# Resumo de sessão — 2026-08-17

Documento de retomada rápida, pensado pra outra sessão de trabalho (ou
um humano) entender o estado do projeto em poucos minutos, sem precisar
reler o `CONTEXT.md` inteiro (~1500 linhas) do zero. Detalhe técnico
completo continua só no `CONTEXT.md` — este arquivo é o resumo de alto
nível.

**Nota sobre este documento**: a tarefa que pediu este resumo referenciava
um `resumo_sessao_alicerce.md` anterior, supostamente já existente no
projeto e usado com sucesso por outra sessão. Não encontrei esse arquivo
em lugar nenhum do repositório (`find`/`grep` não retornaram nada) — não
existe hoje, ou nunca existiu, ou não foi commitado. Este é o primeiro
documento desse tipo no projeto, não uma continuação de um anterior.

## 1. Ponto de partida desta sessão

A sessão começou com 5 commits já feitos localmente (numa sessão
anterior a esta) mas ainda não publicados no remoto: Fase 2 (primeira
fatia de `classificar_divergencia`), esqueleto do frontend
(React/TypeScript/Vite), registro de 4 perfis de `RegraPerfil`
encontrados em auditoria (no `ROADMAP.md`), uma trava de erro de chamada
óbvio no CAPM, e uma trava de limiares invertidos em
`sanity/divergencia.py`. A primeira ação desta sessão foi verificar e
publicar esses 5 commits (checklist de push completo, nada suspeito
encontrado) — não foi trabalho novo desta sessão, só housekeeping de
sincronização com o remoto.

## 2. O que foi implementado e commitado nesta sessão (ordem cronológica)

### 2.1 — TAEE3: dados reais de DDM+CAPM + primeira integração ponta a ponta
**Commit `3b7fdf7`** (publicado no remoto)

Populou `PerfilSetor` de TAEE3 com dado real pesquisado (dividendo
projetado, taxa de crescimento na perpetuidade, beta próprio, valor de
mercado, `eh_estatal`) e escreveu um teste de integração
(`test_taee3_ddm_capm_e2e.py`) demonstrando `calcular_capm()` ->
`calcular_ddm()` funcionando pela primeira vez com número real —
resultado: `Ke=16%` (clampado no teto), valor calculado `R$7,92` vs.
preço de mercado de referência `R$12,44` no dia.

**Decisões importantes**: dividendo projetado escolhido no extremo
CONSERVADOR de uma faixa de mercado divergente (R$0,99 a R$1,16) —
reduz risco de superestimar via DDM. `eh_estatal=False` apesar da CEMIG
(estatal) ser sócia controladora da TAESA — controle é COMPARTILHADO
com a ISA Brasil (privada), nenhuma das duas partes tem maioria
isolada. Selic (14,00% a.a., Copom 05/08/2026) ficou hardcoded no
teste como valor pontual de uma data específica — não existe mecanismo
de busca de Selic no Alicerce ainda, decisão deliberada de não criar um
agora.

*(Numa tarefa seguinte, ainda nesta sessão, uma discrepância aparente
no `Ke` bruto — usuário calculou 20,28% manualmente, o teste reportou
22,78% — foi investigada e confirmada como erro na conta manual do
usuário, não bug: a fórmula real inclui um `COUNTRY_RISK_PREMIUM` fixo
de 2,5% que a conta manual tinha omitido. Nenhum código foi alterado
por causa disso.)*

### 2.2 — RegraPerfil mínimo: roteamento automático DDM_ONLY
**Commit `c703ae0`** (local, pendente de push)

Implementou `pipeline/ddm_only.py::calcular_valor_ddm_only(ticker, rf)`
— consulta a tag `DDM_ONLY` de um ticker e, se presente, encadeia
`calcular_capm()` -> `calcular_ddm()` automaticamente (reproduz
exatamente o resultado manual do item 2.1); se ausente, retorna um
sinal explícito de "sem método aplicável", nunca `None` silencioso.

**Decisão importante**: a função **não** se chama `RegraPerfil`, apesar
do nome parecer óbvio à primeira vista. `RegraPerfil` já está reservado
no `ROADMAP.md` como um `Protocol` (`aplicar(contexto:
ContextoValuation) -> ContextoValuation`) pro design GERAL de múltiplas
regras com precedência — `ContextoValuation` não existe em código
nenhum, só pseudocódigo, e esta tarefa cobria só um caso (sem
precedência a resolver). Usar o nome reservado aqui seria ocupá-lo com
uma implementação que não bate com a assinatura documentada.

### 2.3 — Perfil de insolvência confirmada (portão de segurança)
**Commit `a7aee6b`** (local, pendente de push)

Primeiro dos 4 perfis de `RegraPerfil` já registrados no `ROADMAP.md`
(auditoria do valuation-tracker), maior prioridade. Adicionou
`PerfilSetor.em_recuperacao_judicial` (bool simples) e
`perfis/insolvencia.py::ticker_bloqueado_por_insolvencia()`. Os 6
tickers-piloto (TAEE3, CPLE3, GEPA4, ITSA4, BEEF3, WIZC3) foram
pesquisados individualmente — nenhum está em recuperação judicial hoje
(dado real verificado, não suposição).

**Decisão importante**: campo bool simples, não uma `TagPerfilEconomico`
nova — as tags existentes alimentam composição de METODOLOGIA (qual
método usar); insolvência é um PORTÃO BINÁRIO ortogonal a isso (bloqueia
recomendação antes de qualquer método rodar). Função também não se
chama `RegraPerfil`, mas por um motivo diferente do item 2.2: um portão
binário não tem "método" a escolher, então nem pertence conceitualmente
à mesma família — não é candidato a virar uma das N regras compostas.

### 2.4 — Perfil de classe de ativo incompatível (fundos)
**Commit `b57461b`** (local, pendente de push)

Segundo dos 4 perfis do `ROADMAP.md`. Adicionou `PerfilSetor.classe_ativo`
(`Optional[Literal["acao", "unit", "fiagro", "fii"]]`, SEM default
seguro — campo ausente levanta erro explícito) e
`perfis/classe_ativo.py::ticker_bloqueado_por_classe_ativo_incompativel()`.
Os 6 pilotos são todos `classe_ativo="acao"`.

**Achado de design real, vale destacar**: `TAEE11` (unit da TAESA) e
outras 3 units de tickers-piloto (`CPLE11`, `ITSA11`, `BEEF11`) terminam
em "11" — mesmo sufixo de FIAGROs/FIIs — mas NÃO são fundos, são
empresas reais empacotadas. `GEPA11` é ainda mais enganoso: é uma
DEBÊNTURE, nem unit nem fundo. Por isso a detecção nunca infere classe
de ativo pelo sufixo do ticker, sempre um campo explícito. Nenhum desses
tickers "11" está cadastrado no Alicerce — só documentados como achado.

## 3. Peças "órfãs" ou parciais no radar

Nenhum desses 3 itens abaixo está integrado entre si nem com nenhum
pipeline de produção — são peças isoladas, testadas individualmente,
aguardando composição futura:

- **`pipeline/ddm_only.py::calcular_valor_ddm_only()`** (item 2.2) — só
  roteia TAEE3 (único ticker com tag `DDM_ONLY` hoje). Não sabe nada
  sobre insolvência nem classe de ativo.
- **`perfis/insolvencia.py::ticker_bloqueado_por_insolvencia()`** (item
  2.3) — função isolada, não é chamada por `ddm_only.py` nem por
  nenhum outro lugar. Se um ticker insolvente tivesse tag `DDM_ONLY`
  hoje, `calcular_valor_ddm_only()` calcularia um valor normalmente,
  sem saber do portão de insolvência.
- **`perfis/classe_ativo.py::ticker_bloqueado_por_classe_ativo_incompativel()`**
  (item 2.4) — mesma situação: isolada, não integrada com nada.

Essa não-integração é DELIBERADA, decidida explicitamente em cada uma
das 3 tarefas — não é trabalho esquecido. A composição dos 3 (mais os 2
perfis ainda não implementados, ver seção 5) fica pra quando
`RegraPerfil` for retomado de verdade.

## 4. Estado do Git

- **Branch atual**: `main`
- **Sincronização com o remoto**: ahead de `origin/main` por **3
  commits locais, ainda não publicados** (`c703ae0`, `a7aee6b`,
  `b57461b` — itens 2.2, 2.3 e 2.4 acima). O item 2.1 (`3b7fdf7`) já
  foi publicado durante esta sessão.
- **Working tree**: limpo.
- **Branches de segurança locais pendentes de decisão** (nenhuma
  publicada, nenhuma deletada ainda nesta sessão):
  `backup-pre-commit-regraperfil-minimo`,
  `backup-pre-commit-perfil-insolvencia`,
  `backup-pre-commit-perfil-fundos`.

Últimos 8 commits (cobre toda a sessão + o último commit da sessão
anterior, pra referência):

```
b57461b Perfil de classe de ativo incompatível: portão de fundos (só detecção)
a7aee6b Perfil de insolvência confirmada: portão de segurança (só detecção)
c703ae0 RegraPerfil mínimo: roteamento automático DDM_ONLY (só TAEE3 por enquanto)
3b7fdf7 TAEE3: dados reais de DDM+CAPM e primeira integração ponta a ponta
b5a9ed0 divergencia.py: trava de limiares invertidos, sem renomear nada existente
ccbd896 CAPM (Ke): trava de erro de chamada óbvio, sem alterar o clamp de saída
0f66774 Roadmap: registra 4 perfis de RegraPerfil encontrados em auditoria real
39337b2 Frontend: esqueleto React + TypeScript + Vite, rodando local
```

**Suíte de testes**: 117 testes passando (`cd backend && pytest`,
requer Python 3.11+ — `pip install -e ".[dev]"` primeiro).

## 5. Próximos passos naturais (ordem já estabelecida nesta sessão, não reordenada)

Fila de perfis do `ROADMAP.md`, na ordem de prioridade já registrada:

1. ~~Insolvência confirmada~~ — detecção feita (item 2.3), integração pendente.
2. ~~Fundo/classe de ativo incompatível~~ — detecção feita (item 2.4), integração pendente.
3. **Financeiro/seguradora** — próximo perfil a implementar. Caso real
   de referência já documentado no `ROADMAP.md`: WIZC3 (um dos 6
   pilotos já cadastrados no Alicerce).
4. **Patrimonial/imóveis** — último dos 4 perfis, mais difícil (exige
   desenhar um método de valuation baseado em patrimônio, não em
   lucro — não é só roteamento).

Depois dos 4 perfis (ou em paralelo, conforme prioridade que for
decidida numa sessão futura, não fixada aqui):

- Segundo ticker-piloto com dado real ponta a ponta (hoje só TAEE3 tem).
- Triagem/composição real de `RegraPerfil` (o `Protocol` geral, ainda
  pseudocódigo) — só faz sentido depois de mais de um perfil pronto pra
  compor de verdade.
- Decisão de push dos 3 commits locais pendentes (e das 3 branches de
  segurança acumuladas) — não tomada nesta sessão, fica pra quando o
  usuário decidir.

## 6. Lições e armadilhas descobertas nesta sessão

- **Confirmar antes de nomear, sempre.** Duas vezes nesta sessão
  (`DDM_ONLY` e insolvência) o nome óbvio primeiro-instinto teria sido
  `RegraPerfil` — nas duas vezes, investigar o `ROADMAP.md` antes de
  escrever qualquer código revelou que o nome já estava reservado pra
  um design diferente (`Protocol` com `ContextoValuation`, que não
  existe em código). Vale o hábito de checar convenção existente antes
  de nomear algo nesta base, não só nesses dois casos.
- **Sufixo de ticker "11" não é sinal confiável de fundo.** `TAEE11`,
  `CPLE11`, `ITSA11`, `BEEF11` são units de empresas reais (4 dos 6
  pilotos do Alicerce); `GEPA11` é uma debênture. Só `classe_ativo`
  como campo explícito por ticker resolve isso — nunca inferência por
  padrão de string.
- **Verificar alegações factuais do prompt antes de agir sobre elas,
  mesmo quando vêm do usuário.** Duas vezes nesta sessão uma premissa
  do prompt não bateu com o estado real do repositório: (1) a
  quantidade de commits pendentes de push foi superestimada numa
  tarefa (o prompt esperava mais commits do que realmente estavam
  pendentes); (2) `TAEE11` foi descrito como "já no universo de dados
  do Alicerce" quando na verdade nunca foi cadastrado. Em ambos os
  casos, `git fetch`/`grep` direto no repositório resolveu a dúvida
  antes de agir sobre a premissa errada — vale manter esse hábito de
  verificar em vez de confiar cegamente na descrição do prompt.
- **Campo ausente não é "seguro" por padrão, quando o custo de errar é
  alto.** Padrão consistente nos 2 perfis de portão desta sessão:
  `em_recuperacao_judicial` tem default `False` porque já foi
  VERIFICADO pra todos os pilotos (dado confirmado, não ausência);
  `classe_ativo` não tem nenhum default seguro (`None` levanta erro),
  porque não existe um valor "óbvio e seguro" pra assumir quando o dado
  simplesmente não foi cadastrado ainda.
