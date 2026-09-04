---
name: planificar-incremento
description: Genera un plan de incrementos para una funcionalidad nueva de esta API (proyectos, tareas, filtros, due_at, etc.), basado en el contrato, las decisiones de ingeniería y el estado real del repositorio. Úsala cuando el usuario pida planificar, diseñar el plan de, o definir los incrementos de una funcionalidad antes de implementarla. Esta skill solo planifica: no escribe ni modifica código, no instala dependencias, no toca la base de datos.
---

# Planificar incremento

Produce un documento de plan en `docs/` para una funcionalidad de esta API,
dividido en incrementos numerados y ejecutables. No implementa nada.

## Documentos contra los que se planifica

Léelos, en este orden, antes de escribir una sola línea del plan:

1. `docs/contrato-api.md` — comportamiento observable que el plan debe cumplir.
2. `docs/decisiones-ingenieria.md` — decisiones de ingeniería del equipo
   (base de datos, migraciones, disciplina de pruebas).
3. `CLAUDE.md` — reglas del repositorio que aplican a cualquier tarea.
4. `README.md` — comandos canónicos disponibles para las comprobaciones.
5. `docs/onboarding.md` — qué es hecho, inferencia o desconocido hoy en el
   repo; no planifiques sobre algo que ese documento ya marca como
   desconocido sin resolverlo primero (ver regla de no aplazar, abajo).

Además, revisa el estado real del código que el incremento va a tocar (no
solo los documentos) antes de describir el estado del repositorio.

## Dónde y con qué nombre se guarda el plan

- El archivo va en `docs/`.
- Nombre: `docs/plan-<tema>.md`, donde `<tema>` identifica de qué es el plan
  (ejemplos: `plan-proyectos.md`, `plan-tareas-v2.md`). No uses nombres
  genéricos como `plan.md`.
- Si ya existe un plan para el mismo tema, edítalo en vez de crear uno
  paralelo.

## Estructura obligatoria del documento

1. Encabezado y una línea de propósito.
2. **Fuentes**: lista explícita de los documentos leídos.
3. **Fuera de alcance**: lista explícita de lo que este plan NO cubre. Nunca
   se omite esta sección, aunque la lista sea corta.
4. **Estado del repositorio al planificar**: hechos verificados en el código
   actual, con cita de archivo — no supuestos.
5. **Decisiones**: cada decisión de diseño que la funcionalidad requiere,
   ya tomada (ver regla de no aplazar).
6. **Incrementos** numerados.

## Incrementos

- Numerados, en el orden en que se implementarían.
- Cada incremento describe un cambio concreto y cierra con una
  **Comprobación** ejecutable: un comando o test que alguien puede correr,
  que falla si el incremento no está hecho y pasa si lo está. No se acepta
  una comprobación en prosa sin comando o test asociado.
- Un incremento corresponde a un commit, siguiendo el formato ya usado en
  `docs/plan-persistencia.md`.

## Regla de no aplazar decisiones

- Si una decisión de diseño no se puede resolver con lo que ya hay en el
  repositorio (contrato, decisiones de ingeniería, código existente), no se
  propone en condicional ("se podría", "probablemente", "lo ideal sería").
  Se detiene el plan en ese punto y se pregunta al usuario explícitamente qué
  decidir.
- El documento final no contiene ninguna "decisión abierta": o se resolvió
  preguntando, o el tema pasa a "Fuera de alcance".

## Límite: esta skill planifica, no implementa

- No crea ni modifica ningún archivo de código (`app/`, `alembic/`,
  `tests/`, etc.). El único archivo que escribe es el plan en `docs/`.
- No instala ni actualiza dependencias (`uv add`, cambios en
  `pyproject.toml` o `uv.lock`).
- No toca la base de datos: no corre migraciones, no levanta ni apaga
  `docker compose`, no ejecuta queries.
- Cualquier verificación que necesite hacer para describir el estado del
  repositorio debe ser de solo lectura (leer archivos, `git log`, `git
  status`). Ante la duda de si un comando muta estado, no lo ejecuta y lo
  deja anotado como algo a confirmar.
