# Estilo de código

## Tipado

- Usa `X | None`, nunca `Optional[X]` (ruff `UP` lo exige).
- Usa `list[X]` / `dict[K, V]`, nunca `typing.List` / `typing.Dict` (ruff `UP` lo exige).
- Anota el tipo de retorno de toda función, incluida cada ruta async y cada helper privado de test.
- Los modelos de SQLAlchemy declaran cada columna con `Mapped[T]` y `mapped_column(...)`, nunca `Column` sin tipar.

## Esquemas frente a diccionarios sueltos

- Toda ruta declara `response_model` con un esquema Pydantic; nunca devuelve un `dict` armado a mano ni el modelo ORM directamente.
- Los esquemas de lectura (`*Read`) usan `ConfigDict(from_attributes=True)` para mapear desde el ORM, nunca copian campo por campo.
- Un `PATCH` aplica `payload.model_dump(exclude_unset=True)` y un bucle `setattr`, nunca asigna cada campo a mano.

## Funciones async

- Toda función que toca la base de datos o el ciclo request/response de FastAPI es `async def`.
- Toda ruta recibe la sesión con `Depends(get_session)`; ninguna abre su propia sesión.

## Manejo de errores

- Un error de negocio se señala con `HTTPException(status_code=..., detail="...")`, nunca con una excepción sin capturar ni un código de estado hardcodeado fuera de esa clase.
- El `detail` de todo error es una oración legible en español, nunca una clave interna o un código.
- Una regla que podría violar una restricción de la base (existencia, unicidad) se comprueba antes con una consulta explícita, nunca capturando la excepción de integridad de la base.

## Lo que ruff ya exige (`pyproject.toml`, `[tool.ruff.lint]`)

- Línea máxima de 100 caracteres (`line-length = 100`).
- Imports ordenados y agrupados (stdlib, terceros, locales), sin imports sin usar (regla `I`, incluye `F401`).
- Sintaxis moderna de tipos y construcciones (regla `UP`): sin `Optional`, `Union`, `typing.List`, etc.
- Errores básicos de estilo pycodestyle (regla `E`) y errores lógicos de Pyflakes (regla `F`).
