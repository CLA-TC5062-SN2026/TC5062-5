# Clasificación de problemas del análisis estático — S09-A1

**Equipo 5 · TC5062 · Backend de ReportaYa** (`backend/`: FastAPI + SQLite + JWT)
**Salida completa:** `output_linter.txt` · **Configuración:** `backend/setup.cfg`

## 1. Herramientas y configuración

| Herramienta | Versión | Qué revisa | Configuración relevante |
|---|---|---|---|
| **pylint** | 4.1.3 | Convenciones, diseño (tamaño y complejidad), posibles errores, código duplicado | Línea máx. 120; límites de diseño por defecto (5 argumentos, 15 variables locales, 12 ramas, 50 sentencias); duplicados desde 6 líneas |
| **flake8** | 7.5.0 | Estilo PEP 8, código sin usar, complejidad ciclomática (McCabe) | Línea máx. 120; complejidad máx. 10 |
| **mypy** | 2.4.1 | Tipos | `check_untyped_defs = True` (revisa también funciones sin anotaciones, que son la mayoría) |

Se analizaron `app/` y `scripts/` (2,176 líneas). Las pruebas (`tests/`) quedan fuera porque la actividad pide auditar el código del backend.

**Por qué 120 caracteres y no 79:** el equipo escribe líneas largas a propósito (consultas SQL en una línea). 120 es un límite profesional común; lo que pasa de 120 sí se reporta.

## 2. Resultado

| Herramienta | Resultado |
|---|---|
| pylint | **7.91/10** · 289 mensajes: 249 de convención (C), 17 de refactorización (R), 23 advertencias (W), 0 errores (E) |
| flake8 | **119** problemas |
| mypy | **18** errores en 5 archivos |

pylint y flake8 se traslapan (líneas largas, imports sin usar, varias sentencias por línea), así que abajo cada problema se cuenta **una vez** y se agrupa por tipo.

## 3. Criterios de clasificación

| Severidad | Criterio | Pregunta que usamos para decidir |
|---|---|---|
| **Crítico** | Puede causar un bug observable o un problema de seguridad | ¿Un usuario o un atacante puede obtener un resultado incorrecto **hoy**? |
| **Importante** | Afecta la mantenibilidad o el rendimiento | ¿Hace más difícil o riesgoso cambiar, probar o depurar el código? |
| **Menor** | Estilo, nombres, comentarios | ¿Solo cambia cómo se lee el código, no lo que hace? |

Además, cada advertencia se verificó contra el código. Las que **no** representan un problema real se listan como **falsos positivos** (sección 7): una herramienta no siempre entiende la lógica del programa.

## 4. Críticos (1 problema, 5 lugares)

| ID | Problema | Dónde | Herramienta | Por qué es crítico | Acción |
|---|---|---|---|---|---|
| **CR-1** | El encabezado `Idempotency-Key` se recibe pero **nunca se usa** | `app/routers/reportes.py:140` (alta de reporte), `:390` (notas), `:414` (detenciones), `:437` (costos), `:512` (indicaciones de persistencia) | pylint W0613 `unused-argument` | El contrato (`openapi_equipo.yaml`, parámetro `IdempotencyKey`) promete que un reintento con la misma clave **devuelve el resultado original sin repetir la operación** (RNF-11). Como la clave se ignora, cada reintento **sí se procesa**: un celular sin señal que reenvía su reporte crea un segundo reporte con otro folio, otras fotos y otros avisos; en costos, duplica montos. Es un bug funcional que el usuario sí ve. | Guardar la clave y la respuesta en una tabla `idempotencia(clave, usuario, ruta, respuesta)` y, si la clave ya existe, devolver la respuesta guardada. Ya estaba identificado en `S05_S06_A1/revision_sql.md:106` (deuda técnica intencional, ver `deuda_tecnica.md`). |

No se encontraron problemas de seguridad con las herramientas. La revisión manual de seguridad (inyección SQL, exposición de datos) se hace en `code_review.md`.

## 5. Importantes (4 grupos)

| ID | Problema | Dónde | Herramienta | Por qué es importante y no crítico |
|---|---|---|---|---|
| **IM-1** | **Funciones demasiado grandes o complejas** (violan SRP) | `reportes.py:138` `create_report`: complejidad 26, 83 sentencias, 40 variables, 26 ramas · `reportes.py:281` `correct_report`: complejidad 14, 25 variables · `reportes.py:96` `list_reports`: complejidad 11, 12 argumentos · `usuarios.py:52` `create_user`: complejidad 14 · `usuarios.py:103` `update_user`: complejidad 13 · `serial.py:138`: 18 variables · `util.py:124` `pagina`: 7 argumentos · `reportes.py:37`: 8 argumentos | flake8 C901; pylint R0912, R0913, R0914, R0915, R0917 | Hoy funcionan (las 759 verificaciones de contrato pasan), pero una función con complejidad 26 tiene al menos 26 caminos que probar. Cualquier cambio en `create_report` arriesga romper algo que no se ve. Es el principal candidato a refactorización (Parte 4). |
| **IM-2** | **Excepciones relanzadas sin `from`**: se pierde la causa original | `util.py:56`, `security.py:72`, `security.py:74`, `schemas.py:225`, `schemas.py:227`, `reportes.py:145` | pylint W0707 `raise-missing-from` | La respuesta al cliente es correcta (por ejemplo, el 401 de un JWT vencido) y **no cambia la seguridad**: el cliente nunca ve la causa. Lo que se pierde es la cadena de errores en el **log del servidor**, y eso hace más difícil depurar un fallo real. Por eso es mantenibilidad, no seguridad. |
| **IM-3** | **Anotación de tipo que no se cumple**: `etiqueta()` dice devolver `str` pero puede devolver `None` | `serial.py:69` (lo usa `serial.py:79`) | mypy `return-value` | Quien llama confía en el tipo y no revisa `None`. Hoy no falla porque las llaves foráneas garantizan que la ubicación existe, así que no es un bug observable; pero la firma engaña y un cambio futuro lo puede convertir en uno. Corrección: `-> str | None`. |
| **IM-4** | **Listas de parámetros SQL sin tipo explícito** | `usuarios.py:43`, `:46`; `reportes.py:109`–`:126` (11 errores); `catalogo.py:33`; `avisos.py:53` | mypy `arg-type`, `list-item` (15 errores) | No es un bug: SQLite acepta valores de cualquier tipo en la lista de parámetros. mypy infiere el tipo de la lista por su **primer** elemento y luego marca los demás. Es importante porque 15 errores de "ruido" esconden los errores reales de mypy. Corrección: declarar `params: list[Any] = []`. |

## 6. Menores (agrupados)

| ID | Problema | Cantidad | Ejemplo | Comentario |
|---|---|---|---|---|
| ME-1 | Funciones y clases sin docstring | 85 + 28 | `routers/auth.py`, `schemas.py` | Muchas funciones tienen comentarios que citan el RF; falta pasarlos a docstring. |
| ME-2 | Líneas de más de 120 caracteres | 79 (pylint) / 81 (flake8) | `scripts/init_db.py:102` (151) | Sobre todo consultas SQL en una sola línea. |
| ME-3 | Nombres fuera de la convención de Python (`snake_case`) | 29 | `pageSize`, `ubicacionTipo` | **Parcialmente intencional**: son parámetros de consulta y deben coincidir con los nombres del contrato OpenAPI. Se pueden mantener en la URL con `Query(alias="pageSize")` y usar `page_size` en Python. |
| ME-4 | Varias sentencias en una línea con `;` | 18 | `reportes.py:107` | Dificulta leer y depurar línea por línea. |
| ME-5 | Imports sin usar | 11 | `catalogo.py:2` (`sqlite3`), `usuarios.py:9` (`UNIT_SQL`) | Código muerto; confunde sobre qué depende de qué. |
| ME-6 | Orden y posición de imports, imports dentro de funciones | 7 | `reportes.py:15`, `main.py:76`, `scripts/init_db.py:14` | El de `init_db.py:14` es necesario (ajusta `sys.path` antes de importar `app`). |
| ME-7 | Lambdas asignadas a variable | 2 | `reportes.py:315`, `init_db.py:17` | Un `def` con nombre da mejores trazas de error. |
| ME-8 | Indentación de continuación, `else` innecesario tras `raise` | 3 | `reportes.py:363`, `db.py:28` | Solo estilo. |
| ME-9 | Argumento `e` sin usar en el manejador de errores | 1 | `main.py:68` | FastAPI exige la firma `(request, exc)`; basta renombrarlo `_e`. |

## 7. Falsos positivos (verificados, no requieren cambio)

| Advertencia | Dónde | Por qué no es un problema |
|---|---|---|
| mypy: `carpeta` puede ser `None` al usar `/` | `reportes.py:234` | `carpeta` se crea en la línea 229 **siempre que** `aceptados` tenga elementos, y solo se usa dentro del ciclo sobre `aceptados`. mypy no sigue esa relación entre dos variables. |
| mypy: `ctype` puede ser `None` al usar `.split` | `reportes.py:242` | Un archivo solo entra a `aceptados` si su `content_type` es `image/jpeg`, `image/png` o `video/mp4` (validado en la línea 189), así que nunca es `None`. |

## 8. Resumen y prioridad

Conteo sobre los 426 mensajes de las tres herramientas (289 de pylint, 119 de flake8 y 18 de mypy; incluye los repetidos entre pylint y flake8):

| Severidad | Grupos | Mensajes | % | Prioridad |
|---|---|---|---|---|
| Crítico | 1 | 5 | 1 % | Corregir antes de habilitar el modo sin conexión (RNF-11) |
| Importante | 4 | 43 (IM-1: 21 · IM-2: 6 · IM-3: 1 · IM-4: 15) | 10 % | IM-1 en la Parte 4 (refactorización); IM-2, IM-3 e IM-4 son cambios pequeños para el siguiente sprint |
| Menor | 9 | 376 | 88 % | Corregir automáticamente donde se pueda (formateador, borrar imports) y agregar el linter a la Definition of Done |
| Falso positivo | 2 | 2 | 0.5 % | Documentados; sin cambio |

**Conclusión:** casi 9 de cada 10 mensajes son de estilo y documentación. El riesgo real está en un bug funcional conocido (CR-1) y en la complejidad de `routers/reportes.py`, que concentra 3 de las 5 funciones más complejas y la mayoría de los hallazgos importantes. Por eso es el archivo elegido para el code review (Parte 2).
