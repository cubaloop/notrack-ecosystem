# PC Affiliate Worker (Antigravity Node)
## Integración NoTrack Ecosystem: Astra Codex (Cloud) <--> Antigravity (PC Worker)

### Propósito
Este módulo ejecuta las tareas pesadas y de extracción local en la máquina de David (PC), comunicándose con la capa Cloud desplegada por Astra Codex sin colisionar con `amazon-ui` ni componentes de servidor.

### Arquitectura de Integración
```
┌──────────────────────────────────────┐        ┌────────────────────────────────────────┐
│          CLOUD (Astra Codex)         │        │          PC WORKER (Antigravity)       │
│                                      │        │                                        │
│  - Tienda Pública (Render / Pages)   │  HTTP  │  - Trend Monitor (Google Trends RSS)   │
│  - Catálogo y Motor de Filtros       │<======>│  - Scraper de Tendencias (Playwright)  │
│  - Estadísticas y Tráfico            │  JSON  │  - Enriquecedor de URLs de Afiliado    │
│  - Supabase Dual-Layer               │        │  - Generador de Creativos & IG Copy    │
└──────────────────────────────────────┘        └────────────────────────────────────────┘
```

### Contrato de Datos (Schemas)
- **Tendencia (`TrendItem`):** `trend_id`, `keyword`, `category`, `volume_indicator`, `sources`, `detected_at`.
- **Producto Afiliado (`AffiliateProduct`):** `sku`, `title`, `price_aed`, `price_usd`, `affiliate_url`, `original_url`, `image_url`, `rating`, `review_count`, `trend_score`.
- **Publicación IG (`SocialCreative`):** `creative_id`, `product_sku`, `caption`, `hashtags`, `disclosure_text`, `image_asset_path`, `status`.

### Variables de Configuración (`config.json` o `.env`)
- `AMAZON_AFFILIATE_TAG`: Tag de asociado para inyección limpia en enlaces.
- `TARGET_MARKET`: `AE` (predeterminado) / `US`.
- `GROQ_API_KEY`: Para generación de copy de alta conversión vía Llama-3.3-70b.
- `TREND_POLL_INTERVAL_SEC`: Intervalo de sondeo de tendencias (default: 300s).
