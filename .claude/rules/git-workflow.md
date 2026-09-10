# Flujo de git y Pull Requests

Aplica a cualquier tarea que publique una rama, abra o fusione una Pull
Request en este repositorio.

## Antes de commitear

- Si ya existe o se mencionó una rama de feature relacionada con el cambio
  en curso, confirmar la rama activa (`git status --short --branch`) antes
  de comitear — no asumir que el checkout actual es el lugar correcto solo
  porque nadie pidió cambiar de rama explícitamente.

## Descripción de la Pull Request

Toda PR hacia `main` sigue el mismo formato de cuatro secciones:

```markdown
## Qué cambia
## Qué se decidió y por qué
## Cómo se comprueba
## Qué queda sin probar
```

- "Qué se decidió y por qué" nombra explícitamente lo que quedó fuera de
  alcance a propósito, no solo lo que se implementó.
- "Cómo se comprueba" cita los comandos reales usados (`uv run pytest -q`,
  `uv run ruff check .`) y qué casos nuevos cubren los tests.
- "Qué queda sin probar" es honesto sobre huecos reales, nunca una lista
  vacía de relleno.
- Se muestra el borrador completo y se espera aprobación explícita antes de
  `gh pr create`.

## Cambios sin commitear en la rama que se publica

Si `git status` muestra modificaciones o archivos sin trackear que no
forman parte de los commits que van a la PR, se avisa explícitamente que
quedan afuera — nunca se commitean por iniciativa propia ni se presentan
como si fueran parte del cambio.

## Fusión

Este repositorio integra Pull Requests con merge commit
(`gh pr merge --merge`), nunca squash. Antes de fusionar, comprobar
`mergeable`/`mergeStateStatus` con `gh pr view --json`.
