# Gym Log Web — Proyecto Refactorizado

Aplicación web de seguimiento de entrenamientos construida con Python, Flask
y SQLite. Permite crear sesiones de entrenamiento, agregar ejercicios a
cada sesión y registrar series (peso y repeticiones).

Este repositorio corresponde a la refactorización, contenedorización,
pruebas automatizadas (unitarias y E2E) y despliegue continuo de la
versión original monolítica del proyecto, desarrollada en 6 fases
incrementales.

---

## Fase 1 — Ingeniería inversa y refactorización

### Arquitectura legada (original)

```text
PROYECTO FINAL (GYM APP)/
├── app.py      # 241 líneas: TODAS las rutas, la conexión a la BD
│                 y el arranque de la app en un solo archivo
├── db.py        # Todas las queries SQL de las 3 entidades mezcladas
├── logic.py      # Validaciones de formularios
├── static/
└── templates/
```

Problemas identificados en la ingeniería inversa:

- **Un único archivo `app.py` monolítico**: 15 rutas, lógica de negocio
  (búsqueda "by id" recorriendo listas en Python) y configuración de la
  app conviviendo en el mismo módulo.
- **Conexión a base de datos global**: `conn = sqlite3.connect(...)` se
  abría una sola vez al importar `app.py` y se reutilizaba en todas las
  peticiones — no es seguro con un servidor multi-worker (Gunicorn) y
  hace imposible aislar una base de datos de pruebas.
- **`db.py` mezclaba las 3 entidades** (sessions, exercises, sets) sin
  ninguna separación.
- **Sin variables de entorno**: la ruta de la base de datos y el modo
  debug estaban *hardcodeados*.
- **Sin pruebas automatizadas** y **sin capa de API JSON**.
- **`get_session_by_id` / `get_exercise_by_id`** recorrían en Python
  *todas* las filas devueltas por la base de datos en vez de filtrar con
  `WHERE id = ?` en SQL.

### Arquitectura nueva (refactorizada)

```text
gym_log_web/
├── app.py                 # Application factory: crea y conecta todo
├── config.py               # Config por entorno (dev/testing/production)
├── database.py              # Ciclo de vida de la conexión SQLite (Flask g)
├── services.py               # Validaciones puras (sin Flask, sin BD)
├── models/                   # Capa de datos, un módulo por entidad
│   ├── sessions.py
│   ├── exercises.py
│   └── sets.py
├── blueprints/                # Rutas agrupadas por dominio (Blueprints)
│   ├── main.py                 # "/"
│   ├── sessions.py              # "/sessions", "/add-session"...
│   ├── exercises.py              # "/sessions/<id>/exercises"...
│   ├── sets.py                    # "/sessions/.../add-set"...
│   └── api.py                      # "/api/..." — nuevos endpoints JSON
├── templates/, static/               # Sin cambios (compatibilidad total)
├── tests/                              # Suite de pytest (Fase 3)
├── Dockerfile, .dockerignore            # Contenedorización (Fase 2)
├── requirements.txt, requirements-dev.txt
└── pytest.ini, .coveragerc
```

Cambios clave:

| Aspecto | Legado | Refactorizado |
|---|---|---|
| Rutas | 1 archivo con 15 rutas | 5 Blueprints agrupados por dominio |
| Conexión BD | Global, abierta una vez | Por request, vía `flask.g`, cerrada en teardown |
| Configuración | Hardcodeada en `app.py` | Centralizada en `config.py`, leída de variables de entorno |
| Datos | `db.py` con las 3 entidades mezcladas | `models/sessions.py`, `models/exercises.py`, `models/sets.py` |
| Búsqueda por id | Loop en Python sobre todas las filas | `SELECT ... WHERE id = ?` en SQL |
| Recurso no encontrado | Texto plano, status 200 | Texto plano, status **404** |
| API | Solo HTML | HTML + **API JSON** en `/api/*` |
| Pruebas | Ninguna | 42 pruebas con pytest (Fase 3) + 4 E2E con Selenium (Fase 4) |
| Despliegue | `python app.py` | Docker multi-etapa + Gunicorn, CI/CD y producción en la nube (Fases 2, 5 y 6) |

Las plantillas (`templates/*.html`) y los estilos (`static/style.css`) se
mantuvieron **sin modificaciones** porque usan URLs fijas (no `url_for`
de endpoint), así que los Blueprints se registraron con las mismas
rutas exactas del sistema legado — cero cambios visuales, cero rutura
de compatibilidad.

### Rutas HTML (sin cambios de URL respecto al legado)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard con totales |
| GET | `/sessions` | Listado de sesiones |
| GET/POST | `/add-session` | Crear sesión |
| GET | `/sessions/<id>` | Detalle de sesión |
| POST | `/sessions/<id>/delete` | Eliminar sesión |
| GET/POST | `/sessions/<id>/add-exercise` | Agregar ejercicio |
| GET | `/sessions/<id>/exercises/<eid>` | Detalle de ejercicio |
| POST | `/sessions/<id>/exercises/<eid>/delete` | Eliminar ejercicio |
| GET/POST | `/sessions/<id>/exercises/<eid>/add-set` | Agregar set |
| POST | `/sessions/<id>/exercises/<eid>/sets/<sid>/delete` | Eliminar set |

### Endpoints JSON (nuevos, agregados en la modernización)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/sessions` | Listado de sesiones en JSON |
| POST | `/api/sessions` | Crear sesión `{ "name": "..." }` |
| GET | `/api/sessions/<id>` | Detalle de sesión + ejercicios |
| GET | `/api/sessions/<id>/exercises` | Ejercicios de una sesión |
| GET | `/api/exercises/<id>/sets` | Sets de un ejercicio |
| POST | `/api/exercises/<id>/sets` | Crear set `{ "weight": .., "reps": .. }` |
| GET | `/api/stats` | Totales del dashboard |
| GET | `/api/health` | Diagnóstico de salud: estado de la app y de la BD (Fase 6) |

---

## Fase 2 — Inmutabilidad y contenedorización local (Docker)

### Archivos incluidos

- **`Dockerfile`** — build multi-etapa:
  1. **`builder`**: instala dependencias de `requirements.txt` con
     `pip install --user` sobre `python:3.12-slim`.
  2. **`runtime`**: imagen `python:3.12-slim` limpia que solo copia los
     paquetes instalados y el código fuente (sin herramientas de build),
     corre como **usuario no-root**, y arranca con **Gunicorn** (servidor
     WSGI de producción) en vez del servidor de desarrollo de Flask.
- **`.dockerignore`** — excluye `venv/`, `__pycache__/`, `tests/`,
  `gym.db`, `screenshots/`, `.git`, reportes de cobertura, etc., para
  mantener el contexto de build y la imagen final livianos.

### Cómo construir y correr la imagen localmente

```bash
# 1. Construir la imagen
docker build -t gym-log-web .

# 2. Correr el contenedor, publicando el puerto 5000
docker run --rm -p 5000:5000 --name gym-log-web gym-log-web

# 3. Verificar
curl http://localhost:5000/api/stats
```

Luego abrir `http://localhost:5000` en el navegador.

> **Evidencia de funcionamiento (pendiente de agregar por el alumno):**
> agrega aquí la captura de pantalla de Docker Desktop mostrando la
> imagen `gym-log-web` construida con éxito y el contenedor corriendo
> en el puerto 5000 (por ejemplo `docker-evidence.png`), ya que requiere
> tener Docker Desktop instalado en la máquina local.

---

## Fase 3 — Pruebas unitarias y cobertura (Pytest)

### Suite de pruebas

42 pruebas unitarias en `tests/`, organizadas por responsabilidad:

| Archivo | Qué cubre | # tests |
|---|---|---|
| `test_main.py` | Ruta `/` (dashboard) | 3 |
| `test_sessions.py` | Rutas HTML de sesiones | 8 |
| `test_exercises.py` | Rutas HTML de ejercicios | 7 |
| `test_sets.py` | Rutas HTML de sets | 5 |
| `test_api.py` | Endpoints JSON de `/api/*` | 9 |
| `test_health.py` | Endpoint de monitoreo `/api/health` (OK, commit, fallo de BD → 503) | 3 |
| `test_services.py` | Validaciones puras (`parse_weight`, `parse_positive_int`) | 7 |

Cada test corre contra una base de datos SQLite temporal y aislada
(`tempfile.mkstemp()`), creada y destruida por el fixture `app` en
`tests/conftest.py`, así que las pruebas no comparten estado ni tocan
`gym.db`.

### Cómo correr las pruebas y ver la cobertura

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest.ini` ya configura `pytest-cov` para medir cobertura de todo el
proyecto y **fallar si baja del 80%** (`--cov-fail-under=80`).

### Resultado obtenido

```text
42 passed in 0.87s

Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
app.py                       24      0   100%
blueprints/__init__.py        0      0   100%
blueprints/api.py            74      5    93%   104-112
blueprints/exercises.py      29      0   100%
blueprints/main.py           17      0   100%
blueprints/sessions.py       35      2    94%   37-38
blueprints/sets.py           23      1    96%   17
config.py                    20      0   100%
database.py                  21      0   100%
models/__init__.py            0      0   100%
models/exercises.py          21      2    90%   46-47
models/sessions.py           23      1    96%   49
models/sets.py               14      0   100%
services.py                  16      0   100%
-------------------------------------------------------
TOTAL                       317     11    97%
Required test coverage of 80% reached. Total coverage: 96.53%
```

> Reporte completo disponible en `pytest_coverage_report.txt`.

---

## Fase 4 — Pruebas de interacción real (Selenium E2E)

### Enfoque

El proyecto no tiene login (no existía en la app original), así que los
4 flujos E2E cubren el resto de lo pedido — **creación, navegación,
búsqueda y verificación de registros** — de punta a punta contra un
servidor Flask real corriendo en background (no mocks, no llamadas
directas a la BD):

| Test | Flujo simulado |
|---|---|
| `test_create_session_appears_in_sessions_list` | Crear sesión → verificar que aparece en `/sessions` |
| `test_create_exercise_appears_in_session_detail` | Crear sesión → entrar → agregar ejercicio → verificar que aparece |
| `test_add_set_appears_in_exercise_detail_and_updates_dashboard` | Crear sesión → ejercicio → set → verificar el set Y que el contador del dashboard (`/`) se actualizó |
| `test_delete_session_removes_it_from_list` | Crear sesión → eliminarla (aceptando el `confirm()` del navegador) → verificar que ya no aparece en la búsqueda |

### Nota sobre el botón Delete

El CSS de la app oculta el botón *Delete* de cada tarjeta hasta que el
usuario pasa el mouse encima (`.card .danger-button { visibility: hidden }`).
La prueba E2E hace *hover* sobre la tarjeta antes de hacer clic, igual que
lo haría una persona real.

### Estructura

```text
e2e/
├── conftest.py         # live_server (Flask real en un thread) + driver (Chrome)
├── pages.py              # Page Object Model: un objeto por página
├── pytest.ini            # config propia (no hereda el --cov de las pruebas unitarias)
└── test_e2e_flows.py       # los 4 tests, escritos como flujos de usuario
```

Se usa el patrón **Page Object Model**: los tests no conocen selectores
CSS/XPath, solo llaman métodos como `sessions_page.open_session("Leg Day")`.
Si el HTML cambia, solo se actualiza `pages.py`.

`conftest.py` levanta la app real (`create_app`, la misma factory que usa
producción) en un thread contra un puerto libre y una base de datos
SQLite temporal — Selenium interactúa con un servidor real, igual que un
usuario real.

### Cómo ejecutarlo en modo visual (evidencia local requerida)

```bash
pip install -r requirements-e2e.txt
# Chrome debe estar instalado; Selenium 4.15+ descarga el chromedriver
# correcto automáticamente (Selenium Manager), no hace falta instalarlo aparte.

cd e2e
pytest -v
```

Por defecto **no** corre en headless — vas a ver la ventana de Chrome
abrirse y ejecutar cada paso en tiempo real. Esa ejecución con las 4
pruebas en verde es la evidencia que pide la Fase 4 (captura de pantalla
o grabación de la terminal + la ventana del navegador).

> Para correrlo headless (lo que hace el pipeline de CI, que no tiene
> pantalla), usa `E2E_HEADLESS=1 pytest -v`.

---

## Fase 5 — Pipeline de integración continua (GitHub Actions)

### Archivo del pipeline

`.github/workflows/ci.yml` — se dispara en cada `push`/`pull_request` a
`main`, con 4 jobs encadenados:

```text
unit-tests  ──┬──►  e2e-tests
              └──►  docker-build  ──►  security-scan
```

| Job | Qué hace |
|---|---|
| **unit-tests** | Instala `requirements-dev.txt` y corre `pytest --cov` con el mismo umbral de 80% de la Fase 3. Sube `coverage.xml` como artefacto. |
| **e2e-tests** | Usa el Google Chrome que ya trae el runner de GitHub (Selenium Manager descarga el chromedriver compatible) y corre la suite de Selenium de la Fase 4 en modo headless (`E2E_HEADLESS=1`). |
| **docker-build** | Construye la imagen con el `Dockerfile` de la Fase 2, la corre, y hace un *smoke test* con `curl` contra `/api/health` antes de continuar. Guarda la imagen como artefacto para el siguiente job. |
| **security-scan** | Corre `pip-audit` sobre `requirements.txt` (vulnerabilidades de dependencias Python) y `Trivy` sobre la imagen Docker construida (vulnerabilidades del sistema operativo/paquetes del contenedor). Ambos reportes se suben como artefactos descargables del run. |

Los reportes de seguridad no fallan el pipeline (`exit-code: "0"` en
Trivy, `|| true` en pip-audit) — son informativos, para que el equipo los
revise sin bloquear cada despliegue por una vulnerabilidad de severidad
baja. Se puede endurecer eso más adelante si se requiere.

### Cómo activarlo

1. Sube el proyecto (con la carpeta `.github/workflows/` incluida) a tu
   repositorio de GitHub.
2. Ve a la pestaña **Actions** del repositorio — el pipeline corre
   automáticamente en el primer `push` a `main`.
3. El **enlace al historial de ejecuciones** que pide el entregable es
   la URL de esa pestaña:
   `https://github.com/<tu-usuario>/<tu-repo>/actions`
   (o el link a un run específico una vez que todos los jobs queden en
   verde ✅, por ejemplo `.../actions/runs/<id>`).

---

## Fase 6 — Entrega, despliegue de valor y monitoreo

### Endpoint de diagnóstico `/api/health`

`GET /api/health` responde en tiempo real si la aplicación **y su base de
datos** están sanas:

```json
{"commit":"3f9c2ab...","database":"ok","status":"ok","timestamp":"2026-10-27T16:33:23+00:00","uptime_seconds":2}
```

| Campo | Significado |
|---|---|
| `status` | `ok` si todo funciona, `degraded` si la BD falla |
| `database` | Resultado de un `SELECT 1` contra SQLite |
| `commit` | Commit de Git que está corriendo (lo inyecta la plataforma) — sirve para comprobar que un despliegue llegó a producción |
| `uptime_seconds` | Segundos desde que arrancó el proceso |

Devuelve **HTTP 200** cuando está sano y **HTTP 503** cuando no, así la
plataforma puede dejar de enviarle tráfico. Se usa en tres lugares:
el `HEALTHCHECK` del Dockerfile, el *smoke test* del pipeline y el
`healthCheckPath` de Render.

### Producción en la nube (Render)

El archivo `render.yaml` describe el servicio como código (Blueprint):
construye el `Dockerfile` del repositorio, usa `/api/health` como
chequeo de salud y tiene `autoDeployTrigger: checksPass`, es decir,
**Render despliega un commit únicamente cuando los checks de GitHub
Actions de ese commit pasan** (pruebas unitarias, Selenium, build de
Docker y reportes de seguridad).

Configuración inicial (una sola vez):

1. Entra a [render.com](https://render.com) e inicia sesión con tu cuenta de GitHub.
2. **New + → Blueprint** → elige este repositorio → **Apply**. Render lee
   `render.yaml`, construye la imagen y publica el servicio.
3. Copia la URL pública (algo como `https://gym-log-web.onrender.com`) —
   **ese es el enlace de producción que se entrega al profesor**.
4. Comprueba `https://<tu-url>/api/health`.
5. (Opcional, recomendado para la demo) En GitHub: **Settings → Secrets and
   variables → Actions → Variables → New repository variable** con nombre
   `PRODUCTION_URL` y valor tu URL. El workflow
   `.github/workflows/production-health.yml` esperará entonces a que
   producción reporte el commit recién subido y lo mostrará en verde.

> **Limitaciones del plan gratuito:** el servicio se duerme tras unos
> minutos sin tráfico (la primera petición tarda ~1 minuto en despertar;
> ábrelo unos minutos antes de presentar) y el disco es efímero, por lo
> que la base SQLite se reinicia en cada despliegue. Para datos
> persistentes habría que añadir un disco o migrar a PostgreSQL.

### Guion de la presentación en vivo

1. **Mostrar producción:** abrir la URL pública, crear una sesión, un
   ejercicio y un set; abrir `/api/health`.
2. **Cambio menor en vivo:** por ejemplo, cambiar la frase que dice
   *"A simple workout tracker..."* en `templates/index.html` (no cambies
   el título *Gym Log Web*: una prueba unitaria lo verifica), y luego:
   ```bash
   git add .
   git commit -m "feat: cambio de demostración"
   git push
   ```
3. **Proyectar GitHub → Actions:** el pipeline arranca solo y ejecuta,
   en orden, Pytest → Selenium → Docker build → reportes de seguridad.
4. **Producción se actualiza sola:** cuando los checks pasan, Render
   despliega; al refrescar la URL pública aparece el cambio y
   `/api/health` muestra el nuevo `commit`.

---

## Correr la aplicación localmente (sin Docker)

```bash
pip install -r requirements.txt
python app.py
```

Luego abrir `http://127.0.0.1:5000`.

## Stack

- Python 3.12 / Flask 3.1
- SQLite
- Gunicorn (producción / Docker)
- Pytest + pytest-cov (pruebas unitarias y cobertura — Fase 3)
- Selenium 4 + Page Object Model (pruebas E2E — Fase 4)
- Docker (multi-stage build — Fase 2)
- GitHub Actions + pip-audit + Trivy (CI/CD y seguridad — Fase 5)
- Render + `render.yaml` + `/api/health` (producción y monitoreo — Fase 6)

## Autor

James Charron
