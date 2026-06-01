# [TASK-107] fix: scan results stored in ephemeral filesystem

## Objetivo
`app/storage.py` usa `SCANS_DIR = Path("data/scans")` — hardcoded, efêmero no Railway.
A cada redeploy, todo o histórico é perdido. Migrar para path configurável via env var
`DATA_DIR` para suportar volume persistente Railway montado em `/data`.

## Pacote / Módulo
`app/storage.py` — substituir constante `SCANS_DIR` por função `_scans_dir()` que lê
`os.getenv("DATA_DIR", "data")` dinamicamente (a cada chamada, não na importação).

## Contratos

```python
# Função privada — computa path a cada chamada para respeitar mudanças de env
def _scans_dir() -> Path:
    return Path(os.getenv("DATA_DIR", "data")) / "scans"

# Assinaturas públicas — inalteradas
def save_scan(result: ScanResult) -> Path: ...
def load_scan(date_str: str) -> ScanResult | None: ...
def get_latest_scan() -> ScanResult | None: ...
```

## Detalhes de Implementação
- Remover `SCANS_DIR = Path("data/scans")` (módulo-level constante hardcoded)
- Adicionar `_scans_dir()` — chama `os.getenv("DATA_DIR", "data")` a cada invocação
- Usar `_scans_dir()` internamente em todas as funções (nunca referência ao módulo-level var)
- Atualizar `tests/test_pipeline.py::test_scan_persisted_to_json` —
  `monkeypatch.setattr(storage_module, "SCANS_DIR", ...)` → `monkeypatch.setenv("DATA_DIR", ...)`
- Adicionar `DATA_DIR=data` em `.env.example`
- Railway: montar volume em `/data` e setar `DATA_DIR=/data`

## Tasks
- [x] Spec criada
- [x] RED: escrever tests/test_issue107_persistent_storage.py (falham)
- [x] GREEN: implementar _scans_dir() em app/storage.py
- [x] REFACTOR: atualizar test_pipeline.py + .env.example
- [x] Verify: pytest tests/ -x — 248 passed
- [x] Archive

## Critérios de Verificação
```bash
pytest tests/ -k "test_scan_persists_after_restart" -x  # verifica DATA_DIR no path do arquivo
pytest tests/ -k "test_scan_latest_persists" -x         # get_latest_scan lê de DATA_DIR
pytest tests/ -x                                         # suite completa verde
```
