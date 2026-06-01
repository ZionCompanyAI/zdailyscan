# [TASK-108] Infra: Deploy ML search HTTP proxy on toni-OC01

## Objetivo
Criar um proxy HTTP em toni-OC01 que encaminha requisições de busca ao Mercado Livre
(`api.mercadolibre.com/sites/MLB/search`), contornando o bloqueio de IPs do Railway
pelo PolicyAgent da ML. O zdailyscan no Railway usará `ML_SEARCH_PROXY_URL` para
rotear todas as buscas ML através deste proxy.

## Pacote / Módulo
- `/opt/ml-proxy/proxy.py` — daemon Python3 na máquina toni-OC01
- `/etc/systemd/system/ml-proxy.service` — serviço systemd
- Railway env var `ML_SEARCH_PROXY_URL` no projeto zdailyscan
- `.openspec/` — spec e progress atualizado

## Contratos

```
GET http://localhost:9001/?q=<query>&limit=<n>
→ 200 JSON: { results: [...], paging: { total: N, ... } }
→ 500 JSON: { error: "..." }

Auth: proxy busca token via auth-bus GET /tokens/mercadolibre
Porta: 9001 (0.0.0.0)
```

## Tasks

- [x] Criar /opt/ml-proxy/proxy.py com ProxyHandler + get_ml_token via auth-bus
- [x] Criar /etc/systemd/system/ml-proxy.service com AUTH_BUS_API_KEY injetado
- [x] systemctl daemon-reload + enable + start
- [x] Abrir porta 9001 no ufw (se ativo — ufw inativo em OC01, skip)
- [~] Verificar proxy respondendo localmente — BLOQUEADO: OC01 IP (177.9.43.183 Claro Brasil) também bloqueado pelo ML CloudFront WAF para /sites/MLB/*
- [x] Obter IP público: 177.9.43.183
- [~] Setar ML_SEARCH_PROXY_URL no Railway — PULADO: proxy não funcional, configurar pioraria (latência extra sem benefício)
- [~] Redeploy / validação — PULADO: sem proxy funcional
- [x] Postar comentário na issue com findings e alternativas sugeridas

## Critérios de Verificação
```bash
# 1. Proxy respondendo com resultados reais
curl -sf "http://localhost:9001/?q=celular&limit=3" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); assert len(d.get('results',[])) > 0"

# 2. Serviço ativo
systemctl is-active ml-proxy | grep -q active

# 3. Env var configurada no Railway
# ML_SEARCH_PROXY_URL deve estar presente com valor http://<PUBLIC_IP>:9001
```
