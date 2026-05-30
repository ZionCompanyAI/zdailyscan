# [TASK-052] Playwright E2E Gate — Piloto Contrato de Qualidade

## Objetivo
Implementar gate de qualidade Playwright E2E no zdailyscan como projeto piloto do Contrato de Qualidade MBZSoluções/ZionCompanyAI.

## Pacote / Módulo
Novos artefatos: `tests/e2e/` + `.github/workflows/e2e-gate.yml` + `playwright.config.ts` + `package.json`

## Contratos (Referências Técnicas)

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "html",
  use: {
    baseURL: process.env.BASE_URL || "https://zdailyscan.zioncompanyai.com.br",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
});
```

```typescript
// GET /health retorna: {"status": "ok", "service": "zdailyscan"}
// Login: POST /login com username + password → redirect 303 → /dashboard
// Scanner: GET /dashboard/scanner — tem botão "Iniciar Scan"
```

## Detalhes de Implementação
- smoke.spec.ts: /health OK + root responde
- contract.spec.ts: /health JSON schema + status 200
- auth.spec.ts: login funciona com DASHBOARD_USERNAME/DASHBOARD_PASSWORD; redirect para /dashboard
- dashboard.spec.ts: /dashboard/scanner carrega; botão "Iniciar Scan" existe e está habilitado
- CI workflow: PR + merge_group, Node 20, chromium, artifact em falha (7 dias), timeout 15min
- Credenciais via env: DASHBOARD_USERNAME, DASHBOARD_PASSWORD, BASE_URL

## Tasks
- [x] Criar `.openspec/changes/TASK-052-playwright-e2e-gate.md`
- [x] Criar `package.json` com devDependency `@playwright/test`
- [x] Criar `playwright.config.ts`
- [x] Criar `tests/e2e/smoke.spec.ts`
- [x] Criar `tests/e2e/contract.spec.ts`
- [x] Criar `tests/e2e/auth.spec.ts`
- [x] Criar `tests/e2e/dashboard.spec.ts`
- [x] Criar `.github/workflows/e2e-gate.yml`
- [x] Adicionar `playwright-report/` ao `.gitignore`

## Critérios de Verificação
```bash
# Estrutura criada
test -f .github/workflows/e2e-gate.yml
test -f playwright.config.ts
test -f tests/e2e/smoke.spec.ts
test -f tests/e2e/contract.spec.ts

# Testes passam (requer servidor rodando em localhost:8000)
SCRAPER_MODE=mock BASE_URL=http://localhost:8000 npx playwright test \
  tests/e2e/smoke.spec.ts tests/e2e/contract.spec.ts --reporter=list
```
