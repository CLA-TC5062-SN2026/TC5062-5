# Code review — `backend/app/routers/reportes.py`

**Equipo 5 · TC5062 · S09-A1 · Parte 2**

## 1. Archivo elegido y método

**Archivo:** `backend/app/routers/reportes.py` (534 líneas). Es el router del recurso principal de ReportaYa (reportes y sus subrecursos). Lo elegimos porque el análisis estático lo señaló como el más complejo: concentra 3 de las 5 funciones con mayor complejidad ciclomática (`create_report` 26, `correct_report` 14, `list_reports` 11) y la mayoría de los hallazgos importantes de `clasificacion_problemas.md`.

**Método:**
1. El agente (Claude Code) revisó el archivo buscando los cinco tipos de problema que pide la actividad: duplicación (DRY), responsabilidades múltiples (SRP), manejo de excepciones, seguridad y nombres.
2. Cada hallazgo se verificó contra el código y contra el SRS (`S03_A1/SRS_equipo.md` v2.0). El de seguridad (H-1) se **reprodujo** con el API real sobre una copia desechable de la base de datos.
3. La explicación de por qué cada hallazgo es un problema la escribimos nosotros. El agente la revisó y la completamos donde estaba incompleta; en esos casos se indica qué se agregó.

## 2. Resumen

| ID | Tipo | Líneas | Severidad |
|---|---|---|---|
| H-1 | Seguridad: control de acceso por registro ausente | 95–133, 275–277, 280–328 | Crítica |
| H-2 | SRP: `create_report` con ocho responsabilidades | 137–249 | Importante |
| H-3 | DRY: la regla de duplicados (RF-17) está escrita dos veces | 205–214 y 262–270 | Importante |
| H-4 | Excepciones: datos faltantes terminan en error 500 o en un mensaje falso | 519, 520–525, 308 | Importante |
| H-5 | Nombres poco descriptivos | 105, 315–317 y todo el archivo | Menor |
| H-6 | Seguridad: SQL armado con f-strings (verificado, no explotable) | 128–131, 259–260 | Menor |
| H-7 | DRY: expresión regular de UUID copiada seis veces, y más débil que la del proyecto | 97, 98, 101, 254, 256, 455 | Importante |

---

## 3. Hallazgos

### H-1 · Seguridad: un Residente puede leer y modificar reportes de otras unidades

**Dónde:** `list_reports` (líneas 95–133), `get_report` (275–277) y `correct_report` (280–328).

**Problema.** `security.py` solo revisa el **rol**: la tabla `PERMISOS` permite `GET /reports` y `GET /reports/{folio}` a todos los roles, y `PATCH /reports/{folio}` a Residente y Administración. Pero ninguna de las tres funciones revisa **qué** reporte pide el usuario:

```python
# líneas 105-128: los filtros salen solo de lo que manda el cliente, nunca del usuario autenticado
w, p = [], []
if ubicacionTipo:
    ...
sql_from = "FROM reporte r" + (" WHERE " + " AND ".join(w) if w else "")

# líneas 275-277: cualquier folio, a cualquier rol
def get_report(folio: str = FolioP, db=Depends(get_db)):
    return responder(report_detail(db, _reporte(db, folio)), etag=True)

# líneas 283-284: correct_report carga el reporte y lo corrige sin comparar con `quien`
r = _reporte(db, folio)
verificar_if_match(if_match, report_detail(db, r))
```

**Evidencia.** Con el API en marcha sobre una copia de la base: la Administración registró un reporte en la unidad C-101. Iniciamos sesión como Rosa, residente de la unidad B-502, y obtuvimos:
- `GET /reports` → el reporte de C-101 aparece en su lista.
- `GET /reports/RY-000004` → **200**, con `horariosAcceso: "Lunes a viernes 9-11, nadie en casa despues"` y el nombre del reportante.
- `PATCH /reports/RY-000004` → **200**, y la descripción cambió a «Modificado por una residente de otra unidad».

**Por qué es un problema.** *Nuestra explicación:* `horariosAcceso` dice cuándo puede no haber nadie en casa, y eso es un riesgo de seguridad física para los vecinos: cualquier residente sabría cuándo un departamento está vacío. *Lo que agregamos después de revisarlo:* además del riesgo de **confidencialidad**, hay uno de **integridad**: un residente puede cambiar la descripción o la ubicación del reporte de otro, y como cada corrección queda en el historial a su nombre, el registro de lo que pasó deja de ser confiable. El SRS lo prohíbe de forma explícita: la matriz de visibilidad (2.3) dice que un Residente **no** ve reportes de otras unidades, y RNF-05 dice que «un residente tampoco puede modificar reportes ajenos». En OWASP Top 10 es **A01: Broken Access Control**, el riesgo número uno.

**Código corregido.** Un solo lugar define la matriz de visibilidad, y las tres funciones lo usan:

```python
ROL_ADMIN, ROL_RESIDENTE, ROL_VIGILANCIA, ROL_MANTENIMIENTO = "Administracion", "Residente", "Vigilancia", "Mantenimiento"


def _filtro_visibilidad(quien) -> tuple[str, list]:
    """Condición SQL sobre `r` (tabla reporte) con lo que cada rol puede ver (SRS 2.3, RNF-05)."""
    rol = quien["rol"]
    if rol == ROL_ADMIN:
        return "1=1", []
    if rol == ROL_RESIDENTE:
        # Su unidad desde su fecha de vinculación, y las áreas comunes.
        return ("""((SELECT tipo FROM ubicacion WHERE id = r.ubicacion_id) = 'AreaComun'
                    OR EXISTS (SELECT 1 FROM vinculacion_unidad v
                               WHERE v.residente_id = ? AND v.unidad_id = r.ubicacion_id
                                 AND r.fecha_aviso >= v.fecha_inicio
                                 AND (v.fecha_fin IS NULL OR r.fecha_aviso <= v.fecha_fin)))""", [quien["id"]])
    if rol == ROL_VIGILANCIA:
        return "r.capturado_por = ?", [quien["id"]]
    if rol == ROL_MANTENIMIENTO:
        return "r.responsable_usuario_id = ?", [quien["id"]]
    return "1=0", []  # rol desconocido: no ve nada


def _reporte_visible(db, folio, quien):
    """Como _reporte, pero responde 404 si el usuario no puede verlo (no revela que el folio existe)."""
    condicion, params = _filtro_visibilidad(quien)
    fila = db.execute(f"SELECT r.* FROM reporte r WHERE r.folio = ? AND {condicion}", [folio, *params]).fetchone()
    if not fila:
        raise no_encontrado("Reporte no encontrado")
    return fila


# list_reports: el filtro de visibilidad siempre va primero
condiciones, parametros = _filtro_visibilidad(quien)
condiciones, parametros = [condiciones], list(parametros)

# get_report
def get_report(folio: str = FolioP, db=Depends(get_db), quien=Depends(actor)):
    return responder(report_detail(db, _reporte_visible(db, folio, quien)), etag=True)

# correct_report: verlo no basta; un Residente solo corrige lo que él reportó
r = _reporte_visible(db, folio, quien)
if quien["rol"] == ROL_RESIDENTE and r["reportante_id"] != quien["id"]:
    raise prohibido("Un Residente solo corrige sus propios reportes (RNF-05)")
```

`_filtro_visibilidad` arma SQL con un f-string, pero las condiciones son texto fijo del código y el `id` del usuario va como parámetro `?`, así que no abre una inyección (ver H-6). Falta además ocultar los datos del reportante en los reportes de áreas comunes («Sí, sin datos del reportante»); eso va en `serial.report_detail`.

---

### H-2 · SRP: `create_report` tiene ocho responsabilidades

**Dónde:** líneas 137–249 (112 líneas, complejidad ciclomática 26, 83 sentencias, 40 variables locales).

**Problema.** Una sola función hace, en este orden:

| Líneas | Responsabilidad |
|---|---|
| 142–145 | Leer el JSON de la parte `datos` |
| 148–152 | Revisar permisos por rol sobre los campos de captura (RF-04) |
| 153–181 | Validar reglas de negocio (descripción, categoría, ubicación, acceso, medio y fecha de aviso, reportante) |
| 183–198 | Validar archivos (tipo, tamaño, vacío) |
| 203–204 | Generar el folio |
| 205–214 | Detectar posibles duplicados (RF-17) |
| 215–227 | Insertar el reporte y su historial |
| 228–247 | Guardar los archivos en disco y limpiarlos si algo falla |

**Por qué es un problema.** *Nuestra explicación:* si algo falla en esa función, todo lo demás está en riesgo, porque todo depende de ella. *Lo que agregamos después de revisarlo:* para cambiar una sola regla, por ejemplo el tamaño máximo de una foto, hay que entender y volver a probar 112 líneas con 26 caminos posibles, y un error en esa parte puede romper el alta completa. Tampoco se puede probar la validación de archivos por separado: hoy la única forma de probarla es hacer un `POST /reports` completo con usuario, categoría y ubicación válidos.

**Código corregido.** La función queda como coordinadora y cada responsabilidad pasa a una función con nombre propio:

```python
def _leer_datos(datos: str) -> S.ReportCreate:
    try:
        return S.parsear(S.ReportCreate, json.loads(datos))
    except json.JSONDecodeError as exc:
        raise peticion_invalida("La parte `datos` no es un JSON válido") from exc


def _validar_archivos(fotos, video) -> tuple[list, list]:
    """Valida cada archivo por separado (RF-05). Devuelve (aceptados, rechazados)."""
    ...  # contenido actual de las líneas 184-198


def _datos_de_captura(d, quien, ahora) -> tuple[str, str, str | None]:
    """Medio de origen, fecha de aviso y reportante según quién captura (RF-03, RF-04)."""
    ...  # contenido actual de las líneas 148-152 y 162-181


@router.post("/reports")
def create_report(datos: str = Form(...), fotos: list[UploadFile] = File(default=[]),
                  video: Optional[UploadFile] = File(default=None),
                  idempotency_key: Optional[str] = Header(default=None),
                  db=Depends(get_db), quien=Depends(actor)):
    d = _leer_datos(datos)
    if len(fotos) > 5:
        raise validacion("fotos", "Máximo 5 fotos por reporte")
    ahora = now_utc()
    medio, aviso, reportante = _datos_de_captura(d, quien, ahora)
    descripcion = _descripcion(d.descripcion)
    _, subtipo, base = _resolver_categoria(db, d.categoriaId, d.subtipo)
    ubicacion = _resolver_ubicacion(db, d.ubicacion)
    aceptados, rechazados = _validar_archivos(fotos, video)
    folio = _registrar_reporte(db, d, quien, ubicacion, ...)  # folio, duplicados, INSERT, historial y archivos en una transacción
    detalle = report_detail(db, _reporte(db, folio))
    return responder({**detalle, "archivosRechazados": rechazados}, 201, f"/reports/{folio}",
                     etag=True, etag_de_recurso=detalle)
```

Esta es una de las tres refactorizaciones de la Parte 4 (ver `refactorizacion.md`).

---

### H-3 · DRY: la regla de posibles duplicados (RF-17) está escrita dos veces

**Dónde:** `create_report`, líneas 205–214, y `find_possible_duplicates`, líneas 262–270.

**Problema.** Las dos funciones tienen la misma consulta copiada, con la misma regla: misma categoría, abierto, y en el mismo piso de la misma torre (unidades) o en la misma área común.

```python
# líneas 206-214 (create_report)
dup = db.execute("""SELECT r.folio FROM reporte r JOIN unidad u1 ON u1.ubicacion_id = r.ubicacion_id
                    JOIN unidad u2 ON u2.ubicacion_id = ?
                    WHERE r.categoria_id=? AND r.estado NOT IN ('Cerrado','Cancelado','Unido')
                      AND u1.torre = u2.torre AND u1.piso = u2.piso
                    ORDER BY r.fecha_aviso DESC, r.folio DESC LIMIT 1""", (ubic, d.categoriaId)).fetchone()

# líneas 263-266 (find_possible_duplicates): la misma consulta, sin LIMIT 1
filas = db.execute("""SELECT r.* FROM reporte r JOIN unidad u1 ON u1.ubicacion_id=r.ubicacion_id
                      JOIN unidad u2 ON u2.ubicacion_id=? WHERE r.categoria_id=?
                      AND r.estado NOT IN ('Cerrado','Cancelado','Unido') AND u1.torre=u2.torre AND u1.piso=u2.piso
                      ORDER BY r.fecha_aviso DESC, r.folio DESC""", (ubicacionId, categoriaId)).fetchall()
```

**Por qué es un problema.** *Nuestra explicación:* si se cambia la regla en un solo lugar, podría haber entradas duplicadas. *Lo que corregimos después de revisarlo:* el riesgo no es que se creen registros duplicados, sino que **la misma regla dé dos respuestas distintas**. `find_possible_duplicates` es lo que la Administración consulta antes de registrar, y `create_report` es lo que marca `posible_duplicado_de` al guardar. Si alguien agrega `Terminado` a los estados excluidos en una sola de las dos, la pantalla diría «no hay duplicados» y el reporte se guardaría marcado como duplicado, o al revés. Una regla de negocio (RF-17) debe vivir en un solo lugar.

**Código corregido.**

```python
ESTADOS_FINALES = ("Cerrado", "Cancelado", "Unido")


def _posibles_duplicados(db, ubicacion_tipo: str, ubicacion_id: str, categoria_id: str) -> list:
    """RF-17: reportes abiertos de la misma categoría en el mismo piso y torre (unidades) o en la misma área común."""
    marcadores = ",".join("?" * len(ESTADOS_FINALES))
    if ubicacion_tipo == "Unidad":
        sql = f"""SELECT r.* FROM reporte r JOIN unidad u1 ON u1.ubicacion_id = r.ubicacion_id
                  JOIN unidad u2 ON u2.ubicacion_id = ?
                  WHERE r.categoria_id = ? AND r.estado NOT IN ({marcadores})
                    AND u1.torre = u2.torre AND u1.piso = u2.piso
                  ORDER BY r.fecha_aviso DESC, r.folio DESC"""
        return db.execute(sql, (ubicacion_id, categoria_id, *ESTADOS_FINALES)).fetchall()
    sql = f"""SELECT * FROM reporte WHERE categoria_id = ? AND ubicacion_id = ? AND estado NOT IN ({marcadores})
              ORDER BY fecha_aviso DESC, folio DESC"""
    return db.execute(sql, (categoria_id, ubicacion_id, *ESTADOS_FINALES)).fetchall()


# create_report
duplicados = _posibles_duplicados(db, d.ubicacion.tipo, ubic, d.categoriaId)
posible_duplicado_de = duplicados[0]["folio"] if duplicados else None

# find_possible_duplicates
filas = _posibles_duplicados(db, ubicacionTipo, ubicacionId, categoriaId)
```

Esta es otra de las tres refactorizaciones de la Parte 4.

---

### H-4 · Excepciones: datos faltantes terminan en un error 500 o en un mensaje que no es cierto

**Dónde:** líneas 519, 520–525 (`create_persistence_indication`) y 308 (`correct_report`).

**Problema.**

```python
# línea 519: si el parámetro no existe, fetchone() devuelve None y None["valor"] lanza TypeError
plazo = db.execute("SELECT valor FROM parametro WHERE clave='plazoReaperturaDias'").fetchone()["valor"]

# líneas 520-525: si no se encuentra la entrada de cierre, limite queda en None...
limite = datetime.strptime(cierre["fecha"], ...) + timedelta(days=plazo) if cierre else None
if limite is None or datetime.now(timezone.utc) > limite:
    # ...y se responde que pasó el plazo, aunque la causa real sea otra
    raise conflicto(f"Pasaron más de {plazo:g} días desde el cierre: la Administración crea un reporte nuevo")

# línea 308: mismo patrón que la 519
ant = db.execute("SELECT nombre FROM categoria WHERE id=?", (r["categoria_id"],)).fetchone()["nombre"]
```

**Por qué es un problema.** *Nuestra explicación:* el usuario puede pensar que el sistema no funciona bien. *Lo que agregamos después de revisarlo:* en el primer caso, el `TypeError` llega al manejador genérico de `main.py` y el usuario recibe un **500 «Ocurrió un error inesperado»**, sin saber qué hacer ni a quién avisar, y quien depura solo ve `'NoneType' object is not subscriptable`, sin saber que falta un parámetro de configuración. En el segundo caso es peor, porque el mensaje **es falso**: un residente que indica a tiempo que su problema persiste recibe «pasaron más de 7 días», cuando la causa real es un dato inconsistente (un reporte `Cerrado` sin su entrada de cierre). El residente se rinde y el error de datos nunca se detecta.

**Código corregido.** Un error de configuración o de datos se distingue de una regla de negocio y se registra en el log:

```python
class DatosInconsistentes(Exception):
    """Un dato que el sistema da por hecho no existe: es un error interno, no del usuario."""


def _parametro(db, clave: str):
    fila = db.execute("SELECT valor FROM parametro WHERE clave = ?", (clave,)).fetchone()
    if fila is None:
        raise DatosInconsistentes(f"Falta el parámetro de configuración '{clave}' (RF-27)")
    return fila["valor"]


plazo = _parametro(db, "plazoReaperturaDias")
cierre = db.execute(...).fetchone()
if cierre is None:
    raise DatosInconsistentes(f"El reporte {folio} está Cerrado pero no tiene entrada de cierre en el historial")
limite = datetime.strptime(cierre["fecha"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(days=plazo)
if datetime.now(timezone.utc) > limite:
    raise conflicto(f"Pasaron más de {plazo:g} días desde el cierre: la Administración crea un reporte nuevo")
```

`DatosInconsistentes` sigue respondiendo 500, porque es un error del sistema y no del usuario, pero el log dice exactamente qué falta y el usuario nunca recibe un mensaje falso.

---

### H-5 · Nombres poco descriptivos

**Dónde:** línea 105 (`w, p`), líneas 315–317 (lambda `e`), y en todo el archivo `d`, `r`, `n`, `f`, `c`, `h`, además de los alias `S` (módulo `schemas`) y `b` (función de `serial`).

**Problema.**

```python
# línea 105: ¿qué son w y p?
w, p = [], []
w.append("r.categoria_id=?"); p.append(categoriaId)

# líneas 315-317: una lambda llamada e que arma la etiqueta de una ubicación
e = lambda i, p, rf: f"{db.execute('SELECT etiqueta FROM v_ubicacion WHERE id=?', (i,)).fetchone()['etiqueta']}" + \
    (f" ({p})" if p else "") + (f" [{rf}]" if rf else "")
cambios.append(("ubicacion", e(r["ubicacion_id"], r["parte_afectada"], r["referencia"]), e(ubic, parte, ref)))
```

**Por qué es un problema.** *Esta explicación la construimos con el agente:* en Python, `e` es por convención el nombre de una **excepción** (`except ValueError as e`); el mismo proyecto lo usa así en `main.py:68`. Quien lee `e(...)` espera un error, no una función que formatea texto. Además, dentro de la lambda, `p` significa «parte afectada», mientras que en `list_reports` `p` significa «parámetros»: la misma letra con dos significados en el mismo archivo. `w` y `p` obligan a leer cada `append` para deducir que son las condiciones del `WHERE` y sus parámetros. Un nombre debe decir qué contiene sin que haya que leer cómo se usa.

**Código corregido.**

```python
# list_reports
condiciones, parametros = [], []
if categoriaId:
    condiciones.append("r.categoria_id = ?")
    parametros.append(categoriaId)

# correct_report: función con nombre, fuera del cuerpo (también corrige la lambda asignada, flake8 E731)
def _describir_ubicacion(db, ubicacion_id: str, parte_afectada: str | None, referencia: str | None) -> str:
    etiqueta = db.execute("SELECT etiqueta FROM v_ubicacion WHERE id = ?", (ubicacion_id,)).fetchone()["etiqueta"]
    if parte_afectada:
        etiqueta += f" ({parte_afectada})"
    if referencia:
        etiqueta += f" [{referencia}]"
    return etiqueta

anterior = _describir_ubicacion(db, r["ubicacion_id"], r["parte_afectada"], r["referencia"])
nueva = _describir_ubicacion(db, ubic, parte, ref)
cambios.append(("ubicacion", anterior, nueva))
```

---

### H-6 · Seguridad: SQL armado con f-strings (revisado, no explotable hoy)

**Dónde:** líneas 128–131 (`list_reports`) y 259–260 (`find_possible_duplicates`).

**Problema.**

```python
# líneas 128-130
sql_from = "FROM reporte r" + (" WHERE " + " AND ".join(w) if w else "")
total = db.execute(f"SELECT count(*) {sql_from}", p).fetchone()[0]

# líneas 259-260
tabla = "unidad" if ubicacionTipo == "Unidad" else "area_comun"
if not db.execute(f"SELECT 1 FROM {tabla} WHERE ubicacion_id=?", (ubicacionId,)).fetchone():
```

**Por qué no es explotable hoy.** Revisamos de dónde sale cada parte del texto SQL. En `list_reports`, las piezas de `w` son texto fijo escrito en el código, y todo valor que manda el usuario va en `p` como parámetro `?`, que SQLite nunca interpreta como SQL. Incluso el filtro `texto` escapa `%`, `_` y `\` antes del `LIKE` (línea 125). En `find_possible_duplicates`, `tabla` solo puede valer `"unidad"` o `"area_comun"`, porque `ubicacionTipo` está validado como `Literal["Unidad", "AreaComun"]`.

**Por qué igual es un problema.** La seguridad depende de que **todas** las personas que editen el archivo recuerden esa regla. Bastaría un cambio como `w.append(f"r.estado = '{estado}'")` para abrir una inyección SQL (OWASP A03: Injection), y desde fuera ese código se ve igual al seguro.

**Código corregido.** Hacer explícito que el nombre de la tabla viene de una lista cerrada:

```python
TABLA_POR_TIPO = {"Unidad": "unidad", "AreaComun": "area_comun"}  # nunca valores del usuario

tabla = TABLA_POR_TIPO[ubicacionTipo]  # KeyError si llega un tipo no permitido, en lugar de armar SQL
if not db.execute(f"SELECT 1 FROM {tabla} WHERE ubicacion_id = ?", (ubicacionId,)).fetchone():
```

Y documentar la regla en el código y en la Definition of Done: «en SQL armado con f-string solo se interpolan constantes del código; todo valor del usuario va como parámetro `?`».

---

### H-7 · DRY: la expresión regular de UUID está copiada seis veces y es más débil que la del proyecto

**Dónde:** líneas 97, 98, 101, 254, 256 y 455.

**Problema.**

```python
ubicacionId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),   # línea 97 (y otras cinco)
```

`app/util.py:14` ya define `UUID_RE`, que el resto del proyecto usa. Además, las dos expresiones **no validan lo mismo**:

| Expresión | ¿Acepta `"------------------------------------"` (36 guiones)? |
|---|---|
| `r"^[0-9a-fA-F-]{36}$"` (copiada en este archivo) | **Sí** |
| `util.UUID_RE` (`8-4-4-4-12` caracteres hexadecimales) | No |

**Por qué es un problema.** Copiar la regla seis veces ya provocó una inconsistencia: el mismo dato se valida de una forma en los routers que usan `UUID_RE` y de otra en este archivo, que deja pasar valores que no son UUID. Hoy no rompe nada, porque la consulta simplemente no encuentra resultados, pero el API acepta como válido un dato que su contrato (`format: uuid`) dice que es inválido.

**Código corregido.**

```python
from ..util import UUID_RE

UuidQ = Query(None, pattern=UUID_RE)                 # parámetro opcional
UuidQReq = Query(..., pattern=UUID_RE)               # parámetro obligatorio

def list_reports(..., ubicacionId: Optional[str] = UuidQ, categoriaId: Optional[str] = UuidQ, ...)
```

---

## 4. Aspectos positivos encontrados

Un code review también registra lo que está bien, para no perderlo al refactorizar:

- **Nombre de archivo saneado** (línea 233): `re.sub(r"[^A-Za-z0-9._-]", "_", nombre)[:80]` impide que un nombre como `../../main.py` escriba fuera de la carpeta de subida (*path traversal*).
- **Folio generado dentro de una transacción `IMMEDIATE`** (línea 202): dos altas simultáneas no pueden recibir el mismo folio.
- **Limpieza de archivos si la transacción falla** (líneas 244–247): no quedan fotos huérfanas en disco.
- **Contraseñas y secretos fuera de este archivo**: el router nunca maneja credenciales; todo pasa por `security.py`.

---

## 5. Sección SOLID

**Alcance:** todo el backend (`backend/app/`), no solo `reportes.py`, porque varios principios se ven en cómo se relacionan los módulos entre sí. Las rutas son relativas a `backend/app/`.

**Cómo leer «¿Se respeta?»:** *Sí* = no encontramos violaciones; *Parcialmente* = hay partes que lo cumplen y partes que no; *No* = la violación es la regla general en el código.

### 5.1 Evaluación del código

| Principio | ¿Se respeta? | Ejemplo en el código | Propuesta de corrección |
|---|---|---|---|
| **Single Responsibility (SRP)** | **Parcialmente** | ✅ Los módulos transversales tienen una sola responsabilidad: `security.py` (autenticación y autorización), `db.py` (conexión y transacciones), `schemas.py` (validación de entrada), `config.py` (configuración). ❌ Los routers mezclan HTTP, reglas de negocio, SQL y archivos: `routers/reportes.py:137-249` (`create_report`, ocho responsabilidades, ver H-2). ❌ Los serializadores consultan la base: `serial.py:128-136` (`report_summary` hace 4 consultas por reporte). | Separar en capas por recurso: `routers/` (solo HTTP) → `servicios/` (reglas de negocio) → `repositorios/` (SQL). Mover las consultas de `serial.py` a los repositorios, para que serializar sea solo convertir datos ya leídos. |
| **Open/Closed (OCP)** | **Parcialmente** | ✅ `security.py:89-140`: los permisos son una tabla (`PERMISOS`); una ruta nueva se protege **agregando una entrada**, sin modificar `autorizar`. ✅ `main.py:21-22`: los routers se registran en un ciclo. ❌ Cadenas `if/elif` por tipo: `routers/reportes.py:353-359` (tipos de entrada de historial), `serial.py:42-54` (`user_out` por rol) y `routers/auth.py:27-42` (`sesion_usuario` por rol). Agregar un rol o un tipo de historial obliga a **modificar** esas tres funciones. | Reemplazar los `if/elif` por tablas de despacho, como ya se hace con `PERMISOS`: `DETALLE_POR_ROL = {"Residente": _detalle_residente, ...}` y `FORMATO_HISTORIAL = {"CambioEstado": _formato_cambio_estado, ...}`. Un rol o tipo nuevo se agrega con una función y una entrada en la tabla. |
| **Liskov Substitution (LSP)** | **Sí** | ✅ `schemas.py:21-22`: las 28 clases de entrada heredan de `Base` y **ninguna** cambia su `model_config` (`extra="forbid"`, `strict=True`); por eso `parsear(modelo, data)` (`schemas.py:215`) funciona igual con cualquiera de ellas. ✅ `util.py:19`: `ApiError` extiende `Exception` sin cambiar su comportamiento, y el manejador de `main.py:32-34` la atiende sin importar dónde se lanzó. **Aplicación limitada:** el código casi no usa jerarquías de clases, así que hay pocas sustituciones que evaluar. | Sin violaciones que corregir. Regla para la siguiente iteración: cuando se agreguen las abstracciones propuestas en DIP (por ejemplo, almacenamiento local y en la nube), **todas** las implementaciones deben cumplir el mismo contrato (mismos errores, misma semántica al borrar un archivo inexistente) y probarse con las mismas pruebas. |
| **Interface Segregation (ISP)** | **No** | ❌ `security.py:75-78`: `usuario_actual` devuelve la fila **completa** de `usuario` (`SELECT *`), incluidos `contrasena_hash`, `intentos_fallidos` y `bloqueado_hasta`, y se inyecta como `quien` en todos los endpoints. Los routers solo usan `id` (20 veces), `rol` (1) y `nombre` (1). ❌ `util.py` (134 líneas) junta errores, fechas, ETag, paginación y consultas de permisos (`es_administrador`, `util.py:132`): cada router importa ese módulo completo aunque use una parte. | Inyectar un objeto pequeño con solo lo necesario: `@dataclass(frozen=True) class UsuarioSesion: id: str; nombre: str; rol: str`, construido en `usuario_actual` con `SELECT id, nombre, rol, estado_cuenta`. Así el hash de la contraseña nunca sale de `security.py`. Dividir `util.py` en `errores.py`, `fechas.py` y `http.py` (ETag y paginación). |
| **Dependency Inversion (DIP)** | **No** | ❌ Los routers dependen directamente de detalles concretos: SQL de SQLite escrito en el router (`routers/reportes.py:203-243`) y el sistema de archivos local (`routers/reportes.py:229-235`: `config.UPLOAD_DIR / folio`, `write_bytes`, `shutil.rmtree`). ✅ Parcial: la conexión se inyecta con `Depends(get_db)` (`db.py:16`), lo que permite cambiarla en pruebas. | Definir abstracciones y que los routers dependan de ellas: `class AlmacenArchivos(Protocol)` con `guardar`, `borrar_carpeta`, implementada por `AlmacenLocal` (y luego `AlmacenNube`), inyectada con `Depends`. Igual para los datos: `ReporteRepositorio` con métodos como `siguiente_folio()` y `posibles_duplicados()`. |

### 5.2 Detalle de cada violación y cambio para la siguiente iteración

#### SRP — Parcialmente

**Dónde se viola.** Además de `create_report` (H-2), `serial.py` mezcla dos responsabilidades: convertir filas a JSON **y** leer la base. `report_summary` (`serial.py:128-136`) ejecuta una consulta para la categoría, otra para las detenciones y, dentro de `ubicacion_out`, dos más para la ubicación. Como `list_reports` (`routers/reportes.py:132`) la llama una vez por fila, una página de 100 reportes hace **más de 400 consultas** (problema N+1). Es una violación de SRP que además tiene costo de rendimiento.

**Cambio concreto.** Crear `repositorios/reportes.py` con una consulta que traiga el resumen ya unido:

```python
RESUMEN_SQL = """SELECT r.*, c.nombre AS categoria, v.etiqueta, u.tipo AS ubicacion_tipo,
                        EXISTS (SELECT 1 FROM detencion d WHERE d.reporte_folio = r.folio AND d.fecha_fin IS NULL) AS detenido
                 FROM reporte r JOIN categoria c ON c.id = r.categoria_id
                 JOIN ubicacion u ON u.id = r.ubicacion_id JOIN v_ubicacion v ON v.id = r.ubicacion_id"""
```

y dejar `serial.report_summary(fila)` sin el parámetro `db`: solo convierte. Una página pasa de más de 400 consultas a 2 (conteo y página).

#### OCP — Parcialmente

**Dónde se viola.** El rol del usuario se revisa con `if/elif` en tres funciones distintas (`serial.py:42-54`, `routers/auth.py:27-42`, `routers/reportes.py:148`). Si el condominio agrega un rol, por ejemplo «Comité de vigilancia» (que el SRS ya menciona), hay que encontrar y modificar cada una, y la que se olvide se comporta como si el rol no existiera.

**Cambio concreto.** El proyecto ya tiene el patrón correcto en `PERMISOS`; aplicarlo también al detalle por rol:

```python
def _detalle_residente(db, usuario) -> dict: ...
def _detalle_mantenimiento(db, usuario) -> dict: ...
def _detalle_administracion(db, usuario) -> dict: ...

DETALLE_POR_ROL = {"Residente": _detalle_residente, "Mantenimiento": _detalle_mantenimiento,
                   "Administracion": _detalle_administracion}


def user_out(db, r) -> dict:
    d = {"id": r["id"], "nombre": r["nombre"], "correo": r["correo"], "rol": r["rol"], "estadoCuenta": r["estado_cuenta"]}
    detalle = DETALLE_POR_ROL.get(r["rol"])
    return {**d, **detalle(db, r)} if detalle else d
```

Un rol nuevo agrega una función y una entrada; `user_out` no se toca.

#### LSP — Sí

No hay violaciones. Lo dejamos como regla para cuando se agreguen jerarquías: una implementación nueva de una abstracción no puede pedir más ni prometer menos que la original. Ejemplo concreto para `AlmacenArchivos`: si `AlmacenLocal.borrar_carpeta` no falla cuando la carpeta no existe (como hoy `shutil.rmtree(..., ignore_errors=True)` en `routers/reportes.py:246`), `AlmacenNube.borrar_carpeta` tampoco puede fallar; si no, la limpieza tras un error en `create_report` rompería el alta en producción y no en desarrollo.

#### ISP — No

**Dónde se viola.** Cada endpoint protegido recibe el objeto `quien` con **todas** las columnas de `usuario`, aunque solo use tres. Además de violar ISP, es un riesgo: el hash de la contraseña viaja por todo el código, y basta un `return responder(dict(quien))` por descuido para exponerlo en una respuesta.

**Cambio concreto.**

```python
@dataclass(frozen=True)
class UsuarioSesion:
    id: str
    nombre: str
    rol: str


def usuario_actual(cred=Depends(_bearer), db=Depends(get_db)) -> UsuarioSesion:
    ...
    fila = db.execute("SELECT id, nombre, rol, estado_cuenta FROM usuario WHERE id = ?", (payload["sub"],)).fetchone()
    if not fila or fila["estado_cuenta"] != "Activa":
        raise no_autenticado()
    return UsuarioSesion(fila["id"], fila["nombre"], fila["rol"])
```

Los routers cambian `quien["id"]` por `quien.id`, y mypy puede revisar que nadie pida un campo que no existe.

#### DIP — No

**Dónde se viola.** `create_report` decide **cómo** se guardan los archivos (en disco, en `config.UPLOAD_DIR`). El SRS pide lo contrario: RNF-08 exige poder cambiar el almacenamiento de disco local a la nube **sin tocar las reglas de negocio**, y el ADR-001 de S04 lo resolvía con el patrón Adapter. Hoy, mover las fotos a la nube obliga a reescribir `create_report`.

**Cambio concreto.**

```python
class AlmacenArchivos(Protocol):
    def guardar(self, carpeta: str, nombre: str, contenido: bytes) -> str: ...   # devuelve la clave guardada
    def borrar_carpeta(self, carpeta: str) -> None: ...                          # no falla si no existe


class AlmacenLocal:
    def __init__(self, raiz: Path):
        self.raiz = raiz

    def guardar(self, carpeta: str, nombre: str, contenido: bytes) -> str:
        destino = self.raiz / carpeta / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return f"{carpeta}/{nombre}"

    def borrar_carpeta(self, carpeta: str) -> None:
        shutil.rmtree(self.raiz / carpeta, ignore_errors=True)


def get_almacen() -> AlmacenArchivos:
    return AlmacenLocal(config.UPLOAD_DIR)


# create_report recibe la abstracción, no el detalle
def create_report(..., almacen: AlmacenArchivos = Depends(get_almacen)):
    ...
    clave = almacen.guardar(folio, f"{aid}_{seguro}", contenido)
```

Para usar la nube basta escribir `AlmacenNube` y cambiar `get_almacen`; `create_report` no cambia. En las pruebas se puede inyectar un almacén en memoria con `app.dependency_overrides`.

### 5.3 Prioridad de las correcciones

| Prioridad | Principio | Por qué primero |
|---|---|---|
| 1 | **ISP** (`UsuarioSesion`) | Cambio pequeño que además reduce un riesgo de seguridad (hash de contraseña en todo el código). |
| 2 | **SRP** (separar `create_report`, consultas fuera de `serial.py`) | Es la función más compleja y la que más cambia; también elimina el problema N+1. |
| 3 | **DIP** (`AlmacenArchivos`) | Requisito del SRS (RNF-08) pendiente; conviene antes de desplegar con almacenamiento en la nube. |
| 4 | **OCP** (tablas de despacho por rol) | Se vuelve urgente cuando se agregue un rol nuevo. |
