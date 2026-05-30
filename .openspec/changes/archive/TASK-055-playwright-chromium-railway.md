# [TASK-055] fix(deploy): instalar Playwright Chromium no container Railway

## Objetivo
O scraper usa `crawl4ai` com `AsyncWebCrawler` (headless Chromium). O Railway container não tem
Chromium instalado, causando falha silenciosa no scan. Adicionar instalação do Playwright Chromium
ao `startCommand` do `railway.toml`.

## Pacote / Módulo
`railway.toml` → campo `startCommand` na seção `[deploy]`

## Contratos (Referências Técnicas)

```toml
# Estado desejado
[deploy]
startCommand = "bash -c 'playwright install chromium --with-deps && uvicorn app.main:app --host 0.0.0.0 --port $PORT'"
healthcheckPath = "/health"
restartPolicyType = "on_failure"
```

## Detalhes de Implementação
- Substituir o `startCommand` atual por um bash -c que instala Chromium via `playwright install`
  antes de iniciar o uvicorn
- `--with-deps` garante instalação das dependências do sistema (libXss, etc.) junto com o browser

## Tasks
- [x] Criar spec
- [ ] RED: verificar que grep falha no estado atual
- [ ] GREEN: atualizar railway.toml com novo startCommand
- [ ] Verify: grep deve retornar 0

## Critérios de Verificação
```bash
grep -q "playwright install chromium" railway.toml
```
