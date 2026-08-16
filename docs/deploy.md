# 🚀 Deploy — publicación del mapa

Esta guía explica cómo publicar el HTML en Cloudflare Pages para tener una **URL fija**, sin mantener la VPS encendida.

## ¿Por qué Cloudflare Pages?

| Característica | Cloudflare Pages | Tu VPS actual | GitHub Pages |
|---|---|---|---|
| URL fija | ✓ | Solo con dominio propio | ✓ |
| HTTPS automático | ✓ | Manual (Let's Encrypt) | ✓ |
| CDN global | ✓ | No | Limitado |
| Costo free tier | Ilimitado bandwidth | Ilimitado (tu VPS) | 100 GB/mes |
| Setup time | 5 min | 30 min | 5 min |
| Deploy automático | ✓ (en push a git) | No | ✓ |
| Dominio custom | ✓ (gratis) | ✓ (gratis con DDNS) | ✓ |

**Recomendación**: Cloudflare Pages + GitHub.

---

## Setup paso a paso

### 1. Subir el código a GitHub

```bash
cd /opt/sismos
git init
git add .
git commit -m "Initial: sismicidad Sudamérica + SST mensual"
git branch -M main
git remote add origin git@github.com:cfabian70/Fabian_sismos.git
git push -u origin main
```

### 2. Crear el proyecto en Cloudflare Pages

1. Logueate en https://dash.cloudflare.com/
2. `Workers & Pages` → `Create application` → `Pages` → `Connect to Git`
3. Selecciona el repo `cfabian70/Fabian_sismos`
4. Configuración de build:
   - **Framework preset**: None
   - **Build command**: (vacío)
   - **Build output directory**: `web`
5. Save and Deploy

### 3. URL fija

Cloudflare te asigna `https://fabian-sismos.pages.dev` automáticamente.

### 4. Dominio custom (opcional)

Si tenés `fabianvelasco.com`:
1. DNS section → Add record → CNAME `sismos` → `fabian-sismos.pages.dev`
2. Pages project → Custom domains → Add `sismos.fabianvelasco.com`

---

## Deploy automático

Cada `git push` a `main` redesplega automáticamente. Para actualizar:

```bash
# Workflow completo de actualización
cd /opt/sismos

# 1. Actualizar datos
python3 build/ingest.py --region sudamerica_ext --years 3

# 2. Regenerar HTML
python3 build/export_html.py --window 3

# 3. Commit y push
git add data/ web/index.html
git commit -m "Actualización $(date +%Y-%m-%d): $(sqlite3 data/sismos.db 'SELECT COUNT(*) FROM events') eventos"
git push
```

Cloudflare Pages detecta el push, redeploya en ~30s.

---

## Configurar cron job de actualización

```bash
# /etc/cron.d/sismos-update
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# Cada lunes 4 AM Ecuador (UTC-5 = 9 UTC)
0 9 * * 1 root cd /opt/sismos && python3 build/ingest.py --region sudamerica_ext --years 3 && python3 build/export_html.py --window 3 && git -A && git commit -m "weekly: $(date +%Y-%m-%d)" && git push origin main
```

---

## Verificación post-deploy

Una vez deployado:

1. Abrir la URL `https://fabian-sismos.pages.dev`
2. Verificar:
   - [ ] Mapa base (tiles) carga
   - [ ] Placas naranjas visibles
   - [ ] Ecuador en verde
   - [ ] Slider funcional
   - [ ] Play/pause
   - [ ] Popup en círculos
   - [ ] SST cambia al mover slider

---

## Alternativas

### Opción B: GitHub Pages

Más simple si no querés Cloudflare:

```bash
# Activar Pages en GitHub repo → Settings → Pages → Source: main, /web
# URL: https://cfabian70.github.io/Fabian_sismos/
```

Limitaciones: 100 GB bandwidth/mes, sin CDN global.

### Opción C: VPS propia (lo que ya tenés)

Si querés mantenerlo en `srv1469580`:

```bash
# Apache o nginx con certbot
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d sismos.tu-dominio.com
```

Más control, pero requiere mantenimiento.

---

## Troubleshooting

### El HTML no carga los tiles CartoDB

Causa: la URL de tiles cambió. Editar en `export_html.py`:
```python
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',...)
```

Alternativa OpenStreetMap (sin CDN):
```python
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',...)
```

### El HTML pesa más de 3 MB y el iPhone tarda

Ya está documentado en `docs/upgrade.md`. Solución rápida: subir `min-mag` a 5.0.

### GitHub Pages dice "no encontrado"

El path del output es `web/` y el archivo es `index.html`. Verificar config en Settings → Pages.

---

## Capacidad esperada

Cloudflare Pages free tier:
- Requests ilimitados
- Bandwidth ilimitado (CDN global)
- 500 builds/mes (sobra)
- 100 custom domains/proyecto

**No vas a tener problema de tráfico** salvo que se vuelva viral. Si pasa, configurás rate limiting en Cloudflare.