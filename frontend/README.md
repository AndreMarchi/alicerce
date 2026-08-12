# Alicerce — Frontend

Esqueleto React + TypeScript + Vite, rodando localmente. **Sem nenhuma
API conectada ainda** — o backend (`../backend/`) não expõe nenhum
endpoint (`api/` está vazio), então não há dado real pra mostrar aqui
ainda. Ver `../CONTEXT.md` pra decisões de escopo e `../docs/ROADMAP.md`
pra quando a integração real entra (Fase 4+).

## Como rodar

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5180` (porta fixa, diferente da 5173 padrão
do Vite — o `valuation-tracker` antigo já usa 5173 localmente, e os
dois projetos podem rodar ao mesmo tempo).

## Scripts

- `npm run dev` — servidor de desenvolvimento.
- `npm run build` — build de produção (`tsc -b && vite build`, gera `dist/`).
- `npm run lint` — `oxlint`.
- `npm run preview` — serve o build de produção localmente.

## Stack

React 19 + TypeScript + Vite 8, lint via `oxlint`. Sem framework de CSS
(estilo mínimo em `src/index.css`, com suporte a light/dark via
`prefers-color-scheme`) — nenhuma decisão de design system foi tomada
ainda.
