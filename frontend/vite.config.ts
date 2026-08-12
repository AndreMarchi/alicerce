import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Porta fixa diferente de 5173 (padrão do Vite) — o valuation-tracker
  // antigo já usa 5173 localmente, e os dois projetos podem rodar ao
  // mesmo tempo na mesma máquina.
  server: {
    port: 5180,
  },
  // Sem proxy pra /api ainda — o Alicerce não tem nenhum endpoint
  // exposto (api/ está vazio, ver CONTEXT.md). Quando existir, seguir o
  // mesmo padrão do valuation-tracker (server.proxy['/api'] -> backend).
})
