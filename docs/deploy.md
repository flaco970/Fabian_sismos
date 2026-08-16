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

**Recomendación**: Cloudflare Pages + GitHub (lo que ya tenemos).

---

## Setup paso a paso

### 1. Repo GitHub (ya hecho ✓)

```bash
# Repo: https://github.com/flaco970/Fabian_sismos
# Branch: main
# Contenido: 55 archivos, 1 MB
# HTML servido desde: web/index.html
```

### 2. Conectar a Cloudflare Pages (5 min en tu iPhone)

1. Abrí `https://dash.cloudflare.com/` en Chrome del iPhone
2. Si no tenés cuenta, creá una (gratis)
3. En el menú lateral: **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
4. Conectá GitHub (autorizá a Cloudflare a leer tus repos)
5. Seleccioná **flaco970/Fabian_sismos**
6. Configuración de build:
   - **Framework preset**: `None`
   - **Build command**: *(dejar vacío)*
   - **Build output directory**: `web`
7. Click **Save and Deploy**

### 3. URL fija

Cloudflare te asigna automáticamente:
```
https://fabian-sismos.pages.dev
```

(si el nombre ya está tomado por otro usuario, variará: `fabian-sismos-abc.pages.dev`)

### 4. Dominio custom (opcional, 10 min más)

Si querés `sismos.fabianvelasco.com`:

**En Cloudflare**:
1. Pages project → **Custom domains** → **Set up a custom domain**
2. Ingresá `sismos.fabianvelasco.com`
3. Cloudflare te da un CNAME target

**En tu DNS** (si el dominio está en Cloudflare, automático):
- Tipo: `CNAME`
- Nombre: `sismos`
- Destino: `fabian-sismos.pages.dev`

**Si el dominio está en otro registrador** (GoDaddy, Namecheap, etc.):
- Agregá un CNAME `sismos` → `fabian-sismos.pages.dev`
- Esperá 24-48h para propagación

---

## Deploy automático

Cada `git push` a `main` redesplega automáticamente. Para actualizar:

```bash
cd /opt/sismos

# 1. Actualizar datos
python3 build/ingest.py --region sudamerica_ext --years 3

# 2. Regenerar HTML
python3 build/export_html.py --window 3

# 3. Commit y push
git add data/ web/index.html
git commit -m "Actualización $(date +%Y-%m-%d): $(sqlite3 data/sismos.db 'SELECT COUNT(*) FROM events') eventos"
git push origin main
```

Cloudflare Pages detecta el push, redeploya en ~30s, URL queda actualizada.

---

## Configurar cron job de actualización

```bash
# /etc/cron.d/sismos-update
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# Cada lunes 4 AM Ecuador (UTC-5 = 9 UTC)
0 9 * * 1 root cd /opt/sismos && /opt/sismos/scripts/update.sh && git push origin main
```

El script `scripts/update.sh` ya hace ingesta + export + commit automáticamente.

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

Si algo falla, revisar:
- Cloudflare dashboard → Pages → fabian-sismos → Deployments → Logs

---

## Alternativas

### Opción B: GitHub Pages (más simple)

Si no querés Cloudflare, en GitHub:
1. Repo → Settings → Pages
2. Source: **Deploy from a branch** → `main` → `/web`
3. Save

URL: `https://flaco970.github.io/Fabian_sismos/`

Limitaciones: 100 GB bandwidth/mes, sin CDN global, latencia mayor en Asia/Europa.

### Opción C: Mantener el túnel `trycloudflare.com` actual

URL temporal: `https://pipeline-pick-mid-payments.trycloudflare.com`

Ventajas: cero setup
Desventajas: cambia cada vez que reinicio `cloudflared`, no tiene HTTPS confiable a largo plazo, depende del VPS encendido

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

### Cloudflare Pages: "Build failed"

Si configuraste build command vacío y solo "web" como output, debería funcionar. Si pusiste algo en build command, sacalo.

---

## Capacidad esperada

Cloudflare Pages free tier:
- Requests ilimitados
- Bandwidth ilimitado (CDN global)
- 500 builds/mes (sobra)
- 100 custom domains/proyecto

**No vas a tener problema de tráfico** salvo que se vuelva viral. Si pasa, configurás rate limiting en Cloudflare.

---

## Comparación con lo que tenés HOY

| | Hoy (túnel trycloudflare) | Después (Cloudflare Pages) |
|---|---|---|
| URL | `pipeline-pick-mid-payments.trycloudflare.com` | `fabian-sismos.pages.dev` |
| Estable | No (cambia al reiniciar) | Sí |
| HTTPS | Sí (Cloudflare) | Sí |
| VPS encendida | Requerida | NO requerida |
| Costo | $0 | $0 |
| Latencia Ecuador | ~150 ms | ~30 ms (CDN cercano) |
| Deploy automático | No | Sí (en git push) |