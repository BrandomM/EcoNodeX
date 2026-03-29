# EcoNodeX — Contexto para Claude Code

## ¿Qué es EcoNodeX?

Aplicación de escritorio local (offline-first) para gestión de datos ecológicos de comunidades de insectos e hidrobiología. Destinada a un único usuario en Windows. No hay cloud, no hay autenticación.

**Stack:**
- Backend: Python 3.11+ · FastAPI · SQLAlchemy 2 · SQLite
- Frontend: React 18 · Vite · Tailwind CSS · Recharts
- Empaquetado: PyInstaller (ejecutable) + Inno Setup (instalador)
- Puerto: `8765`
- BD: `~/EcoNodeX/econodex.db` (dev) o `<exe_dir>/data/econodex.db` (packaging)

## Arquitectura

```
main.py → uvicorn → backend/app/main.py (FastAPI)
                    ├── routers/  (CRUD + análisis + exports + upload)
                    ├── services/ (lógica de negocio pura)
                    └── frontend/dist/ (React SPA, servida como estáticos)
```

- En **desarrollo**: Vite en `:5173` proxea `/api` a `:8765`
- En **producción**: FastAPI sirve `frontend/dist/` + SPA catch-all

## Datos y modelos

Entidades principales: `Project → Location (árbol) / Taxon (árbol) / Method → SamplingEvent → Replicate → OccurrenceRecord`, `Media`, `MergeLog`

- Localidades y taxa son árboles auto-referenciales (parent_id nullable)
- Los alias de taxa se auto-generan si no se especifican
- Las fotos se almacenan en la carpeta local configurada por proyecto

## Flujos importantes

### Merge de taxa (destructivo)
1. Preview: `POST /api/taxa/merge/preview`
2. Execute: `POST /api/taxa/merge/execute` con `confirmation: "CONFIRMAR"`
3. Antes de ejecutar: backup automático en `~/EcoNodeX/backups/`
4. Reasigna records + media + children del taxón origen al destino
5. Log en tabla `merge_logs`

### Subida de fotos por QR (LAN)
1. Backend genera QR con URL `http://<IP>:8765/upload?project=<id>`
2. Página móvil `/upload` (React SPA, dark mode, sin auth)
3. `POST /api/upload/files` recibe `multipart/form-data` con: `project_id`, `linked_to_type`, `linked_to_id`, `files[]`
4. Se generan thumbnails en `<photos_root>/thumbnails/`

### DwC-A export
- Usa Event core (no Occurrence core)
- eventID: `E{event.id}` para eventos, `R{rep.id}` para réplicas (parentEventID = evento)
- occurrenceID: `OCC{record.id}`
- taxonID: `T{taxon.id}`

## Tests

```bash
pytest backend/tests/ -v
```

- `conftest.py`: BD in-memory + TestClient de FastAPI
- `test_analyses.py`: fórmulas matemáticas (Shannon, Simpson, Bray-Curtis, Jaccard)
- `test_crud.py`: CRUD integración
- `test_merge.py`: flujo completo de fusión de taxa
- `test_exports.py`: forma/estructura de archivos exportados

## Comandos frecuentes

```bash
# Dev: backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8765 --reload

# Dev: frontend
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Pruebas
pytest backend/tests/ -v

# Packaging
cd frontend && npm run build && cd ..
pyinstaller econodex.spec

# Instalador (requiere Inno Setup instalado)
iscc installer/setup.iss
```

## Convenciones de código

- Python: f-strings, type hints donde añaden claridad, sin tipado en funciones obvias
- FastAPI: `Depends(get_db)` en todos los endpoints, schemas Pydantic v2 (`model_dump`, `model_validate`)
- React: hooks, functional components, Tailwind (sin CSS modules), sin Redux
- Nombres en español en la UI; código en inglés
- IDs: enteros auto-increment (no UUID)
- Fechas: strings ISO (`YYYY-MM-DD`) para fechas, `datetime` UTC para timestamps

## Scope de MVP #1 (lo que NO está implementado)

- PWA / captura offline en móvil
- Sistema de plugins
- Campos personalizados
- Catálogo estático (Pokédex)
- Sincronización o backup en cloud
- Multi-usuario / autenticación
- Scripts R auto-generados
- Importación de proyectos desde ZIP (solo exportación)

## Notas importantes

- La seed se ejecuta automáticamente al primer inicio (si no hay proyectos en la BD)
- El servidor vincula a `0.0.0.0` para ser accesible en LAN (necesario para el flujo QR)
- Los respaldos se guardan en `~/EcoNodeX/backups/` como ZIPs con timestamp
- PyInstaller requiere `frontend/dist/` ya compilado antes de ejecutar `pyinstaller econodex.spec`
