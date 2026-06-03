# ZDailyScan — API Reference

Base URL: `http://localhost:8000` (local) | `https://<railway-domain>` (produção)

---

## Autenticação

O ZDailyScan usa dois mecanismos de autenticação:

| Tipo | Uso |
|------|-----|
| **API Key** | Header `x-api-key: <SCAN_API_KEY>` — somente `POST /scan/run` |
| **Session Cookie** | Cookie `session` assinado via `POST /login` — rotas `/dashboard/*` |

---

## Endpoints Públicos

### `GET /health`

Health check do serviço. Não requer autenticação.

**Response `200`**
```json
{
  "status": "ok",
  "service": "zdailyscan"
}
```

---

### `GET /scan/latest`

Retorna o resultado do scan mais recente armazenado.

**Response `200`** — objeto `ScanResult`
```json
{
  "scan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "date": "2026-06-03",
  "status": "completed",
  "total_scanned": 150,
  "total_viable": 12,
  "products": [
    {
      "product_id": "1005005678901234",
      "title": "USB-C Hub 7-in-1 Multiport Adapter",
      "score_total": 0.724183,
      "score_margem": 0.651200,
      "score_demanda_br": 0.800000,
      "score_oportunidade": 0.550000,
      "score_tendencia": 0.700000,
      "score_logistica": 1.0,
      "margin_brl": 45.50,
      "sell_price_suggestion_brl": 125.00,
      "viavel": true,
      "demand_count": 80,
      "import_cost_brl": 50.00
    }
  ]
}
```

**Response `404`** — nenhum scan encontrado
```json
{"detail": "No scans found"}
```

---

### `GET /scan/{date}`

Retorna o resultado do scan de uma data específica.

**Path params**

| Param | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `date` | string | `2026-06-03` | Data no formato `YYYY-MM-DD` |

**Response `200`** — objeto `ScanResult` (mesmo schema de `/scan/latest`)

**Response `404`**
```json
{"detail": "Scan not found"}
```

---

### `POST /scan/run`

Dispara um scan manual em background. Requer autenticação via API Key.

**Headers**

| Header | Obrigatório | Descrição |
|--------|-------------|-----------|
| `x-api-key` | Sim | Valor da env var `SCAN_API_KEY` |

**Response `200`**
```json
{
  "status": "started",
  "scan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Response `401`**
```json
{"detail": "Unauthorized"}
```

---

### `GET /scrapers/aliexpress`

Debug — faz scrape direto do AliExpress e retorna produtos brutos. Não requer autenticação.

**Query params**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `category` | string | `200003655` | ID de categoria AliExpress |
| `limit` | int | `20` | Número máximo de produtos |

**Categorias disponíveis**

| ID | Nome |
|----|------|
| `200003655` | Consumer Electronics |
| `100003070` | Phones & Telecom |
| `200000783` | Computer & Office |

**Response `200`**
```json
{
  "count": 2,
  "products": [
    {
      "product_id": "1005005678901234",
      "title": "USB-C Hub 7-in-1",
      "price_usd": 12.99,
      "sale_count_30d": 3200,
      "rating": 4.8,
      "freight_usd": 0.0,
      "image_url": "https://ae01.alicdn.com/kf/...",
      "product_url": "https://www.aliexpress.com/item/...",
      "category_id": "200003655"
    }
  ]
}
```

---

## Autenticação de Sessão

### `GET /login`

Página de login (HTML). Redireciona para `/dashboard` se já autenticado.

**Response `200`** — HTML

---

### `POST /login`

Autentica o usuário e cria session cookie.

Também disponível em `POST /auth/login`.

**Body** — `application/x-www-form-urlencoded`

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `username` | string | Sim |
| `password` | string | Sim |

**Response `303`** — redireciona para `/dashboard` com cookie `session` (sucesso)

**Response `401`** — página de login com mensagem de erro

---

### `GET /logout`

Invalida a sessão removendo o cookie.

**Response `303`** — redireciona para `/login`

---

## Dashboard (requer session cookie)

Todas as rotas abaixo exigem cookie `session` válido. Sem autenticação, retornam `303` para `/login`.

---

### `GET /dashboard`

Página principal do dashboard com lista de datas de scans disponíveis.

**Response `200`** — HTML

---

### `GET /dashboard/{date}`

Página de relatório de um scan por data.

**Path params**

| Param | Tipo | Exemplo |
|-------|------|---------|
| `date` | string | `2026-06-03` |

**Response `200`** — HTML

**Response `404`**
```json
{"detail": "Relatório não encontrado"}
```

---

### `GET /dashboard/explorer`

Página de exploração de produtos agregados de todos os scans.

**Query params**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `category_id` | string | — | Filtrar por ID de categoria |
| `min_score` | float | `0` | Score mínimo (0–100) |
| `sort_by` | string | `score` | `score` \| `price` \| `demand` |
| `limit` | int | `50` | Máximo de produtos retornados |

**Response `200`** — HTML

---

### `GET /dashboard/scanner`

Página com histórico de scans e controle de execução manual.

**Response `200`** — HTML

---

### `GET /dashboard/settings`

Página de configurações (cookies AliExpress, categorias, Telegram).

**Response `200`** — HTML

---

### `POST /dashboard/settings`

Atualiza os cookies de sessão AliExpress.

**Body** — `application/x-www-form-urlencoded`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `aliexpress_session_cookies` | string | Valor raw dos cookies |

**Response `303`** — redireciona para `/dashboard/settings`

---

### `POST /dashboard/settings/categories`

Atualiza as categorias ativas para o scan.

**Body** — `application/x-www-form-urlencoded`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `categories` | string[] | IDs de categorias a ativar |

**Response `303`** — redireciona para `/dashboard/settings`

---

### `POST /dashboard/settings/telegram-test`

Envia mensagem de teste ao Telegram configurado.

**Response `200`** — sucesso
```json
{"status": "ok"}
```

**Response `200`** — falha (HTTP 200 com body de erro)
```json
{"status": "error", "detail": "connection refused"}
```

---

## Dashboard — API JSON

### `GET /dashboard/products`

Lista todos os produtos agregados de todos os scans (JSON).

**Query params** — mesmos de `GET /dashboard/explorer`

**Response `200`**
```json
{
  "products": [
    {
      "product_id": "1005005678901234",
      "title": "USB-C Hub 7-in-1",
      "score_total": 0.724183,
      "score_margem": 0.651200,
      "score_demanda_br": 0.800000,
      "score_oportunidade": 0.550000,
      "score_tendencia": 0.700000,
      "score_logistica": 1.0,
      "margin_brl": 45.50,
      "sell_price_suggestion_brl": 125.00,
      "viavel": true,
      "demand_count": 80,
      "import_cost_brl": 50.00
    }
  ]
}
```

---

### `GET /dashboard/scans`

Lista todos os scans armazenados (JSON).

**Response `200`**
```json
{
  "scans": [
    {
      "scan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "date": "2026-06-03",
      "product_count": 12,
      "status": "completed"
    }
  ]
}
```

---

### `POST /dashboard/scan/trigger`

Dispara um scan manual em background (autenticado via session).

**Body** — `application/x-www-form-urlencoded`

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `categories` | string[] | — | IDs de categorias; vazio = todas ativas |

**Response `200`**
```json
{
  "scan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "running"
}
```

---

### `GET /dashboard/scan/{scan_id}/status`

Consulta o status de um scan em andamento ou concluído.

**Path params**

| Param | Tipo | Descrição |
|-------|------|-----------|
| `scan_id` | string (UUID) | ID retornado pelo trigger |

**Response `200`**
```json
{
  "scan_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "running",
  "product_count": 0
}
```

Valores possíveis de `status`: `running` | `completed` | `failed`

**Response `404`**
```json
{"detail": "scan_id not found"}
```

---

## Schemas

### `ScanResult`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `scan_id` | string (UUID) | Identificador único do scan |
| `date` | string | Data do scan (`YYYY-MM-DD`) |
| `status` | string | `completed` (default) |
| `total_scanned` | int | Total de produtos analisados |
| `total_viable` | int | Produtos com `viavel=true` |
| `products` | `ProductScore[]` | Top 20 produtos viáveis |

### `ProductScore`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `product_id` | string | ID do produto no AliExpress |
| `title` | string | Título do produto |
| `score_total` | float | Score composto (0–1) |
| `score_margem` | float | Score de margem de lucro (0–1) |
| `score_demanda_br` | float | Score de demanda no Brasil (0–1) |
| `score_oportunidade` | float | Score de oportunidade de mercado (0–1) |
| `score_tendencia` | float | Score de tendência de busca (0–1) |
| `score_logistica` | float | Score logístico pelo preço (0–1) |
| `margin_brl` | float | Margem em BRL (`avg_price_br - import_cost`) |
| `sell_price_suggestion_brl` | float | Preço sugerido de venda (`import_cost × 2.5`) |
| `viavel` | bool | `true` se `score_total >= 0.60` |
| `demand_count` | int | Número de resultados encontrados no ML |
| `import_cost_brl` | float | Custo total de importação em BRL |
