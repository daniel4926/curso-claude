---
name: segmentar-commits
description: Reparte los cambios actuales del árbol de trabajo (staged y sin stagear) en una secuencia de commits atómicos con Conventional Commits, basándose en el estado real del repositorio (git status y git diff --stat), no en supuestos. Úsala cuando el usuario pida dividir, repartir, segmentar u ordenar cambios en commits antes de confirmarlos. Muestra el reparto propuesto y espera aprobación explícita antes de crear ningún commit; no decide qué cambios hacer, no hace git push, y no usa git add -A.
---

# Segmentar commits

Reparte los cambios actuales del repositorio en una secuencia de commits,
cada uno con una sola intención, usando Conventional Commits. No asume el
estado del repositorio: lo verifica en el momento de invocarse.

## Paso 1 — Estado real del repositorio

Antes de proponer nada, correr:

```sh
git status --short
git diff --stat
git diff --cached --stat
```

Se corren los tres aunque parezca que no hace falta: `git status --short`
puede no distinguir bien renombres o cambios parciales ya indexados, y si
el usuario dejó algo en el índice de una sesión anterior, `git diff --stat`
solo (sin `--cached`) no lo muestra.

No se usa `git diff` sin `--stat`, ni se lee el contenido completo de un
archivo modificado, salvo el caso descrito en "Cuándo mirar el contenido"
más abajo. El resumen por archivo (ruta, líneas `+`/`-`, si es nuevo,
borrado o renombrado) alcanza para trazar el mapa del cambio y decidir
cómo agruparlo; el contenido línea por línea no aporta nada a esa decisión
y crece con el tamaño del cambio, no con la cantidad de archivos.

### Cuándo mirar el contenido

Si un mismo archivo mezcla cambios de intención claramente distinta (por
ejemplo, un fix puntual y una limpieza de estilo en el mismo archivo) y el
resumen no alcanza para decidir si van en el mismo commit o en dos, recién
ahí se pide el diff completo de **ese archivo puntual**
(`git diff -- <archivo>`), nunca el de todo el árbol.

## Paso 2 — Agrupar por intención, no por tipo de archivo

Cada grupo es un commit con una sola intención (una funcionalidad, un fix,
un refactor, un cambio de documentación, etc.). Señales para agrupar:

- Un archivo de código y el test que lo comprueba van en el mismo commit:
  un commit que agrega comportamiento sin el test que lo prueba, o un test
  sin el código que lo hace pasar, no es un estado comprobable.
- Cambios en archivos sin relación entre sí (un fix en un módulo y una
  tarea de limpieza en otro) van en commits separados aunque se hayan
  tocado en la misma sesión.
- Un mismo archivo puede aparecer en más de un commit si sufrió cambios de
  distinta intención.

## Paso 3 — Ordenar para que cada commit sea comprobable

El orden importa: cada commit, aplicado sobre el anterior, debe dejar el
repositorio en un estado que se pueda comprobar con los comandos
canónicos del repo (`README.md`) — `uv run pytest -q` y
`uv run ruff check .` no deberían romperse a mitad de la secuencia por
haber separado, por ejemplo, un modelo de la migración que lo crea, o una
función de quien ya la usa.

Si dos cambios son interdependientes (un modelo nuevo y el router que lo
usa), van en el mismo commit, o en commits consecutivos donde el primero
no deja el repositorio roto hasta que llega el segundo.

## Paso 4 — Elegir el prefijo por lo que hace el commit

Conventional Commits, prefijo según la intención del commit completo,
nunca según la carpeta o la extensión de sus archivos:

| Prefijo | Cuándo |
|---|---|
| `feat` | Agrega comportamiento observable nuevo |
| `fix` | Corrige un comportamiento incorrecto |
| `refactor` | Cambia la estructura interna sin cambiar comportamiento observable |
| `test` | Agrega o ajusta tests sin cambiar el código de producción que prueban |
| `docs` | Cambios solo en documentación |
| `chore` | Mantenimiento sin efecto en comportamiento ni documentación (dependencias, configuración) |

Un test que acompaña a un `feat` no convierte el commit en `test`: el
prefijo lo decide la intención del conjunto, no la presencia de un tipo de
archivo en particular.

## Paso 5 — Mostrar el reparto y esperar aprobación

Antes de tocar nada: mostrar cada commit propuesto, en el orden acordado,
con sus archivos y su mensaje completo (incluido el pie de atribución
vigente en la sesión, si la sesión lo pide). Todavía no se corre
`git add` ni `git commit`.

Esperar aprobación explícita. Si el usuario pide cambios al reparto (mover
un archivo de un commit a otro, dividir uno en dos, cambiar un mensaje),
ajustar y volver a mostrar antes de confirmar nada.

## Paso 6 — Confirmar, un commit a la vez

Solo tras la aprobación: por cada grupo, en el orden acordado, `git add`
de sus archivos por nombre y `git commit`. Al terminar el último, correr
`git status` y confirmar que el árbol quedó limpio, salvo que el usuario
haya dicho explícitamente que algo se queda deliberadamente sin commitear.

## Fuera de alcance

- No decide qué cambios hacer ni corrige código: solo reparte lo que ya
  existe en el árbol de trabajo.
- No hace `git push`.
- No usa `git add -A` ni `git add .`: siempre agrega archivos por nombre,
  grupo por grupo.
