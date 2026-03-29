# EcoNodeX — MVP #1

Aplicación de escritorio local para gestión de datos ecológicos de comunidades de insectos e hidrobiología.
Sin cloud, sin autenticación, offline-first.

---

## Tabla de contenidos

1. [Requisitos](#requisitos)
2. [Instalación para desarrollo](#instalación-para-desarrollo)
3. [Ejecutar en modo desarrollo](#ejecutar-en-modo-desarrollo)
4. [Compilar el frontend](#compilar-el-frontend)
5. [Empaquetar con PyInstaller](#empaquetar-con-pyinstaller)
6. [Instalador Windows (Inno Setup)](#instalador-windows-inno-setup)
7. [Ejecutar tests](#ejecutar-tests)
8. [Estructura del proyecto](#estructura-del-proyecto)
9. [Flujo de subida de fotos por QR (LAN)](#flujo-de-subida-de-fotos-por-qr-lan)
10. [Exportaciones](#exportaciones)
11. [Análisis](#análisis)
12. [Notas de seguridad](#notas-de-seguridad)

---

## Requisitos

- **Python 3.11+**
- **Node.js 20+** (solo para desarrollo/build del frontend)
- Windows 10/11 (primario); compatible con macOS/Linux

---

## Instalación para desarrollo

```bash
# 1. Clonar / descomprimir el proyecto
cd EcoNodeX

# 2. Crear entorno virtual Python
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Instalar dependencias Python
pip install -r backend/requirements.txt

# 4. Instalar dependencias del frontend
cd frontend
npm install
cd ..
```

---

## Ejecutar en modo desarrollo

Abre **dos terminales**:

**Terminal 1 — Backend (FastAPI):**
```bash
# Desde la raíz del proyecto
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8765 --reload
```
El servidor inicia en `http://localhost:8765`.
El primer arranque crea automáticamente la BD (`~/EcoNodeX/econodex.db`) y siembra datos demo.

**Terminal 2 — Frontend (Vite dev server):**
```bash
cd frontend
npm run dev
```
Abre `http://localhost:5173` en el navegador.
El proxy de Vite redirige `/api/*` al backend en `:8765`.

---

## Compilar el frontend

```bash
cd frontend
npm run build
# El resultado queda en frontend/dist/
```

Después de compilar, el backend sirve el frontend directamente desde `frontend/dist/`.
Solo necesitas el **servidor backend**:

```bash
python main.py
# Abre automáticamente http://localhost:8765 en el navegador
```

---

## Empaquetar con PyInstaller

```bash
# 1. Compilar el frontend primero
cd frontend && npm run build && cd ..

# 2. Instalar PyInstaller
pip install pyinstaller

# 3. Generar el ejecutable
pyinstaller econodex.spec

# El resultado queda en dist/EcoNodeX/
# Ejecutable: dist/EcoNodeX/EcoNodeX.exe
```

El ejecutable:
- Incluye el frontend compilado como archivos de datos.
- Al iniciarse, arranca el servidor FastAPI en un hilo y abre el navegador en `http://localhost:8765`.
- Los datos del usuario se guardan en `%USERPROFILE%\EcoNodeX\` (o `~/EcoNodeX/`).

---

## Instalador Windows (Inno Setup)

1. Instala [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Genera primero el ejecutable con PyInstaller (paso anterior).
3. Compila el instalador:

```bash
# Desde la raíz del proyecto
iscc installer\setup.iss
# O abre el archivo .iss en el IDE de Inno Setup
```

El instalador queda en `dist\installer\EcoNodeX_Setup_v1.0.0.exe`.

---

## Ejecutar tests

```bash
# Desde la raíz del proyecto (con el entorno activado)
pip install pytest httpx
pytest backend/tests/ -v
```

Los tests usan una BD SQLite en memoria; no requieren servidor en ejecución.

---

## Estructura del proyecto

```
EcoNodeX/
├── main.py                    # Punto de entrada (PyInstaller + dev)
├── econodex.spec              # Spec de PyInstaller
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── config.py          # Configuración (puerto, rutas de datos)
│       ├── database.py        # SQLAlchemy + SQLite
│       ├── models.py          # Modelos ORM
│       ├── schemas.py         # Esquemas Pydantic v2
│       ├── main.py            # App FastAPI + rutas estáticas
│       ├── seed.py            # Datos demo (se carga al primer inicio)
│       ├── routers/           # Endpoints por entidad
│       │   ├── projects.py
│       │   ├── locations.py
│       │   ├── taxa.py        # Incluye merge de morphoespecies
│       │   ├── sampling.py    # Eventos + réplicas
│       │   ├── records.py     # Registros de ocurrencia
│       │   ├── methods.py     # Catálogo de métodos
│       │   ├── media.py       # Gestión de fotos
│       │   ├── analyses.py    # Índices y análisis
│       │   ├── exports.py     # CSV, Excel, DwC-A, ZIP
│       │   └── uploads.py     # QR + subida desde móvil
│       └── services/
│           ├── analyses_service.py  # Cálculos puros (Shannon, Simpson, etc.)
│           ├── export_service.py    # Generación de archivos de exportación
│           ├── media_service.py     # Thumbnails, EXIF
│           └── backup_service.py    # Copias de seguridad pre-merge
├── backend/tests/
│   ├── conftest.py
│   ├── test_analyses.py       # Tests unitarios de índices
│   ├── test_crud.py           # Tests de integración CRUD
│   ├── test_merge.py          # Tests del flujo de fusión de taxa
│   └── test_exports.py        # Tests de forma/estructura de exportaciones
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx
│       ├── api/client.js      # Cliente fetch para la API
│       ├── context/           # Contexto de proyecto activo
│       ├── hooks/             # useApi hook
│       ├── components/        # Layout, TreeView, Modal, PhotoGallery, etc.
│       └── pages/             # Una página por módulo de la app
├── installer/
│   └── setup.iss              # Script Inno Setup
└── README.md
```

---

## Flujo de subida de fotos por QR (LAN)

1. En la app de escritorio, ve a **Taxa** (o Localidades) y haz clic en **📷 Subir desde móvil**.
2. Aparece un código QR con la URL `http://<IP-LAN>:8765/upload?project=<id>`.
3. Escanea el QR con el móvil (misma red Wi-Fi).
4. En la página móvil:
   - Busca y selecciona el destino (taxón, localidad o réplica).
   - Selecciona una o más fotos.
   - Pulsa **Subir**.
5. Las fotos se guardan en la carpeta de fotos del proyecto, se generan thumbnails y se asocian automáticamente.
6. En la app de escritorio, las fotos aparecen en la galería de la entidad correspondiente.

> **Nota:** No hay autenticación. Úsalo solo en redes locales privadas.

---

## Exportaciones

| Formato         | Endpoint                        | Descripción                                    |
|-----------------|---------------------------------|------------------------------------------------|
| CSV por tabla   | `/api/exports/csv/<tabla>`      | Taxa, Localidades, Eventos, Réplicas, Registros, Métodos, Medios |
| Matriz abundancia | `/api/exports/csv/abundance-matrix` | Réplicas × Taxa con conteos               |
| Matriz presencia | `/api/exports/csv/presence-absence-matrix` | Réplicas × Taxa (0/1)            |
| Excel completo  | `/api/exports/excel`            | Todas las tablas en un libro .xlsx            |
| DwC-A           | `/api/exports/dwca`             | ZIP con event/occurrence/taxon/multimedia.csv + meta.xml |
| Proyecto ZIP    | `/api/exports/project`          | BD + CSVs + fotos (opcional)                  |
| Respaldo        | `POST /api/exports/backup`      | Copia de la BD en `~/EcoNodeX/backups/`       |

---

## Análisis

Los análisis se ejecutan desde la sección **Análisis** de la app.
Todos aceptan un **alcance**: proyecto completo, localidad (subárbol), o evento específico.

| Análisis                  | Descripción                                                       |
|---------------------------|-------------------------------------------------------------------|
| Riqueza (S)               | Número de taxa con ≥1 individuo; abundancia total (N)             |
| Shannon-Wiener (H')       | H' = −Σpᵢ·ln(pᵢ); incluye equitabilidad de Pielou (J')          |
| Simpson (D)               | D = 1 − Σnᵢ(nᵢ−1)/(N(N−1))                                      |
| Curva de acumulación      | Permutaciones aleatorias del orden de muestras; media ± DE       |
| Bray-Curtis (beta)        | Disimilitud por pares de réplicas; matriz + media                |
| Jaccard (beta)            | Disimilitud presencia/ausencia; matriz + media                   |

Los análisis devuelven resultados JSON + gráfico PNG (base64) cuando aplica.
Se puede exportar el JSON para procesamiento posterior en R.

---

## Notas de seguridad

- **Sin autenticación** en el flujo de carga de fotos por QR. Esto es por diseño para MVP #1.
- La página de subida (`/upload`) es accesible desde cualquier dispositivo en la misma red.
- **No exponer el servidor a Internet.** Úsalo solo en redes locales privadas.
- Los datos se almacenan localmente en `~/EcoNodeX/`. No se envían a ningún servidor externo.
- Los respaldos automáticos se crean antes de cada fusión de taxa en `~/EcoNodeX/backups/`.
