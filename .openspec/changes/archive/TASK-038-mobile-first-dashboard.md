# [TASK-038] Mobile-first redesign: todas as páginas do dashboard

## Objetivo
Refatorar todos os templates do dashboard para mobile-first, mantendo o design
Impeccable MBZ (OKLCH tokens, Inter font, dark theme). Issue #38.

## Pacote / Módulo
- `app/templates/base.html`
- `app/templates/login.html`
- `app/templates/dashboard.html`
- `app/templates/explorer.html`
- `app/templates/scanner.html`
- `app/templates/settings.html`

## Contratos (Referências Técnicas)

```
Viewport meta obrigatório:
  <meta name="viewport" content="width=device-width, initial-scale=1">

Navegação:
  - Mobile (<768px): bottom-nav fixo com ícones+label, class="bottom-nav"
  - Desktop (≥768px): top nav horizontal, class="top-nav"
  - main: padding-bottom suficiente em mobile para não ocultar conteúdo sob bottom-nav

Input font-size: mínimo 16px em todos os campos (evita zoom iOS)

Tap targets: mínimo 44px height em todos os botões

Grids responsivos (explorer):
  - Mobile: 1 coluna
  - Tablet (≥600px): 2 colunas
  - Desktop (≥900px): 3 colunas

Filtros (explorer): envolver em <details><summary> para colapsar em mobile

Scanner tabela → cards mobile: media query @media (max-width: 599px)
  esconde <table>, mostra .scan-cards com cards individuais

Settings: grid-template-columns: 1fr em mobile, auto-fill em desktop
```

## Detalhes de Implementação
- CSS puro com var(--color-*) e media queries — sem Bootstrap, sem CDN externo
- OKLCH tokens mantidos em todas as páginas
- Bottom nav: links para Dashboard, Explorer, Scanner, Settings com texto de rótulo
- Top nav existente oculto em mobile via @media (max-width: 767px)

## Tasks (checklist de execução)
- [x] Escrever testes RED em tests/test_mobile_first.py
- [x] Confirmar falha dos testes RED
- [x] Refatorar base.html: bottom-nav mobile, top-nav desktop, padding-bottom main
- [x] Refatorar login.html: font-size 16px nos inputs, button min-height 44px
- [x] Refatorar explorer.html: filtros em <details>, grid 1/2/3 colunas
- [x] Refatorar scanner.html: btn full-width mobile, tabela→cards mobile
- [x] Refatorar settings.html: 1 coluna mobile
- [x] Refatorar dashboard.html: grid responsivo, btn full-width mobile
- [x] Confirmar todos os testes passando (RED→GREEN)
- [x] Archive

## Critérios de Verificação
- test_mobile_first.py todos passam
- tests/test_dashboard.py todos passam
- tests/test_dashboard_phase2.py todos passam
