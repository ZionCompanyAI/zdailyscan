# Progress

## Em andamento
(nenhum)

## Concluído (issue #170)
- TASK-170: docs — docs/api-reference.md com todos os endpoints (23 rotas), schemas ScanResult e ProductScore — arquivado 2026-06-03

## Concluído (issue #167)
- TASK-167: fix(pipeline+api) — ScanResult.status="completed" (default) + /scan/run redireciona para _run_scan_background do dashboard (atualiza _scan_status corretamente) — arquivado 2026-06-02

## Concluído (issue #137)
- TASK-137: fix(pipeline) — TECH_KEYWORDS + is_tech_product() regex word-boundary; categoria scan filtra non-tech antes de chamadas de API; keyword scan não afetado — arquivado 2026-06-02

## Concluído (issue #154)
- TASK-154: fix(scraper) — subprocess curl --compressed + regex undefined-como-chave (2 passos) + NaN/Infinity→null + nixpacks.toml + preço None-safe — arquivado 2026-06-01

## Concluído (issue #150)
- TASK-150: fix(scraper) — Accept-Encoding + 9 browser headers em _SCRAPLING_HEADERS + retry 3x com asyncio.sleep(4) em _scrape_with_scrapling — arquivado 2026-06-01

## Concluído (issue #145)
- TASK-145: fix(scraper) — sanitize `undefined` JS token via re.sub antes do raw_decode + multi-pattern fallback (_init_data_ → runParams → __INITIAL_STATE__) para keyword search + None-safe numeric parsing — arquivado 2026-06-01

## Concluído (issue #143)
- TASK-143: fix(scraper) — _scrape_with_scrapling substitui StealthyFetcher/Playwright por httpx.get + regex _dida_config_._init_data_ + _find_product_list recursivo — arquivado 2026-06-01

## Concluído (issue #139)
- TASK-139: feat(scraper) — SCRAPER_MODE=scrapling com StealthyFetcher (HTTP puro, sem custos) + fallback automático firecrawl→scrapling em caso de 402 — arquivado 2026-06-01

## Concluído (issue #129)
- TASK-129: chore — remover categorias não-tech (Home & Garden 200000828, Sports 200000834) de CATEGORIES e CATEGORY_NAMES; 4 testes atualizados para 3 categorias — arquivado 2026-06-01

## Concluído (issue #107)
- TASK-107: fix(storage) — _scans_dir() lê DATA_DIR env var; elimina SCANS_DIR hardcoded; dashboard.py + 3 test files atualizados — arquivado 2026-06-01

## Concluído (issue #126)
- TASK-126: fix(scraper) — _scrape_with_http() via httpx JSON API, SCRAPER_MODE default http, crawl4ai fallback — arquivado 2026-06-01

## Concluído (issue #124)
- TASK-124: fix(scraper) — domain+path injetados nos cookies AliExpress para Playwright — arquivado 2026-06-01

## Concluído (issue #122)
- TASK-122: fix(scraper) — session_cookies injetado no BrowserConfig, wait_for removido, try/except no crawler — arquivado 2026-06-01

## Concluído (issue #115)
- TASK-115: fix(scraper) — Firecrawl removido de get_hot_products; crawl4ai é sempre o scraper — arquivado 2026-06-01

## Concluído (issue #110)
- TASK-110: feat(analyzer) — search_br_market_via_zoom Zoom.com.br fallback — arquivado 2026-06-01

## Concluído (issue #108)
- TASK-108: infra — proxy ML no OC01 (systemd ativo) — bloqueado: OC01 IP também 403 pela ML CloudFront WAF — arquivado 2026-06-01

## Concluído (issue #104)
- TASK-104: fix(analyzer) — ML search proxiada via ML_SEARCH_PROXY_URL (PolicyAgent block) — arquivado 2026-06-01

## Concluído (issue #103)
- TASK-103: fix(analyzer) — get_ml_token auth-bus dinâmico, fallback ML_USER_ACCESS_TOKEN — arquivado 2026-06-01

## Concluído (issue #100)
- TASK-100: fix(scraper) — CrawlerRunConfig cookies kwarg removido — arquivado 2026-06-01

## Concluído (issue #98)
- TASK-098: fix(scraper) — crawl4ai chamado mesmo sem cookies — arquivado 2026-06-01

## Concluído (issue #91)
- TASK-091: fix(scraper) — Firecrawl httpx timeout 60→180s, body timeout 150000ms, %r logger — arquivado 2026-05-31

## Concluído (issue #85)
- TASK-085: test — cobrir gaps de regressão #81/#82 (test_scraper_regressions.py + endpoint count) — arquivado 2026-05-30

## Concluído (issue #82)
- TASK-082: fix(scraper) — SCRAPER_MODE=firecrawl respeitado mesmo com cookies — arquivado 2026-05-30

## Concluído (issue #81)
- TASK-081: fix(scraper) — min_rating default 4.9→0.0, regressão PR #77 — arquivado 2026-05-30

## Concluído (issue #78)
- TASK-078: fix(settings) — persistir cookies e categorias em Railway env vars — arquivado 2026-05-30

## Concluído (issue #57)
- TASK-057: feat(dashboard) — AliExpress credentials form in settings — arquivado 2026-05-30

## Concluído (issue #55)
- TASK-055: fix(deploy) — playwright install chromium no startCommand Railway — arquivado 2026-05-30

## Concluído (issue #12)
- TASK-012: CI workflow — habilitar GitHub Merge Queue — arquivado 2026-05-29

## Concluído (issue #42)
- TASK-042: Settings — remover API AliExpress, categorias configuráveis, card crawl4ai — arquivado 2026-05-29

## Concluído (issue #40)
- TASK-040: fix POST /scan/trigger — redireciona 303 para /scanner — arquivado 2026-05-29

## Concluído (issue #38)
- TASK-038: Mobile-first redesign — todas as páginas do dashboard — arquivado 2026-05-29

## Concluído (adicionados nesta sessão)
- TASK-036: Explorer de Produtos + Scanner + Settings — Fase 1 UI — arquivado 2026-05-29

## Concluído (adicionados nesta sessão)

## Concluído
- TASK-001: Estrutura base do projeto ZDailyScan — arquivado 2026-05-28
- TASK-002: Analyzer ML market check + import calculator — arquivado 2026-05-28
- TASK-003: Scorer de viabilidade ZDailyScan — arquivado 2026-05-28
- TASK-004: Scheduler diário + pipeline + storage + endpoints /scan — arquivado 2026-05-28
- TASK-005: Scraper AliExpress com Crawl4AI + mock + fallback Firecrawl — arquivado 2026-05-28
- TASK-006: Conectar scraper Crawl4AI ao pipeline e expor endpoint — arquivado 2026-05-28
- TASK-007: Report diário — top 10 via Telegram + arquivo Markdown — arquivado 2026-05-28
- TASK-008: Post-merge GitHub Action — auto-atualiza README e progress.md — arquivado 2026-05-28
- TASK-030: Dashboard web — relatórios, force scan e login compartilhável — arquivado 2026-05-28
