# Diferencias entre los SRS individuales y su consolidación — ReportaYa

| Campo | Valor |
|---|---|
| Documento | Registro de aportes, conflictos y brechas de la consolidación |
| Fecha | 3 de octubre de 2026 |
| Origen | Sección 6 de `SRS_equipo.md` (v2.0), ampliada con los aportes de cada integrante y los criterios de resolución |
| Documentos comparados | `SRS_final.md` (**SRS-Base**, v1.2, apoyado en la entrevista con la Lic. Patricia Soto), `SRS_final_Alejandro Arreola.md` (**SRS-Arreola**, v1.1) y `SRS_finalluis.md` (**SRS-Luis**, v1.2) |
| Resultado | `SRS_equipo.md`: 27 RF, 161 criterios de aceptación `RF-XX-AC-Y`, 17 RNF y 14 RD |

Todos los identificadores (`RF-XX`, `RF-XX-AC-Y`, `RNF-XX`, `RD-XX`, `EX-XX`) de este documento se refieren a la numeración de `SRS_equipo.md`, no a la de los SRS individuales. La matriz de equivalencias está en la sección 7 de `SRS_equipo.md`.

**Advertencia sobre las fuentes.** SRS-Base se apoya en una entrevista distinta de la que usan SRS-Arreola y SRS-Luis (sesión A con un cliente simulado y sesión B con un administrador de condominio real). Parte de los conflictos viene de esa diferencia de fuentes y no de errores de redacción.

---

## 1. Qué aportó cada integrante

### 1.1 SRS-Base (`SRS_final.md`)

Es el documento que mejor cubre los **casos de borde y la operación a largo plazo**. También es el único que agrega mecanismos para reducir el trabajo manual de la administración.

| Aporte | Dónde quedó en `SRS_equipo.md` |
|---|---|
| Detección de duplicados al crear un reporte y unión de reportes | RF-17 |
| Alerta de reporte estancado con umbral por prioridad y aviso de reporte nuevo a la Administración | RF-22, RF-11-AC-1 |
| Exportación del tablero para la asamblea anual | RF-23 |
| Registro del canal de origen y métrica de adopción | RF-03, RF-04, RF-13-AC-6 |
| Reparación con garantía y retención extendida de fotos | RF-25, RNF-13 |
| Respaldo y recuperación | RNF-14 |
| Constancia de las fotos compartidas con proveedores externos | RNF-15 |
| Política de evidencia para proveedores sin acceso (terminado sin foto con justificación) | RF-08-AC-4, RF-08-AC-5, RD-09 |
| Sugerencia de prioridad por categoría y subtipo (luminaria de pasillo frente a foco de jardín) | RF-06-AC-5 a AC-8, RD-01 |
| Reapertura de reportes cerrados dentro de un periodo corto | RF-19 |
| Edición del reporte por el residente antes de asignarlo | RF-26 |
| Umbrales configurables como parámetros, no como constantes | RF-27 |
| Aviso a la Administración cuando el residente no tiene canal digital | RF-11-AC-8 |
| Criterio de desempate en la lista de mantenimiento (prioridad y antigüedad) | RF-16, RF-16-AC-3 |
| Categorías de limpieza de áreas comunes y jardinería | RD-01 |
| Estructura de ubicación (torre, piso, departamento, área común, sótano) | RD-13 |
| Recurrencia como dato que se presenta en la asamblea | RD-14 |
| Tolerancia a mala conectividad: guardar en el dispositivo y reintentar | RNF-11 |
| Disponibilidad en picos de lluvia (99 % mensual) | RNF-12 |

### 1.2 SRS-Arreola (`SRS_final_Alejandro Arreola.md`)

Es el documento más **honesto sobre lo que no se sabe** (23 dudas D-01 a D-23, sin completar con supuestos) y el que mejor modela los **roles y las reglas de negocio del condominio**.

| Aporte | Dónde quedó en `SRS_equipo.md` |
|---|---|
| Incidencia detenida con motivo y tiempo detenido separado en el tablero | RF-18, RF-13-AC-5 |
| Clasificación de responsabilidad: común, privada o por determinar | RF-06, RF-06-AC-9, RD-03 |
| Registro de costo y pagador | RF-20 |
| Identificación del propietario sin pedírselo al inquilino | RF-24 |
| Delegación temporal a la auxiliar administrativa | RF-21 |
| Vigilancia como actor que registra reportes | RF-04, RF-04-AC-5, RF-04-AC-7, RF-02-AC-8 |
| Pregunta obligatoria «¿es peligroso o está empeorando?» | RF-03-AC-6, RF-06-AC-7 |
| Atención parcial («se atendió lo urgente», con lo pendiente descrito) | RF-08-AC-7 |
| Adjuntar video | RF-05-AC-5, RF-05-AC-6 |
| Emergencias por teléfono, fuera del sistema | RD-12, EX-11 |
| Reglas de autorización de gastos y de decisiones por rol | RD-10 |
| Horarios del condominio (informativos) | RD-11, EX-09 |
| Consulta de reportes asignados sin señal | RNF-11 |
| Las cifras del tablero coinciden con sus registros | RNF-16 |
| Parte afectada dentro del departamento | RF-03-AC-8, RD-13 |
| Diferencias entre las dos entrevistas (C-1 a C-5 de su SRS) | Cuestiones abiertas, sección 5 |
| Modelo de casos de uso y matriz de participación por rol | Matriz de visibilidad (2.3) |
| Distinción entre «terminado» y «cierre» | RF-07, RF-08, RF-09 |

### 1.3 SRS-Luis (`SRS_finalluis.md`)

Es el documento más **verificable y automatizable**: los criterios de aceptación tienen datos concretos, códigos de error definidos y reglas de tiempo que se pueden probar.

| Aporte | Dónde quedó en `SRS_equipo.md` |
|---|---|
| Modelo de estados con tabla de transiciones por rol | RF-07 |
| Contrato de errores (401, 404, 403, 409, 422) y orden de precedencia | 3.0 |
| Datos de prueba comunes y reloj controlable | 3.0, RNF-10 |
| Matriz de visibilidad por rol | 2.3, RNF-05 |
| Confirmación del residente en 72 horas y condiciones de cierre | RF-09 |
| Fecha programada de visita y notas internas de avance | RF-15 |
| Ubicación de origen distinta de la observada | RF-06-AC-2, 1.3 |
| Autorización de acceso al departamento | RF-03-AC-3, RD-06, RF-16-AC-4 |
| Activación y recuperación de contraseña | RF-14 |
| Seguridad de cuentas (hash, HTTPS, expiración, bloqueo) | RNF-06 |
| Accesibilidad (WCAG 2.1 AA) | RNF-09 |
| Tablero con tiempo de primera atención, resolución y cumplimiento por objetivo | RF-13, RD-02 |
| Definición verificable de incidencia recurrente (3 en 90 días) | 1.3, RF-13-AC-2, RF-13-AC-3 |
| Tiempos objetivo en horas | RD-02 |
| Folio, fecha de aviso y rango de fechas inclusivo | 1.3 |
| Cancelación por el residente solo si ya se resolvió | RF-07-AC-6 a AC-9 |
| Correo con reintentos y aviso interno | RF-11 |
| Aviso al propietario no residente por correo, sin cuenta | RF-11-AC-2, RD-05 |
| Alta de cuentas solo por la Administración | RF-02, EX-08 |
| Trazabilidad de necesidades a requerimientos | Sección 7 |

---

## 2. Criterios que se aplicaron para resolver

Cuando dos o más SRS diferían, se aplicó este orden de prioridad:

1. **Evidencia de la entrevista con el cliente real.** Si la entrevista real respaldaba una postura, se adoptó (C-01, C-02, C-11).
2. **Verificabilidad.** Si una postura se podía probar con un criterio medible y la otra no, se adoptó la medible (C-05, C-07).
3. **Que no se pierda información ni trabajo.** Se prefirió registrar de inmediato y que la Administración decida después (C-12, C-21).
4. **Coherencia con el modelo de estados y con la matriz de visibilidad.** Una decisión no podía romper una regla ya aceptada (C-20, C-08).
5. **Alcance de 12 semanas.** Lo que no cabe no se baja de nivel; se difiere explícitamente en la priorización de la sección 5 de `SRS_equipo.md` (C-11).
6. **Cuando las posturas se complementaban,** se combinaron en lugar de elegir una (C-03, C-05, C-08).

---

## 3. Conflictos entre versiones y cómo se resolvieron

| # | Tema | SRS-Base | SRS-Arreola | SRS-Luis | **Decisión del equipo** | Aplicada en |
|---|---|---|---|---|---|---|
| C-01 | Quién cierra el reporte | Mantenimiento cierra con foto | Solo el Administrador | Solo la Administración | **Mantenimiento marca `Terminado`; solo la Administración cierra.** Lo respaldó la entrevista real y evita cierres sin revisión. | RF-07, RF-08, RF-09, RD-04 |
| C-02 | Foto al crear el reporte | Obligatoria | Opcional | Opcional (0 a 5) | **Opcional,** con solicitud visible. La cliente real dijo que no siempre debe ser obligatoria. | RF-03-AC-7, RF-05 |
| C-03 | Prioridad | Sugerida por tipo y subtipo | Manual, niveles sin definir | Manual | **Sugerida por categoría, subtipo y respuesta de peligro; decide la Administración.** Combina las tres posturas. | RF-06, RD-01 |
| C-04 | Nombres de prioridad | Urgente, Media, Baja | Sin definir | Urgente, Normal, Menor | **Urgente, Normal, Menor.** | RD-01, RD-02 |
| C-05 | Tiempos objetivo | Urgente: ver en < 1 h y atender el mismo día; Normal: 3 a 5 días hábiles; proveedores fuera de la meta | Sin objetivos | Urgente 1 h y 24 h; Normal 72 h; Menor 168 h; proveedores incluidos | **Horas de SRS-Luis** (verificables), con **cumplimiento de proveedores en un bloque aparte** (idea de SRS-Base). La diferencia con «días hábiles» se registra como decisión asumida en la sección 5. | RD-02, RF-13 |
| C-06 | Umbrales configurables | Configurables | No aplica | Fijos en el despliegue | **Configurables por el Administrador.** Evita redespliegues para ajustar números que la cliente no fijó. | RF-27 |
| C-07 | Incidencia recurrente | Mismo tipo y ubicación, sin umbral | Sin definir | 3 o más en 90 días, sin cancelados | **Definición de SRS-Luis** (única verificable), parametrizable; excluye `Unido`. | 1.3, RF-13, RD-14 |
| C-08 | Reapertura | Desde `Cerrado`, en un periodo corto | Desde `Cerrado`, decide el Administrador | Solo desde `Terminado` | **Desde `Terminado` (sin plazo) y desde `Cerrado` dentro de 30 días,** solo por la Administración, con el mismo folio e historial. | RF-07, RF-09-AC-5, RF-19 |
| C-09 | Costos | Fuera de alcance | Monto y pagador | Solo responsable; monto fuera | **Pagador y monto opcional,** solo visibles para la Administración; sin análisis de gasto. | RF-20, EX-02 |
| C-10 | Alta de cuentas | Autoregistro con validación | Sin definir | Solo la Administración | **Solo la Administración crea cuentas,** con enlace de activación (resuelve la duda sobre contraseñas). | RF-02, RF-14, EX-08 |
| C-11 | Trabajo sin conexión | Guardar y reintentar | No perder lo capturado; consulta sin señal | Fuera de alcance | **Incluido** como RNF-11, con viabilidad técnica por evaluar y posibilidad de diferirlo explícitamente. La cliente mencionó zonas sin señal. | RNF-11 |
| C-12 | Edición por el residente | Permitida antes de asignar | No se menciona | Excluida | **Permitida solo en `Reportado`,** con versiones inalterables. | RF-26 |
| C-13 | Contexto del sitio | Condominio o campus | Solo condominio | Solo condominio | **Solo condominio.** | 1.2, EX-14 |
| C-14 | Granularidad de ubicación | Torre, piso, depto., área común | Igual, más parte afectada | Torre y número, sin piso | **Torre, piso, número y parte afectada;** áreas comunes con referencia. | RF-02, RF-03, RD-13 |
| C-15 | Medios de aviso | Canal digital del residente | Sin definir | Correo y aviso interno | **Correo y aviso interno,** con reintentos; sin canal digital pasa por la Administración. | RF-11 |
| C-16 | Disponibilidad | 99 % mensual (propuesto) | Fuera de horario laboral | Sin requisito | **99 % mensual** más disponibilidad fuera de horario laboral. | RNF-12 |
| C-17 | Stack | Sin stack | FastAPI y React/Vite | FastAPI y Next.js | **Backend común; frontend por decidir** según RNF-11. Es el único conflicto que se deja abierto a propósito. | R-03, sección 4 |
| C-18 | Cuándo se avisa al residente | Solo recibido, asignado, cerrado | Sin definir | Cualquier cambio de estado | **Se avisa en alta, asignación, terminado, cierre, cancelación, unión, reapertura, detención y fecha de visita; no por `En proceso` ni por notas.** Evita avisos de más. | RF-11 |
| C-19 | Proveedor externo y el sistema | No usa el sistema | Acceso por definir | Tiene cuenta | **Dos tipos:** con acceso (cuenta) o sin acceso (contacto que la Administración actualiza). | RF-02, RF-07, RD-09 |
| C-20 | Quién actualiza por un proveedor sin acceso | Administración y Mantenimiento | No definido | No aplica | **Solo la Administración,** para no romper la regla de visibilidad por asignación. | RF-07-AC-10 |
| C-21 | Duplicados | Aviso antes de confirmar el alta; Administración une | Candidato abierto | Se cancela con motivo | **El reporte se crea de inmediato con marca de posible duplicado;** la Administración decide. No se pierde ningún aviso. | RF-17 |
| C-22 | Obligatoriedad de horarios de acceso | No aplica | Pendiente (D-17) | Autorización obligatoria | **Autorización obligatoria en unidades; horarios opcionales.** | RF-03 |

### 3.1 De quién se tomó cada resolución

| Resolución adoptada | Conflictos | Postura que prevaleció |
|---|---|---|
| Se adoptó la postura de SRS-Arreola y SRS-Luis | C-01, C-02, C-13 | Dos de tres, con apoyo de la entrevista real |
| Se adoptó la postura de SRS-Luis | C-04, C-07, C-10, C-15, C-22 | Verificabilidad y control de acceso |
| Se adoptó la postura de SRS-Base | C-06, C-12, C-19, C-21 | Evitar pérdida de reportes y redespliegues |
| Se adoptó la postura de SRS-Arreola | C-09, C-14 | Información que los otros dos omitían |
| Se combinaron dos o tres posturas | C-03, C-05, C-08, C-11, C-16, C-18, C-20 | Cada postura resolvía una parte distinta |
| Se deja abierto | C-17 | Depende de la viabilidad técnica de RNF-11 |

Conteo de los 21 conflictos resueltos (C-17 queda abierto) donde la postura de cada integrante se adoptó total o parcialmente: SRS-Luis en 12, SRS-Base en 11 y SRS-Arreola en 9. En las decisiones combinadas se cuenta a cada integrante cuya postura entró en la resolución. La cifra no mide la calidad de cada SRS; solo indica en cuántas decisiones pesó su postura.

---

## 4. Brechas incorporadas (lo que solo uno o dos SRS tenían)

| # | Brecha | Origen | Dónde quedó |
|---|---|---|---|
| G-01 | Alerta de reporte estancado y aviso de reporte nuevo | SRS-Base | RF-22, RF-11-AC-1 |
| G-02 | Exportar el tablero para la asamblea | SRS-Base | RF-23 |
| G-03 | Registro del canal de origen y métrica de adopción | SRS-Base y SRS-Luis | RF-03, RF-04, RF-13-AC-6 |
| G-04 | Retención de datos, garantía, respaldo y fotos con terceros | SRS-Base | RF-25, RNF-13, RNF-14, RNF-15 |
| G-05 | Estado «Detenida» y tiempo detenido en el tablero | SRS-Arreola | RF-18, RF-13-AC-5 |
| G-06 | Clasificación de responsabilidad (común, privada, por determinar) | SRS-Arreola | RF-06, RD-03 |
| G-07 | Identificación del propietario | SRS-Arreola y SRS-Luis | RF-24, RD-05, RF-11-AC-2 |
| G-08 | Delegación temporal a la Auxiliar | SRS-Arreola | RF-21 |
| G-09 | Vigilancia como actor que registra reportes | SRS-Arreola | RF-04, RF-02-AC-8 |
| G-10 | Emergencias por teléfono y sin integración con WhatsApp | SRS-Arreola | RD-12, EX-06, EX-11 |
| G-11 | Confirmación del residente con plazo y cierre condicionado | SRS-Luis | RF-09 |
| G-12 | Fecha programada de visita y notas internas | SRS-Luis | RF-15 |
| G-13 | Ubicación de origen distinta de la observada | SRS-Luis | RF-06-AC-2 |
| G-14 | Autorización de acceso al departamento | SRS-Arreola y SRS-Luis | RF-03, RD-06, RF-16-AC-4 |
| G-15 | Seguridad de cuentas, recuperación de contraseña y accesibilidad | SRS-Luis | RNF-06, RF-14, RNF-09 |
| G-16 | Reloj controlable para pruebas | SRS-Luis | RNF-10 |
| G-17 | Pregunta obligatoria «¿peligroso o empeorando?» | SRS-Arreola | RF-03-AC-6, RF-06-AC-7 |
| G-18 | Cancelación por el residente | SRS-Base y SRS-Luis | RF-07-AC-6 a AC-9 |
| G-19 | Gestión de usuarios de personal | SRS-Base y SRS-Luis | RF-02 |
| G-20 | Unión de reportes duplicados | SRS-Base | RF-17 |
| G-21 | Reaperturas contadas aparte de la recurrencia | SRS-Base (pendiente) | RD-14, RF-13 |
| G-22 | Categorías de limpieza y jardinería | SRS-Base | RD-01 |
| G-23 | Atención parcial («se atendió lo urgente») | SRS-Arreola | RF-08-AC-7 |
| G-24 | Video adjunto | SRS-Arreola | RF-05-AC-5, RF-05-AC-6 |

---

## 5. Lo que ya coincidía en los tres documentos

Estos requerimientos aparecían en los tres SRS y no necesitaron resolución:

- Alta de reporte con descripción, ubicación y fotos (RF-03).
- Captura de reportes en nombre de un residente (RF-04).
- Prioridad decidida por la Administración (RF-06).
- Asignación a mantenimiento o a un proveedor externo (RF-06).
- Historial de cambios con usuario, fecha y hora, sin posibilidad de borrarlo (RF-07, RNF-07).
- Notificación al reportante (RF-11).
- Consulta del estado por el residente (RF-10).
- Lista de pendientes de mantenimiento (RF-16).
- Evidencia fotográfica del trabajo (RF-08).
- Reapertura conservando el historial (RF-19).
- Tablero de tiempos e incidencias recurrentes (RF-13).
- Un residente solo ve lo suyo (RNF-05).
- Fotos tratadas como información sensible (RD-08).
- Uso desde el celular sin instalar nada (RNF-01).
- Un solo condominio (EX-07).
- Sin integración con WhatsApp (EX-06).
- Costo bajo y aprobación del comité o la asamblea (RNF-17).

---

## 6. Decisiones asumidas sin confirmación del cliente

Estas propuestas del equipo ninguna entrevista las confirmó textualmente, y `SRS_equipo.md` las trata como definitivas. Los valores numéricos se ajustan en RF-27 sin cambiar la especificación.

| Decisión | Dónde |
|---|---|
| Terminado sin foto para proveedores sin acceso, con justificación y marca de auditoría | RF-08-AC-4, RD-09 |
| 3 pantallas para registrar un reporte o terminar uno | RNF-02 |
| Disponibilidad de 99 % mensual | RNF-12 |
| Umbrales de estancamiento de 2 h, 24 h y 72 h | RF-22 |
| Reapertura de un cerrado dentro de 30 días | RF-19 |
| Confirmación del residente en 72 h (la cliente real mencionó «una semana, tal vez») | RF-09 |
| Objetivo de «Normal» de 72 horas corridas (SRS-Base decía 3 a 5 días hábiles) | RD-02 |
| Video de hasta 50 MB | RF-05 |
| Política de fotos compartidas con terceros y periodos de retención | RNF-13, RNF-15 |
| Umbral de $15,000 para autorización del comité (lo dio solo el cliente simulado) | RD-10 |

**Cuestiones que siguen abiertas** porque dependen de información que el cliente aún no ha dado: quién autoriza el acceso a un departamento (la cliente real dijo «el residente», el simulado dijo propietario o inquilino), la participación del comité y de los proveedores en el sistema, quién ve los tiempos de atención además de la Administración, y cómo identificar a usuarios que no recuerdan contraseñas.
