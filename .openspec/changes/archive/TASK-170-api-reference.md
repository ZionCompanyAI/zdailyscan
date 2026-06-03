# [TASK-170] docs: criar docs/api-reference.md — referência completa dos endpoints

## Objetivo
Criar arquivo `docs/api-reference.md` documentando todos os endpoints HTTP do ZDailyScan com método, rota, autenticação, parâmetros e exemplos de response.

## Pacote / Módulo
- `docs/api-reference.md` — novo arquivo (sem código de produção)

## Contratos (Referências Técnicas)

Endpoints identificados em `app/main.py` e `app/routers/`:

| Método | Rota | Auth |
|--------|------|------|
| GET | / | — |
| GET | /health | — |
| GET | /scan/latest | — |
| GET | /scan/{date} | — |
| POST | /scan/run | x-api-key header |
| GET | /scrapers/aliexpress | — |
| GET | /login | — |
| POST | /login | — |
| POST | /auth/login | — |
| GET | /logout | session cookie |
| GET | /dashboard | session cookie |
| GET | /dashboard/explorer | session cookie |
| GET | /dashboard/scanner | session cookie |
| GET | /dashboard/settings | session cookie |
| POST | /dashboard/settings | session cookie |
| POST | /dashboard/settings/categories | session cookie |
| POST | /dashboard/settings/telegram-test | session cookie |
| GET | /dashboard/products | session cookie |
| GET | /dashboard/scans | session cookie |
| POST | /dashboard/scan/trigger | session cookie |
| GET | /dashboard/scan/{scan_id}/status | session cookie |
| POST | /dashboard/scan | session cookie (legacy) |
| GET | /dashboard/{date} | session cookie |

## Tasks
- [x] Criar `docs/api-reference.md` com todos os endpoints
- [x] Cada endpoint com método, rota, auth, params, response example
- [x] Verificar critérios de aceite

## Critérios de Verificação
```bash
test -f docs/api-reference.md && echo "OK"
grep -n "scan/latest\|scan/run\|x-api-key" docs/api-reference.md | head -5
```
