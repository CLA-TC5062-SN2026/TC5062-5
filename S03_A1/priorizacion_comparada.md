# ReportaYa · Priorización comparada del backlog

*Versión 2 de `backlog_priorizado.md`: incluye todo su contenido (secciones 1–6) y agrega la sección 7, que compara esta priorización con la del autor del proyecto.*

---

## Backlog priorizado por valor de negocio

**Rol:** Product Owner · **Insumos:** `SRS_equipo.md` v2.0 e `historias_usuario.md` (44 historias, 186 SP)

## 1. Cómo se priorizó

**Valor de negocio.** Cada historia se evalúa contra los 5 objetivos medibles del SRS (§1): **O1** registro único con folio y fecha; **O2** el residente consulta estado y visita sin preguntar; **O3** la Administración mide tiempos contra el objetivo; **O4** evidencia e historial inalterable; **O5** adopción (la meta de la cliente: que la mayoría de los reportes entre por el sistema en 3 meses).

**Método: WSJF simplificado** (Weighted Shortest Job First): `WSJF = (VN + CT + RR) ÷ SP`.

| Factor | Pregunta | Escala |
|---|---|---|
| **VN** · Valor de negocio | ¿Cuánto contribuye a O1–O5 y al problema de la cliente (reportes perdidos, duplicados, sin evidencia)? | 1, 2, 3, 5, 8, 13 |
| **CT** · Criticidad en el tiempo | ¿Bloquea a otras historias o pierde valor si se retrasa? | 1, 2, 3, 5, 8, 13 |
| **RR** · Reducción de riesgo / habilitación | ¿Reduce un riesgo del proyecto o habilita funcionalidad posterior? | 1, 2, 3, 5, 8, 13 |
| **SP** · Esfuerzo | La estimación de la historia | Fibonacci |

**Dos reglas encima del número:**
1. **El alcance mínimo de 12 semanas va primero.** Las historias de prioridad Alta (RF-01 a RF-16 y RF-27, acordadas como mínimo en el SRS §5, punto 15) se ordenan entre sí; las Media y Baja forman el Release 2. El WSJF reordena dentro de cada bloque, no cambia qué entra al mínimo.
2. **Una historia nunca va antes de lo que necesita.** Si el WSJF pide algo cuyo prerrequisito aún no está (por ejemplo, asignar sin tener usuarios), el orden final lo respeta.

## 2. Resumen del Product Owner

**Al tope (sprints 1–2):** cuenta inicial, login, padrón, usuarios y activación, y luego **reportar** (HU-10) con sus variantes baratas. Sin esto no entra ningún reporte y nada más se puede probar. Los dos primeros sprints suman 42 SP, el 23 % del esfuerzo total.

**Corazón del valor (sprints 3–5):** asignar, estados, pendientes del personal, consulta de estado del residente, terminar con evidencia y cerrar. Es el ciclo que resuelve el problema de fondo: *«nadie sabe en qué estado va cada reporte»*.

**Al fondo:** reapertura, duplicados, delegación, corrección de reportes, garantía y, sobre todo, **HU-14 (conservar capturas sin conexión, 13 SP)**. Resuelven casos reales pero menos frecuentes, o cuestan mucho para el valor que dan.

**Tres historias de prioridad Alta que el WSJF pone casi al final del mínimo:** HU-41 (tablero, 8 SP), HU-39 (búsqueda) y HU-31 (cancelar). Se justifican en §4.

## 3. Backlog ordenado

VN = valor de negocio · CT = criticidad en el tiempo · RR = reducción de riesgo · Orig. = prioridad original · Entrega = sprint propuesto (S1–S6) o Release 2 (R2).

| # | Historia | Épica | SP | VN | CT | RR | WSJF | Orig. | Entrega |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **HU-06** · Crear la primera cuenta de Administración | E1 | 2 | 5 | 13 | 3 | 10.5 | Alta | S1 |
| 2 | **HU-01** · Iniciar sesión según mi rol | E1 | 3 | 8 | 13 | 8 | 9.7 | Alta | S1 |
| 3 | **HU-02** · Mantener el padrón de unidades y áreas comunes | E1 | 3 | 5 | 8 | 5 | 6.0 | Alta | S1 |
| 4 | **HU-09** · Ajustar los plazos y umbrales del sistema | E1 | 3 | 5 | 5 | 5 | 5.0 | Alta | S1 |
| 5 | **HU-03** · Dar de alta y desactivar usuarios | E1 | 5 | 8 | 8 | 5 | 4.2 | Alta | S1 |
| 6 | **HU-05** · Activar mi cuenta y recuperar mi contraseña | E1 | 5 | 8 | 8 | 5 | 4.2 | Alta | S1 |
| 7 | **HU-10** · Reportar una falla desde mi celular | E2 | 8 | 13 | 13 | 8 | 4.2 | Alta | S2 |
| 8 | **HU-12** · Enviar el reporte aunque no tenga foto | E2 | 2 | 5 | 3 | 3 | 5.5 | Alta | S2 |
| 9 | **HU-13** · Indicar la ubicación exacta y si autorizo el acceso | E2 | 3 | 8 | 5 | 3 | 5.3 | Alta | S2 |
| 10 | **HU-16** · Registrar reportes desde la caseta | E2 | 3 | 5 | 5 | 3 | 4.3 | Alta | S2 |
| 11 | **HU-20** · Confirmar o cambiar la prioridad sugerida | E3 | 5 | 8 | 8 | 5 | 4.2 | Alta | S2 |
| 12 | **HU-21** · Asignar un reporte a un responsable | E3 | 5 | 13 | 8 | 8 | 5.8 | Alta | S3 |
| 13 | **HU-24** · Aplicar el flujo de estados del reporte | E3 | 5 | 13 | 8 | 8 | 5.8 | Alta | S3 |
| 14 | **HU-42** · Detectar fallas que se repiten | E5 | 3 | 8 | 5 | 3 | 5.3 | Alta | S3 |
| 15 | **HU-23** · Ver mis pendientes ordenados por urgencia | E3 | 3 | 8 | 5 | 3 | 5.3 | Alta | S3 |
| 16 | **HU-32** · Consultar el estado de mis reportes | E4 | 5 | 13 | 8 | 5 | 5.2 | Alta | S3 |
| 17 | **HU-27** · Registrar avances y la fecha de la visita | E3 | 3 | 5 | 5 | 3 | 4.3 | Alta | S3 |
| 18 | **HU-15** · Registrar un reporte a nombre de un residente | E2 | 5 | 8 | 8 | 5 | 4.2 | Alta | S4 |
| 19 | **HU-34** · Avisar a Mantenimiento y a la Administración, y vigilar los correos fallidos | E4 | 5 | 8 | 8 | 5 | 4.2 | Alta | S4 |
| 20 | **HU-04** · Registrar proveedores externos con o sin acceso | E1 | 3 | 3 | 5 | 3 | 3.7 | Alta | S4 |
| 21 | **HU-26** · Registrar el avance de un proveedor que no usa el sistema | E3 | 5 | 8 | 5 | 5 | 3.6 | Alta | S4 |
| 22 | **HU-33** · Recibir avisos de mis reportes | E4 | 5 | 8 | 5 | 5 | 3.6 | Alta | S4 |
| 23 | **HU-11** · Adjuntar fotos y un video al reporte | E2 | 5 | 8 | 5 | 5 | 3.6 | Alta | S5 |
| 24 | **HU-25** · Terminar un trabajo con evidencia | E3 | 5 | 13 | 8 | 8 | 5.8 | Alta | S5 |
| 25 | **HU-36** · Cerrar un reporte después de revisarlo | E4 | 5 | 8 | 5 | 8 | 4.2 | Alta | S5 |
| 26 | **HU-40** · Ver el detalle completo de un reporte | E5 | 3 | 5 | 3 | 3 | 3.7 | Alta | S5 |
| 27 | **HU-35** · Confirmar si la reparación quedó bien | E4 | 5 | 8 | 3 | 5 | 3.2 | Alta | S5 |
| 28 | **HU-22** · Reclasificar un reporte durante la atención | E3 | 3 | 3 | 3 | 3 | 3.0 | Alta | S6 |
| 29 | **HU-31** · Cancelar un reporte que ya se resolvió | E3 | 3 | 3 | 3 | 2 | 2.7 | Alta | S6 |
| 30 | **HU-41** · Ver los tiempos de atención y el cumplimiento | E5 | 8 | 8 | 5 | 5 | 2.2 | Alta | S6 |
| 31 | **HU-39** · Buscar reportes anteriores | E5 | 5 | 5 | 3 | 3 | 2.2 | Alta | S6 |
| 32 | **HU-38** · Enterarme de los reportes que no se mueven | E4 | 3 | 5 | 3 | 3 | 3.7 | Media | R2 |
| 33 | **HU-28** · Marcar un reporte como detenido | E3 | 3 | 3 | 2 | 3 | 2.7 | Media | R2 |
| 34 | **HU-44** · Exportar el tablero para la asamblea | E5 | 3 | 3 | 3 | 2 | 2.7 | Media | R2 |
| 35 | **HU-07** · Identificar al propietario de la unidad | E1 | 2 | 2 | 1 | 2 | 2.5 | Media | R2 |
| 36 | **HU-29** · Registrar el costo y quién lo pagó | E3 | 3 | 3 | 2 | 2 | 2.3 | Media | R2 |
| 37 | **HU-43** · Ver el tiempo detenido y la adopción del sistema | E5 | 3 | 3 | 2 | 2 | 2.3 | Media | R2 |
| 38 | **HU-37** · Indicar que el problema persiste y reabrir el reporte | E4 | 5 | 5 | 2 | 3 | 2.0 | Media | R2 |
| 39 | **HU-17** · Enterarme de un posible reporte duplicado | E2 | 5 | 5 | 2 | 3 | 2.0 | Media | R2 |
| 40 | **HU-30** · Marcar una reparación con garantía | E3 | 2 | 2 | 1 | 1 | 2.0 | Baja | R2 |
| 41 | **HU-08** · Delegar mis funciones a la auxiliar mientras estoy ausente | E1 | 5 | 3 | 2 | 3 | 1.6 | Media | R2 |
| 42 | **HU-18** · Unir reportes duplicados o mantenerlos independientes | E2 | 5 | 3 | 2 | 2 | 1.4 | Media | R2 |
| 43 | **HU-19** · Corregir mi reporte antes de que lo asignen | E2 | 3 | 2 | 1 | 1 | 1.3 | Baja | R2 |
| 44 | **HU-14** · No perder lo que capturé aunque falle la conexión | E2 | 13 | 5 | 2 | 3 | 0.8 | Media | R2 |

## 4. Justificación

### 4.1 Por qué estas historias van al tope

| Historia | Razón |
|---|---|
| **HU-06** Primera cuenta de Administración · WSJF 10.5 | Es la de mayor ratio: 2 SP y bloquea todo. Sin la primera cuenta nadie entra al sistema ni lo configura. |
| **HU-01** Login por rol · 9.7 | Es la puerta de todo y sostiene la matriz de visibilidad (quién ve qué). Un error aquí es de seguridad, no de comodidad. |
| **HU-02, HU-03, HU-05** Padrón, usuarios, activación | Habilitadoras. Cada reporte necesita una unidad válida (HU-10 las usa) y un usuario activo. El valor es indirecto pero ninguna otra historia funciona sin ellas. |
| **HU-09** Parámetros configurables · 5.0 | Cuesta 3 SP y evita rehacer después: los plazos (1 h, 24 h, 72 h, 168 h) vienen de entrevistas, no de un contrato (SRS S-04). Si cambian, se ajustan sin programar. |
| **HU-10** Reportar desde el celular · 4.2 | Su WSJF numérico no es el mayor porque cuesta 8 SP, pero **es la razón de ser del producto** (O1, O5). Va justo después de sus prerrequisitos, no por ratio. |
| **HU-12, HU-13** Sin foto; ubicación y acceso | Casi gratis (2 y 3 SP) y quitan barreras de adopción (O5): exigir foto haría que la gente siguiera usando WhatsApp. HU-13 captura lo que el personal necesita para ir al lugar. |
| **HU-21, HU-24, HU-25** Asignar, estados, terminar con evidencia · 5.8 | Son el ciclo operativo: la Administración asigna, Mantenimiento avanza y termina con evidencia (O4). Los tres empatan en el mayor WSJF del mínimo. |
| **HU-32** El residente consulta el estado · 5.2 | Es el beneficio visible para el residente (O2) y reduce las llamadas a la Administración. |

### 4.2 Por qué estas van a la mitad

HU-15 y HU-16 (captura a nombre del residente y desde la caseta) pesan más que su ratio sugiere: la Administración captura por los adultos mayores que no usarán el sistema (SRS, tabla de actores). Sin ellas, el sistema solo cubre a quien sabe usar la app, y la adopción (O5) se queda corta. HU-34, HU-33 y HU-26 (avisos y proveedores sin acceso) hacen que lo asignado llegue a alguien y que el trabajo de terceros quede registrado; son necesarias, pero requieren que el ciclo ya exista.

### 4.3 Por qué estas van al fondo

| Historia | Razón |
|---|---|
| **HU-14** Sin conexión · 13 SP · WSJF 0.8 | Es la menos eficiente: 13 SP (la siguiente historia más grande tiene 8) y el SRS ya la ubica en el segundo plazo (RNF-11 completo). Ataca un riesgo de conectividad que el SRS no documenta como problema principal. **Recomendación: partirla** (guardar borrador local de texto primero; fotos y reenvío después). |
| **HU-19** Corregir mi reporte · 1.3 | Pocos casos, y la Administración puede reclasificar mientras tanto (HU-22). |
| **HU-18, HU-17** Unir duplicados, avisar posible duplicado | El problema es real (el SRS lo cita: dos personas reportan lo mismo), pero hoy la Administración lo detecta a mano y puede seguir haciéndolo un tiempo. Se hace después del ciclo básico. |
| **HU-08** Delegación a la auxiliar · 1.6 | Mejora de conveniencia durante ausencias; mientras tanto el Administrador opera. |
| **HU-30, HU-29** Garantía y costo | Información útil para el comité, no necesaria para atender un reporte. |
| **HU-37** Reapertura · 2.0 | Importa cuando ya hay reportes cerrados y vencen los 30 días. No hay casos hasta que el ciclo lleve semanas operando. |

### 4.4 Tensiones: prioridad Alta, pero poco ratio

El WSJF no es una orden; es un argumento. Aquí el PO decide con juicio:

- **HU-41 Tablero de tiempos (8 SP, WSJF 2.2).** Es parte del mínimo (objetivo O3), así que se queda en el mínimo, pero va en el sprint 6, cuando ya hay datos que mostrar: un tablero sin reportes cerrados no se puede validar. **Recomendación:** partirla; entregar primero el cumplimiento por prioridad, y dejar para después los demás bloques.
- **HU-39 Búsqueda y HU-31 Cancelar (WSJF 2.2 y 2.7).** Siguen en el mínimo, pero son lo primero que se recorta si el calendario se aprieta: la Administración puede consultar el listado y el residente puede pedir la cancelación por otro medio.
- **HU-35 Confirmar solución (3.2).** Va después de HU-36 en valor, pero se entrega en el mismo sprint porque confirmar y cerrar forman una sola experiencia.
- **HU-42 Recurrentes (5.3)** sale temprano por su ratio (3 SP), pero solo muestra algo cuando hay reportes acumulados. Si se prefiere, se puede mover al sprint 5 sin costo.

## 5. Plan propuesto (6 sprints de 2 semanas)

- **Sprint 1 (semanas 1–2)** · 21 SP: HU-06, HU-01, HU-02, HU-09, HU-03, HU-05
- **Sprint 2 (semanas 3–4)** · 21 SP: HU-10, HU-12, HU-13, HU-16, HU-20
- **Sprint 3 (semanas 5–6)** · 24 SP: HU-21, HU-24, HU-42, HU-23, HU-32, HU-27
- **Sprint 4 (semanas 7–8)** · 23 SP: HU-15, HU-34, HU-04, HU-26, HU-33
- **Sprint 5 (semanas 9–10)** · 23 SP: HU-11, HU-25, HU-36, HU-40, HU-35
- **Sprint 6 (semanas 11–12)** · 19 SP: HU-22, HU-31, HU-41, HU-39
- **Release 2 (después del mínimo)** · 55 SP: HU-38, HU-28, HU-44, HU-07, HU-29, HU-43, HU-37, HU-17, HU-30, HU-08, HU-18, HU-19, HU-14

Capacidad supuesta: **~24 SP por sprint**. Es un supuesto mío: 131 SP del mínimo ÷ 6 sprints ≈ 22 SP. Hay que reemplazarlo por la velocidad real del equipo después del primer sprint. El sprint 6 queda con 5 SP de holgura.

## 6. Riesgos y supuestos

1. **Los puntajes VN/CT/RR son juicio del PO** a partir del SRS, no datos medidos. Conviene revisarlos con el equipo y, para VN, con la cliente (administración del condominio).
2. **El ciclo completo (reportar → asignar → terminar → cerrar) solo funciona hasta el sprint 5.** Si algo se atrasa, la demostración final está en riesgo. Mitigación: probar el flujo extremo a extremo con datos de ejemplo desde el sprint 3.
3. **Los estimados de SP no están calibrados**; reordenar por WSJF cambia si cambian los SP (HU-14, HU-41).
4. **Dependencias:** tomadas del SRS (por ejemplo, terminar con evidencia requiere el flujo de estados y las fotos). Si el diseño técnico revela otras, el orden se ajusta.

## 7. Comparación con la priorización del autor

### 7.1 Base de la comparación

Se comparan dos órdenes de las 44 historias (HU-01 a HU-44): el del **Product Owner** (secciones 3 a 5 de este documento) y el del **autor del proyecto** (Manuel Medina). **El autor confirmó que su orden es idéntico al de este documento.** Este documento no reproduce la lista del autor, así que la coincidencia se registra según su confirmación y no por una comparación posición por posición hecha aquí.

### 7.2 En qué coincidimos

Coincidimos en todo:

| Aspecto | Resultado |
|---|---|
| Posición de cada historia (1 a 44) | Idéntica en las 44 |
| Alcance mínimo de 12 semanas | Las mismas 31 historias de prioridad Alta (131 SP) |
| Release 2 | Las mismas 13 historias Media y Baja (55 SP) |
| Historias al tope | HU-06, HU-01, HU-02, HU-09, HU-03, HU-05, y después HU-10 |
| Historias al fondo | HU-19, HU-14 (partirla) y el resto del Release 2 |
| Tensiones señaladas en §4.4 | HU-41, HU-39 y HU-31 al final del mínimo |

### 7.3 En qué diferimos

**En nada.** No hay historias que cambien de posición, de bloque ni de release, y no hay prioridades Alta, Media o Baja que una de las dos versiones reclasifique. Por eso no hay diferencias que resolver ni propuestas de reconciliación.

### 7.4 Por qué coincidimos

Ambas priorizaciones parten de las mismas razones, que son las de la sección 4:

1. **El mismo ancla de valor.** Los 5 objetivos medibles del SRS (§1): registro único, consulta de estado por el residente, medición de tiempos, evidencia e historial, y adopción.
2. **Lo que bloquea va primero.** Cuenta inicial, login, padrón, usuarios y activación van al tope porque sin ellos no entra ningún reporte, y reportar (HU-10) va justo después de sus prerrequisitos.
3. **El ciclo operativo es el corazón.** Asignar, estados, terminar con evidencia y cerrar atacan el problema central: *«nadie sabe en qué estado va cada reporte»*.
4. **El mínimo acordado manda.** El alcance de 12 semanas (RF-01 a RF-16 y RF-27, SRS §5, punto 15) se prioriza antes que el Release 2.
5. **Lo caro y poco frecuente va al final.** HU-14 (13 SP), duplicados, delegación, garantía y reapertura aportan menos valor por punto de esfuerzo que el resto.

### 7.5 Qué significa la coincidencia, y qué no

- **Qué significa:** el orden es robusto frente a dos formas de razonarlo. Ambos llegaron a la misma secuencia y a las mismas tres excepciones (HU-41, HU-39, HU-31), lo cual da confianza en que el orden no depende de un puntaje aislado.
- **Qué no significa:** no es una validación externa. Los puntajes VN/CT/RR siguen siendo juicio del PO (§6, punto 1), y el orden está construido sobre el mismo SRS y las mismas estimaciones, así que las dos versiones comparten los mismos supuestos. Antes de dar el orden por definitivo, falta contrastarlo con la cliente (administración del condominio) y con el equipo, y recalcularlo si cambian los puntos de historia o la velocidad real.

### 7.6 Siguiente paso

Reflejar este orden en el tablero de GitHub (columna Backlog) y revisarlo en la planificación del sprint 1, con la velocidad real del equipo.
