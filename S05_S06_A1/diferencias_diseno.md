# Diferencias de diseño del equipo ReportaYa

Qué aportó cada integrante en los tres artefactos de diseño (especificación OpenAPI, diagrama de clases y arquitectura), qué conflictos aparecieron y cómo se resolvieron.

**Integrantes:** Manuel Medina (M), Emmanuel Castañeda «Lupus» (L), Alejandro Arreola (A) y Luis Guerrero (G).
**Contrato base:** `SRS_equipo.md` v2.0.
**Resultados consolidados:** `openapi_equipo.yaml`, `diagrama_clases_equipo.puml` y `arquitectura_equipo.md` con `diagrama_componentes_equipo.puml`.
**Detalle por artefacto:** `analisis_diferencias.md` (API, conflictos C-1 a C-24), `analisis_clases.md` (clases, K-1 a K-23) y la sección 2 de `arquitectura_equipo.md` (AR-2 a AR-13).

**Qué material se revisó.** Las cuatro especificaciones OpenAPI; los diagramas de clases de M, A y G; los diagramas de componentes de M, A y G; los ADR de M y G; el encabezado del ADR de A (citado en sus diagramas); `revision_rest.md` y `decisiones_y_trazabilidad.md` de L, y sus dos diagramas de secuencia. **No se adjuntaron** el diagrama de clases ni el de componentes de L, ni el ADR de A. Lo que se dice de ellos sale de lo que sus otros documentos citan, y se marca así.

---

## 1. Qué aportó cada integrante

### 1.1 Especificación OpenAPI

| | Aportó y se adoptó | Se descartó o se cambió |
|---|---|---|
| **M** | Base del contrato: casi todos los paths (`/reports/{folio}/…`), un `POST` por transición como evento con `Location`, `GET /assignees`, `/external-providers`, costos con anulación, garantía, constancia de fotos compartidas, `duplicate-flag`, delegaciones como colección, parámetros con bitácora, `Idempotency-Key` (los cuatro lo incluyen), `If-Match` (solo M) y tablero con PDF por `Accept` | `PUT` además de `PATCH` en el padrón; `PATCH` para parámetros (pasó a `PUT`); `429` en el login |
| **L** | Principios REST (sin verbos en la URI, `201` con `Location`, `409` y `500` declarados, merge-patch), orden de errores 401 → 404 → 403 → 409 → 422, `DELETE /sessions/current`, `GET` de indicaciones de persistencia, método de trazabilidad automática contra el SRS | Rutas en español; `POST /transiciones` genérico; rutas anidadas por ciclo; varios responsables con ramas derivadas; `/vinculos` entre reportes; reapertura a `Asignado`; `responsableCosto` derivado; sin `If-Match` |
| **A** | `GET /reports/possible-duplicates`, vinculaciones del residente a la unidad (`/users/{id}/unit-links`), constancia de foto compartida, idea de exportar el tablero, delegación a la Auxiliar | Rutas en español; `POST /transiciones`; delegación como recurso por usuario; ruta separada `/tablero/exportacion`; login con `200` y solo `401` y `422` como errores |
| **G** | `DELETE` de la fecha programada de visita, `PATCH` de avisos como leídos (también en M y L), idea de una lista de asignados propia del Mantenimiento | `PUT /assignment`; `/users/me/assigned-reports` (se fusionó en `GET /reports`); `429`; sin Vigilancia, catálogo, costos, detenciones ni parámetros (modelaba un SRS anterior) |

### 1.2 Diagrama de clases

| | Aportó y se adoptó | Se descartó o se cambió |
|---|---|---|
| **M** | La estructura más completa: `EntradaHistorial` con subclases (incluidas `Costo` e `IndicacionPersistencia`), `CicloAtencion` con los datos por ciclo, interfaz `Responsable`, `Costo.anula`, `RegistroComparticion`, enumeraciones y notas de reglas de integridad | `Residente` con ocupación y fecha propias; `Propietario` como clase con relación 1..*; jerarquía `Archivo`→`Fotografia`→`FotoAlta`/`FotoEvidencia`; clase `Garantia`; `Pagador` y teléfono en `Usuario` |
| **A** | `VinculacionUnidad`, un solo `Adjunto` con tipo y etapa, `ConfirmacionResidente`, `VersionCorreccion` con campo y valores, `perfilAdministracion`, `emitidoEn`/`venceEn`/`usadoEn` en el enlace, `subidoPor`, justificación escrita de cada decisión | Dos asociaciones con `{xor}` en lugar de `Responsable`; datos de evidencia y garantía en `Reporte`; propietario con atributos planos |
| **G** | `hashToken` (solo se guarda el hash), `intentosFallidos`/`bloqueadoHasta`, nota `{xor}` sobre el dueño de cada foto, justificación de `CicloAtencion` como clase | `EventoReporte` único con `detalle` JSON; `PerfilMantenimiento` compuesto; enum `Rol` sin Vigilancia; estado sin `Unido`; valores en mayúsculas; faltan piso, delegación, proveedor sin acceso, parámetros, detenciones y costos |
| **L** | Sus documentos citan un diagrama con decisiones D1 a D6 (no adjunto) | Sus decisiones D2 (varios responsables por ciclo) y D4 (reapertura a `Asignado`) contradicen el SRS y ya se rechazaron en el API; falta comparar el diagrama completo |

### 1.3 Arquitectura

| | Aportó y se adoptó | Se descartó o se cambió |
|---|---|---|
| **M** | ADR-001 (monolito modular en capas, worker, idempotencia, proxy, respaldo, evolución futura de `avisos`), ADR-002 (ciclo de atención), ADR-003 (historial de solo inserción), diagrama de contenedores y de despliegue, regla «ningún módulo lee las tablas de otro» | Frontend sin decidir; la API envía los correos de activación y recuperación; la «tabla de trabajos» sin transacción explícita; el proxy solo aparece en el despliegue |
| **A** | Outbox escrita en la misma transacción que el cambio, regla «sin broker», puertos `AlmacenArchivos`, `ServicioCorreo` y `Reloj`, React + Vite, módulos `configuracion` y `atencion`, tolerancia sin conexión | El navegador llama directo a la API; contenedor `frontend` sin proxy; `gestion` y `atencion` por separado; falta `auth` |
| **G** | Análisis de cuatro alternativas con sus compromisos, tabla RNF → arquitectura, módulo `auth`, Caddy como proxy, respaldo con `pg_dump`, mitigación del bloqueo por fila | Next.js en un contenedor Node; tarea periódica dentro de la API; sin Vigilancia, worker, PWA sin conexión ni respaldo externo (su ADR usa su SRS v1.2) |
| **L** | JWT con `sid` y tabla de sesiones, `Idempotency-Key` con vigencia de 24 h, versionado `/api/v1`, límite de peticiones en el proxy, evidencia en los diagramas de secuencia de la outbox y la cola local | Su ADR y su diagrama de componentes (no adjuntos) decían «cookie de sesión» |

**Resumen de aportes.** M fue la base del API, de las clases y de la arquitectura; A aportó los refinamientos de dominio y la regla de la outbox; G aportó el análisis comparativo de alternativas y la seguridad del token; L aportó los principios REST, la idempotencia y la sesión revocable, y el método de verificación automática.

---

## 2. Conflictos y resolución

### 2.1 Cuántos hubo

| Artefacto | Conflictos | Dónde está el detalle |
|---|---|---|
| OpenAPI | 24 (C-1 a C-24) más 2 que surgieron al leer los documentos de L (sección 2.3) | `analisis_diferencias.md` |
| Clases | 23 (K-1 a K-23) | `analisis_clases.md` |
| Arquitectura | 12 (AR-2 a AR-13) | `arquitectura_equipo.md`, sección 2.3 |

### 2.2 Criterios que se aplicaron, en este orden

1. **Manda el SRS_equipo v2.0.** Por eso se rechazaron los varios responsables de L y su reapertura a `Asignado`.
2. **Si el SRS no decide, manda el contrato del API.** Cada atributo de clase debe tener un campo equivalente (se verificó con un script: 0 diferencias en 34 clases y 19 enumeraciones).
3. **Si ninguno decide, gana el diseño más simple que no pierde información** (por ejemplo, un solo `Adjunto` en lugar de cuatro subclases, o el worker aparte en lugar de una tarea dentro de la API).

### 2.3 Dos conflictos nuevos que salieron de los documentos de L

No estaban en `analisis_diferencias.md` porque venían de `decisiones_y_trazabilidad.md`:

| # | Tema | Variantes | Resolución | Razón |
|---|---|---|---|---|
| C-25 | **Responsable del costo** | L: se deriva de la responsabilidad (`COMUN` → condominio, `PRIVADA` → propietario), no se acepta como dato. M y A: dato que registra la Administración | Dato de entrada con valores `Condominio` o `Condomino` | RF-06 lo lista entre los datos de la asignación y RF-06-AC-2 lo registra explícitamente (propietario de una unidad de origen distinta de la observada). La responsabilidad `PorDeterminar` no permite derivarlo |
| C-26 | **Concurrencia optimista** | L: se excluye (riesgo bajo, todo es de solo inserción). M: `ETag` e `If-Match` | Se mantiene `If-Match` solo en las operaciones que reemplazan o corrigen datos (`PATCH` del reporte, reclasificación, visita, garantía) y no en las que crean eventos | Evita que dos personas de la Administración se pisen sin costo apreciable; si el equipo decide quitarlo, el cambio no rompe a los clientes |

### 2.4 Decisiones que valen para los tres artefactos

Estas decisiones se tomaron una sola vez y se reflejan igual en el API, en las clases y en la arquitectura:

| Decisión | API | Clases | Arquitectura |
|---|---|---|---|
| **Un solo responsable por reporte** (usuario de Mantenimiento o proveedor con o sin acceso) | `responsableId`, `ResponsableRef`, `GET /assignees` | Interfaz `Responsable` | — |
| **Ciclo de atención** por reapertura, mismo folio; reapertura lleva a `EnProceso` | `/cycles`, `/reopenings`, `Ciclo` | `CicloAtencion` | ADR-002 de M |
| **Historial de solo inserción**; los borrados responden 403 | `DELETE` rechazado, `/history` | `EntradaHistorial` y subclases | ADR-003 de M; repositorios sin actualizar ni borrar |
| **Idempotencia** de los envíos que se reintentan sin señal | `Idempotency-Key`, `x-idempotent` | Fuera del dominio (infraestructura) | Tabla de claves, limpieza en el worker |
| **Sesión revocable** con expiración por inactividad | `/sessions`, `DELETE /sessions/current` | Fuera del dominio | JWT con `sid` y tabla de sesiones |
| **Correo asíncrono con 3 reintentos** que nunca impide guardar el cambio | `/email-deliveries` (`Fallido`) | `EnvioCorreo` | Outbox transaccional y worker; la API no habla con el correo |
| **Tablero y PDF con las mismas cifras** | `GET /metrics` con `Accept` | Derivados, sin clase | Módulo `metricas` |
| **Parámetros configurables** con bitácora | `/parameters` | `Parametro`, `CambioParametro` | Módulo `configuracion` |

### 2.5 Cambios que la verificación cruzada obligó a hacer

Al comparar las clases con el API aparecieron cuatro errores del propio `openapi_equipo.yaml` (no de los diagramas individuales). Ya están corregidos:

| Schema | Antes | Ahora | Fuente |
|---|---|---|---|
| `CostCreate`, `Cost` | `monto` obligatorio; `pagador` con cuatro valores | `monto` opcional; `pagador` con `Condominio` o `Condomino` | RF-20 |
| `ReportCreate`, `ReportDetail` | sin `desdeCuando` ni `habiaPasadoAntes` | Agregados | RF-03-AC-9 |
| `CompletionData`, `Ciclo` | `pendiente` booleano | `pendientes` texto de hasta 1,000 caracteres | RF-08-AC-7 |
| `AssignRequest`, `ReclassifyRequest`, `ReportDetail` | `responsableCosto` libre | Enum `Pagador` | RD-03 |

---

## 3. Qué debe actualizar cada integrante

| Integrante | Artefactos individuales por alinear |
|---|---|
| **M** | Diagrama de clases: clases `Garantia`, `Propietario` como entidad, jerarquía de archivos, `Pagador` y teléfono en `Usuario`; contenedores: agregar proxy y quitar el correo directo desde la API |
| **L** | Especificación y secuencias a las rutas de `openapi_equipo.yaml`; decisiones D2 y D4 del diagrama de clases; ADR y componentes, que decían «cookie de sesión»; entregar el diagrama de clases y el de componentes para compararlos |
| **A** | Diagrama de componentes: agregar proxy y módulo `auth`, y sacar el contenedor `frontend`; clases: `Responsable` en lugar del `{xor}`, `Garantia` por ciclo; rutas del API |
| **G** | Rehacer ADR y diagramas sobre el SRS v2.0 (Vigilancia, `Unido`, worker, PWA sin conexión, respaldo, costos, delegación, parámetros); cambiar Next.js, tarea interna y enum `Rol` |

---

## 4. Decisiones abiertas

| Tema | Estado | Quién debería cerrarlo |
|---|---|---|
| Notas internas: 404 o 403 para quien no las ve | Se eligió 404; el SRS no lo dice | Cliente simulado |
| Objetivo de resolución «Normal» (72 h o 3 a 5 días hábiles) | Es parámetro configurable | Cliente simulado |
| Código al bloquear una cuenta | 401 genérico; M y G proponían 429 | Equipo |
| Librería del PDF del tablero | Sin elegir | Quien implemente `metricas` |
| Proveedor de correo, nube y respaldos | Abierto (diseño técnico) | Equipo |
| Viabilidad de RNF-11 (modo sin conexión con fotos) | Riesgo mayor; prototipar en las primeras semanas | Quien implemente la PWA |
| Comparar el diagrama de clases de L cuando se entregue | Pendiente | L |
