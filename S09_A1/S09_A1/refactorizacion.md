# Refactorización guiada — S09-A1

**Equipo 5 · TC5062 · Parte 4**

## 1. Hallazgos elegidos y por qué

De los hallazgos de `code_review.md` (H-1 a H-7) y de la evaluación SOLID (sección 5), elegimos los tres que más reducen el riesgo de cambiar el código **sin cambiar lo que hace el API**:

| # | Hallazgo | Principio | Por qué este |
|---|---|---|---|
| R-1 | **H-3** · La regla de posibles duplicados (RF-17) estaba escrita dos veces | DRY | Una regla de negocio con dos copias puede dar dos respuestas distintas. Es el cambio más seguro y deja lista la pieza que usa R-2. |
| R-2 | **H-2** · `create_report` tenía ocho responsabilidades (complejidad 26) | SRP | Es la función más compleja del backend y la que más cambia. |
| R-3 | **SOLID-ISP** · Cada endpoint recibía la fila completa del usuario, con el hash de la contraseña | ISP | Además de mejorar el diseño, reduce un riesgo de seguridad. |

**Por qué no elegimos H-1 (control de acceso).** Es el hallazgo más grave, pero no es una refactorización: corregirlo **cambia** lo que responde el API (un Residente dejaría de ver reportes ajenos). Una refactorización, por definición, cambia la estructura sin cambiar el comportamiento, y eso es lo que permite usar las pruebas existentes como red de seguridad. H-1 queda como la primera historia del siguiente sprint (ver `deuda_tecnica.md`).

## 2. Cómo verificamos que nada se rompió

1. **Antes:** las pruebas de contrato (`backend/tests/test_contrato.py`, que compara rutas, códigos y esquemas de respuesta contra `openapi_equipo.yaml`) daban **759 verificaciones, 0 fallos**.
2. Aplicamos las tres refactorizaciones, una por una, revisando después de cada una que la aplicación importara sin errores.
3. **Después:** levantamos el servidor con el código nuevo, recreamos la base (`init_db.py --reset --demo`) y volvimos a correr las pruebas: **759 verificaciones, 0 fallos**. La salida completa está en `pruebas_despues_refactorizacion.txt`.
4. Volvimos a correr el análisis estático para medir el efecto.

| Métrica | Antes | Después |
|---|---|---|
| Pruebas de contrato | 759 · 0 fallos | **759 · 0 fallos** |
| Calificación de pylint | 7.91/10 | **8.03/10** |
| Funciones con complejidad > 10 (flake8 C901) | 5 | **4** (sale `create_report`) |
| Complejidad de `create_report` | 26 | **≤ 10** (ya no se reporta) |
| Líneas de `create_report` | 112 | **32** (coordinación); la lógica pasa a 11 funciones con nombre propio |
| Errores de mypy | 18 | **17** (ver R-3) |

**Un detalle del método:** en R-2 cuidamos que las validaciones se ejecuten **en el mismo orden** que antes. Si un reporte tiene dos errores, el API responde con el primero que encuentra; cambiar el orden habría cambiado la respuesta, y las pruebas de contrato lo habrían detectado.

---

## 3. R-1 · Una sola definición de la regla de posibles duplicados (DRY)

**Archivo:** `backend/app/routers/reportes.py`

### Antes

La misma consulta estaba copiada en dos funciones: `create_report` (líneas 205–214 originales) y `find_possible_duplicates` (líneas 262–270). Los estados finales aparecían como texto literal en las dos y otra vez en `correct_report` (línea 285).

```python
# create_report (líneas 205-214)
if es_unidad:  # RF-17: mismo piso de la misma torre y misma categoría, abierto
    dup = db.execute("""SELECT r.folio FROM reporte r JOIN unidad u1 ON u1.ubicacion_id = r.ubicacion_id
                        JOIN unidad u2 ON u2.ubicacion_id = ?
                        WHERE r.categoria_id=? AND r.estado NOT IN ('Cerrado','Cancelado','Unido')
                          AND u1.torre = u2.torre AND u1.piso = u2.piso
                        ORDER BY r.fecha_aviso DESC, r.folio DESC LIMIT 1""", (ubic, d.categoriaId)).fetchone()
else:
    dup = db.execute("""SELECT folio FROM reporte WHERE categoria_id=? AND ubicacion_id=?
                        AND estado NOT IN ('Cerrado','Cancelado','Unido')
                        ORDER BY fecha_aviso DESC, folio DESC LIMIT 1""", (d.categoriaId, ubic)).fetchone()

# find_possible_duplicates (líneas 262-270): las mismas dos consultas, sin LIMIT 1
if ubicacionTipo == "Unidad":
    filas = db.execute("""SELECT r.* FROM reporte r JOIN unidad u1 ON u1.ubicacion_id=r.ubicacion_id
                          JOIN unidad u2 ON u2.ubicacion_id=? WHERE r.categoria_id=?
                          AND r.estado NOT IN ('Cerrado','Cancelado','Unido') AND u1.torre=u2.torre AND u1.piso=u2.piso
                          ORDER BY r.fecha_aviso DESC, r.folio DESC""", (ubicacionId, categoriaId)).fetchall()
else:
    filas = db.execute("""SELECT * FROM reporte WHERE categoria_id=? AND ubicacion_id=?
                          AND estado NOT IN ('Cerrado','Cancelado','Unido') ORDER BY fecha_aviso DESC, folio DESC""",
                       (categoriaId, ubicacionId)).fetchall()

# correct_report (línea 285)
if r["estado"] in ("Cerrado", "Cancelado", "Unido"):
```

### Después

```python
ESTADOS_FINALES = ("Cerrado", "Cancelado", "Unido")                       # línea 28


def _posibles_duplicados(db, ubicacion_tipo: str, ubicacion_id: str, categoria_id: str) -> list:   # línea 95
    """RF-17: reportes abiertos de la misma categoría en el mismo piso de la misma torre (unidades)
    o en la misma área común, del más reciente al más antiguo. Única definición de la regla."""
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


# al registrar (dentro de _registrar_reporte, ver R-2): el más reciente
duplicados = _posibles_duplicados(db, ubicacion_tipo, valores["ubicacion_id"], valores["categoria_id"])
valores["posible_duplicado_de"] = duplicados[0]["folio"] if duplicados else None

# find_possible_duplicates: todos
filas = _posibles_duplicados(db, ubicacionTipo, ubicacionId, categoriaId)

# correct_report
if r["estado"] in ESTADOS_FINALES:
```

### Justificación técnica

- **Una regla, un lugar.** RF-17 ahora vive en una función con nombre y docstring que cita el requisito. Si la Administración decide excluir también `Terminado`, se cambia `ESTADOS_FINALES` y lo ven por igual la consulta previa (`find_possible_duplicates`), el alta (`create_report`) y la corrección (`correct_report`). Antes había que acordarse de tres lugares.
- **Mismo resultado que antes.** Las consultas originales tenían el mismo `WHERE` y el mismo `ORDER BY`; la de `create_report` solo agregaba `LIMIT 1`. Tomar el primer elemento (`duplicados[0]`) de la lista ordenada da el mismo folio. Las pruebas de contrato de `GET /reports/possible-duplicates` y de `posibleDuplicado` en el alta siguen pasando.
- **Sin riesgo de inyección.** El f-string solo interpola `marcadores` (una cadena de `?` generada a partir de una constante del código); los estados y los identificadores siguen yendo como parámetros.
- **Costo aceptado:** en el alta ahora se leen todos los duplicados en lugar de uno. En un condominio (RNF-03: hasta 100 reportes al mes) son pocas filas; si algún día importara, se agrega un parámetro `limite` a la función, sin volver a copiar la regla.

---

## 4. R-2 · `create_report` dividida por responsabilidades (SRP)

**Archivo:** `backend/app/routers/reportes.py`

### Antes

Una sola función de 112 líneas (137–249), complejidad ciclomática 26, 40 variables locales. Fragmento representativo (la versión completa es la del repositorio del equipo `TC5062-5`, antes de esta actividad):

```python
@router.post("/reports")
def create_report(datos: str = Form(...), fotos: list[UploadFile] = File(default=[]), ...):
    try:
        d = S.parsear(S.ReportCreate, json.loads(datos))
    except json.JSONDecodeError:
        raise peticion_invalida("La parte `datos` no es un JSON válido")       # sin `from`: se pierde la causa
    ...
    es_residente = quien["rol"] == "Residente"
    captura = [c for c in ("medioOrigen", "fechaAviso", ...) if c in d.model_fields_set]
    if es_residente and captura:
        raise prohibido(...)
    ...                                                  # 25 líneas de reglas de negocio
    aceptados, rechazados = [], []
    candidatos = [(f, "Foto") for f in fotos] + ...
    for f, tipo in candidatos:                           # 15 líneas de validación de archivos
        ...
    carpeta = None
    try:
        with tx(db, immediate=True):
            n = db.execute("SELECT COALESCE(MAX(...") ...  # folio
            if es_unidad: dup = ...                        # duplicados (copia de la regla, ver R-1)
            db.execute("""INSERT INTO reporte (...) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'Reportado',?,?,?,?,?,?,?,?,?)""",
                       (folio, aviso, ahora, medio, descripcion, parte, ref, int(d.esPeligroso),
                        None if d.autorizaAcceso is None else int(d.autorizaAcceso), ...))   # 21 valores por posición
            ...                                            # historial
            for nombre, tipo, ctype, contenido in aceptados:   # archivos a disco
                ...
    except BaseException:
        ...
```

### Después

`create_report` queda como **coordinadora**: dice qué pasos hay y en qué orden, y cada paso es una función con nombre, docstring y un requisito del SRS.

```python
@router.post("/reports")                                                    # línea 298
def create_report(datos: str = Form(...), fotos: list[UploadFile] = File(default=[]),
                  video: Optional[UploadFile] = File(default=None),
                  idempotency_key: Optional[str] = Header(default=None),  # aceptado; ver revision_sql.md
                  db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    """Coordina el alta: valida en el orden del contrato y registra en una transacción."""
    d = _leer_datos(datos)
    if len(fotos) > 5:
        raise validacion("fotos", "Máximo 5 fotos por reporte")
    es_residente = quien.rol == "Residente"
    _validar_campos_de_captura(d, es_residente)
    descripcion = _descripcion(d.descripcion)
    _, subtipo, prioridad_base = _resolver_categoria(db, d.categoriaId, d.subtipo)
    ubicacion_id, parte, referencia = _resolver_ubicacion(db, d.ubicacion)
    _validar_acceso(d)
    ahora = now_utc()
    medio, aviso = _origen_del_aviso(d, es_residente, ahora)
    reportante = _reportante(db, d, quien, es_residente)
    aceptados, rechazados = _validar_archivos(fotos, video)

    valores = {
        "fecha_aviso": aviso, "fecha_captura": ahora, "medio_origen": medio, "descripcion": descripcion,
        ...
        "reportante_id": reportante, "capturado_por": quien.id, "categoria_id": d.categoriaId, ...
    }
    folio = _registrar_reporte(db, valores, d.ubicacion.tipo, aceptados, rechazados)
    detalle = report_detail(db, _reporte(db, folio))
    return responder({**detalle, "archivosRechazados": rechazados}, 201, f"/reports/{folio}", etag=True, etag_de_recurso=detalle)
```

Funciones extraídas (todas en `reportes.py`):

| Función | Línea | Responsabilidad | Antes estaba en |
|---|---|---|---|
| `_leer_datos` | 159 | JSON de la parte `datos` → `ReportCreate` (ahora con `raise ... from exc`) | 142–145 |
| `_validar_campos_de_captura` | 167 | RF-04: un Residente no envía campos de captura | 148–152 |
| `_validar_acceso` | 173 | Autorización y horarios de acceso a la unidad | 157–161 |
| `_origen_del_aviso` | 181 | Medio de origen y fecha de aviso según quién captura | 162–172 |
| `_reportante` | 196 | Quién es el residente que reporta | 173–181 |
| `_validar_archivos` | 209 | RF-05: tipo, tamaño y archivo vacío, uno por uno | 183–198 |
| `_siguiente_folio` | 232 | Folio consecutivo `RY-000000` | 203–204 |
| `_insertar_reporte` | 238 | `INSERT` del reporte y su primera entrada de historial | 215–227 |
| `_guardar_adjuntos` | 253 | Escribir archivos y registrar cada adjunto | 228–243 |
| `_registrar_reporte` | 276 | La transacción completa y la limpieza si falla | 200–247 |
| `_posibles_duplicados` | 95 | RF-17 (R-1) | 205–214 |

Además del cambio de estructura, el `INSERT` pasó de 21 parámetros **por posición** (`?,?,?...`) a parámetros **con nombre** (`:fecha_aviso, :descripcion, ...`) a partir del diccionario `valores`. Con 21 valores en fila era fácil intercambiar dos sin que nada fallara; con nombres, cada valor dice a qué columna va.

### Justificación técnica

- **Cada regla se puede cambiar y probar sola.** Cambiar el tamaño máximo de una foto ahora significa leer `_validar_archivos` (22 líneas), no 112. `_validar_archivos` y `_origen_del_aviso` no dependen de FastAPI ni de una petición completa, así que se pueden probar con pruebas unitarias directas.
- **Se lee como el caso de uso.** El cuerpo de `create_report` es casi la lista de pasos de RF-03 y RF-04 del SRS: leer, validar captura, descripción, categoría, ubicación, acceso, origen, reportante, archivos, registrar.
- **Mismo comportamiento.** Las validaciones conservan exactamente el orden original (por ejemplo, la de captura del Residente sigue antes que la de descripción), así que cada petición inválida recibe el mismo primer error que antes. La transacción `IMMEDIATE` sigue cubriendo folio, duplicados, inserción y adjuntos, y la limpieza de archivos ante un error sigue igual.
- **Medido:** la complejidad de `create_report` bajó de 26 a menos de 10 (flake8 ya no la reporta), sus variables locales de 40 a 23, y el `raise` sin `from` de la línea 145 (IM-2) quedó corregido de paso.

---

## 5. R-3 · El usuario autenticado como un objeto pequeño (ISP)

**Archivos:** `backend/app/security.py`, `backend/app/routers/auth.py` y los routers que reciben `quien` (`reportes.py`, `usuarios.py`, `avisos.py`, `catalogo.py`).

### Antes

```python
# security.py:63-78
def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer), db=Depends(get_db)):
    ...
    fila = db.execute("SELECT * FROM usuario WHERE id = ?", (payload["sub"],)).fetchone()
    if not fila or fila["estado_cuenta"] != "Activa":
        raise no_autenticado()
    return fila          # las 8 columnas, incluidas contrasena_hash, intentos_fallidos y bloqueado_hasta

# security.py:143-148
def autorizar(request: Request, usuario=Depends(usuario_actual)):
    ...
    if roles is None or usuario["rol"] not in roles:

# en los routers (22 usos): solo se leen id, rol y nombre
def create_note(..., quien=Depends(actor)):
    eid = _historial(db, folio, quien["id"], "Nota")
```

### Después

```python
# security.py:64-74
@dataclass(frozen=True)
class UsuarioSesion:
    """Lo único que los endpoints necesitan del usuario autenticado (ISP). El hash de la contraseña,
    los intentos fallidos y el bloqueo nunca salen de este módulo."""
    id: str
    nombre: str
    rol: str

    @classmethod
    def de_fila(cls, fila) -> "UsuarioSesion":
        return cls(fila["id"], fila["nombre"], fila["rol"])


# security.py:77-92
def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer), db=Depends(get_db)) -> UsuarioSesion:
    ...
    fila = db.execute("SELECT id, nombre, rol, estado_cuenta FROM usuario WHERE id = ?", (payload["sub"],)).fetchone()
    if not fila or fila["estado_cuenta"] != "Activa":
        raise no_autenticado()
    return UsuarioSesion.de_fila(fila)


# security.py:157
def autorizar(request: Request, usuario: UsuarioSesion = Depends(usuario_actual)) -> UsuarioSesion:
    ...
    if roles is None or usuario.rol not in roles:

# en los routers
def create_note(..., quien: UsuarioSesion = Depends(actor)):
    eid = _historial(db, folio, quien.id, "Nota")

# auth.py: login construye el mismo objeto a partir de la fila que ya leyó
"usuario": sesion_usuario(db, UsuarioSesion.de_fila(u))
```

### Justificación técnica

- **ISP:** cada endpoint depende solo de lo que usa (`id`, `nombre`, `rol`). Antes dependía de las 8 columnas de `usuario`, así que un cambio en esa tabla podía afectar a cualquier endpoint.
- **Seguridad:** el hash de la contraseña, los intentos fallidos y el bloqueo ya **no salen de la base** en cada petición; ni siquiera se leen. Un `return responder(dict(quien))` por descuido ya no puede exponerlos. Además la consulta es más chica.
- **Errores detectables antes de ejecutar.** Con la fila, `quien["rool"]` (un error de dedo) solo fallaba al ejecutar ese endpoint. Con la dataclass, mypy lo detecta sin ejecutar nada. `frozen=True` impide que un endpoint cambie por error los datos del usuario de la sesión.
- **Efecto en mypy (18 → 17 errores).** Al tener tipo, mypy pudo revisar código que antes daba por bueno. Desaparecieron 2 falsos positivos de `create_report` (R-2 hizo explícitos los tipos) y apareció **1** advertencia nueva del mismo patrón ya clasificado como IM-4 (`avisos.py:28`, lista de parámetros inferida como `list[str]`). En `auth.py` la misma inferencia apareció y la corregimos anotando `d: dict[str, Any]`.
- **Mismo comportamiento.** `crear_token` sigue recibiendo la fila completa en el login (necesita leerla para validar la contraseña), y `/auth/me` y `/auth/login` devuelven el mismo `SesionUsuario`; las pruebas de autenticación del contrato siguen pasando.

---

## 6. Resumen de cambios

| Archivo | Cambio |
|---|---|
| `app/routers/reportes.py` | R-1, R-2 y R-3: `_posibles_duplicados`, `ESTADOS_FINALES`, 11 funciones extraídas de `create_report`, `quien.<campo>` |
| `app/security.py` | R-3: `UsuarioSesion`, `usuario_actual` y `autorizar` tipados |
| `app/routers/auth.py` | R-3: `sesion_usuario` recibe `UsuarioSesion` |
| `app/routers/usuarios.py`, `avisos.py`, `catalogo.py` | R-3: `quien.id` en lugar de `quien["id"]` |

Pruebas: **759 verificaciones, 0 fallos** antes y después (`pruebas_despues_refactorizacion.txt`).
