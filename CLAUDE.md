# CLAUDE.md

Guía para Claude Code en este repositorio. Contiene solo lo que aplica a
cualquier tarea; el detalle vive en los documentos referenciados.

## Fuentes de verdad

- **Comportamiento observable de la API**: `docs/contrato-api.md`. No se
  implementa ni modifica un endpoint sin leerlo antes.
- **Decisiones de ingeniería del equipo** (base de datos, migraciones,
  disciplina de pruebas, datos locales): `docs/decisiones-ingenieria.md`.
- **Comandos canónicos**: `README.md`.
- **Mapa de hechos vs. inferencias vs. desconocidos del repo**, con cita de
  archivo y línea: `docs/onboarding.md`.

## Comandos esenciales

```sh
uv sync --frozen        # instalar dependencias exactas del lockfile
uv run pytest -q        # correr la suite
uv run ruff check .     # lint
```

El resto de comandos (levantar/apagar Postgres, arrancar la API, correr un
solo test) está en `README.md`.

## Persistencia en pruebas

- Las pruebas que ejercitan persistencia corren contra **PostgreSQL**, nunca
  contra SQLite: no reproduce las mismas restricciones, tipos ni migraciones.
  Detalle en `docs/decisiones-ingenieria.md`.

## Datos locales

- Nunca abrir, mostrar, editar ni confirmar `.env`: puede contener secretos.
  `.env.example` es la fuente permitida para conocer nombres de variables.

## Disciplina de pruebas

- Nunca debilitar ni eliminar un test existente para conseguir verde. Si el
  comportamiento acordado cambió, primero se actualiza el contrato
  (`docs/contrato-api.md`) y después el test, en un commit separado. Detalle
  en `docs/decisiones-ingenieria.md`.
