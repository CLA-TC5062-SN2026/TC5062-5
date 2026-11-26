# Priorización comparada — ReportaYa

| Campo | Valor |
|---|---|
| Actividad | S03-A1 · Product Backlog de SCRUM |
| Base | `SRS_equipo.md` (v2.0) y `backlog_completo.md` |
| Perspectiva | Product Owner |
| Fecha | 4 de octubre de 2026 |

Este documento ordena las 15 historias de `backlog_completo.md` desde la perspectiva del Product Owner. No cambia ninguna historia ni sus Story Points, criterios de aceptación o épicas: solo propone su **orden** de entrega y lo compara con la prioridad que asignó el equipo (Alta, Media, Baja).

---

## 1. Criterio de priorización del Product Owner

La prioridad del equipo se basa en una regla de alcance: Alta si el RF está en el mínimo de 12 semanas (sección 5, punto 15 del SRS). Esa regla dice **qué** entra en las 12 semanas, pero no **en qué orden**: deja 13 historias empatadas en Alta. El Product Owner las ordena con cuatro criterios, en este orden de peso:

1. **Dependencia.** Una historia no se puede demostrar ni probar si la que la habilita no existe (por ejemplo, no hay asignación sin un reporte registrado).
2. **Valor temprano.** Primero el flujo de punta a punta más corto que resuelve el problema del condominio: que un reporte se registre, se asigne, se atienda y se cierre con evidencia. Un flujo incompleto no le sirve a la Administración aunque cada parte esté terminada.
3. **Valor de negocio.** Impacto en los objetivos medibles del SRS (1.2): registro único, consulta sin preguntar, tiempo contra objetivo, evidencia y adopción.
4. **Riesgo.** Las historias grandes o con dependencias externas (correo, cálculos de tiempo) van con margen suficiente antes del fin de las 12 semanas, para que un retraso no deje fuera el alcance mínimo.

## 2. Orden propuesto por el Product Owner

| Posición | ID | Historia resumida | SP | Prioridad del equipo | Motivo de la posición |
|---|---|---|---|---|---|
| 1 | HU-02 | Activar la cuenta, iniciar sesión por rol y recuperar la contraseña | 5 | Alta | Dependencia técnica de todo: el comando de arranque crea al primer Administrador (RF-14-AC-4) y el control por rol protege cada petición (RNF-05). También integra temprano el servicio de correo. |
| 2 | HU-01 | Administrar el padrón | 5 | Alta | Sin unidades, áreas comunes, residentes ni responsables no se puede registrar ni asignar ningún reporte. |
| 3 | HU-03 | El residente reporta con ubicación, fotos y video | 8 | Alta | Inicio del flujo principal y primer elemento del alcance mínimo. Además, ataca pronto el riesgo técnico de la carga de archivos (RNF-04, RNF-08). |
| 4 | HU-04 | Captura de reportes que llegan por otro medio | 5 | Alta | Permite que la Administración use el sistema desde el primer día, aunque los residentes todavía reporten por WhatsApp o caseta. Reutiliza el formulario de HU-03. |
| 5 | HU-06 | Clasificar, asignar, reclasificar o cancelar | 8 | Alta | Segundo paso del flujo: sin asignación, Mantenimiento no recibe trabajo. |
| 6 | HU-07 | Mantenimiento ve sus asignados, inicia la atención, notas y fecha de visita | 8 | Alta | Tercer paso del flujo: el reporte asignado empieza a avanzar. |
| 7 | HU-09 | Marcar `Terminado` con evidencia | 5 | Alta | Cuarto paso del flujo: la evidencia del trabajo (objetivo medible 4). |
| 8 | HU-12 | Confirmación del residente, cierre o reapertura | 8 | Alta | Cierra el flujo de punta a punta. Desde aquí el sistema ya sustituye a la libreta. |
| 9 | HU-10 | El residente consulta el estado y cancela un reporte ya resuelto | 5 | Alta | Cumple el objetivo medible 2 (consultar sin preguntar) y reduce las llamadas a la Administración. Depende de que haya estados que consultar. |
| 10 | HU-11 | Avisos por correo y en el sistema | 8 | Alta | Lleva el seguimiento al residente y al propietario no residente. Va después de HU-10 porque los avisos informan cambios que el residente ya puede consultar. |
| 11 | HU-15 | Tablero de tiempos, recurrencia y adopción | 13 | Alta | Necesita un flujo completo que genere datos. Es la historia más grande, así que se inicia con margen dentro de las 12 semanas. |
| 12 | HU-14 | Búsqueda e historial | 5 | Alta | Su valor crece cuando ya hay reportes acumulados. Mientras tanto, la Administración consulta el detalle de cada reporte desde el propio flujo. |
| 13 | HU-08 | Detener y reanudar un reporte | 3 | Media | Se sube por encima de una historia Alta (HU-13): completa criterios del mínimo (RF-10-AC-6, RF-13-AC-5 y el campo «marca de detenido» de RF-16) y es barata. |
| 14 | HU-13 | Parámetros configurables | 3 | Alta | Los valores iniciales de RF-27 permiten operar sin la pantalla de edición. Su valor aparece cuando la Administración quiere ajustar un número tras usar el sistema. |
| 15 | HU-05 | Exportar el tablero a PDF | 3 | Media | Depende de HU-15 y su valor se concentra en el momento de presentar al comité o a la asamblea. |

**Puntos acumulados:** el flujo de punta a punta (posiciones 1 a 8) suma 52 SP; las historias Alta del equipo llegan a 86 SP hasta la posición 14, con HU-08 (3 SP) intercalada.

## 3. Comparación entre la priorización del equipo y la del Product Owner

### 3.1 Coincidencias importantes

- Las 13 historias que el equipo marcó Alta siguen dentro del alcance de 12 semanas en el orden del Product Owner. Ninguna se saca del mínimo.
- HU-05 (exportación) queda al final en ambos enfoques: es de segunda fase y depende de HU-15.
- Las dos historias Media son las únicas de segunda fase en ambos casos, y RF-17 sigue diferido.
- Ambos enfoques reconocen las dependencias de HU-08 con criterios del alcance mínimo.

### 3.2 Historias que el Product Owner subiría

| Historia | Cambio | Razón |
|---|---|---|
| HU-04 (captura de terceros) | Al 4.º lugar, junto a HU-03. | **Negocio:** al inicio casi todos los avisos siguen llegando por WhatsApp, llamada o caseta; sin HU-04 la Administración no puede dejar la libreta. Además, RF-04 alimenta la métrica de adopción (RF-13-AC-6), que necesita datos desde el principio. **Técnica:** reutiliza el formulario y las validaciones de HU-03, por lo que construirla enseguida es barato. |
| HU-08 (detención) | De Media a la posición 13, por encima de HU-13 (Alta). | **Técnica:** tres criterios del alcance mínimo no se pueden verificar completos sin ella. **Costo:** 3 SP. |

### 3.3 Historias que el Product Owner bajaría

| Historia | Cambio | Razón |
|---|---|---|
| HU-13 (parámetros) | A la posición 14, aunque es Alta. | **Negocio:** la Administración necesita editar los valores solo después de usar el sistema y ver que no se ajustan. Los valores iniciales de RF-27 bastan para operar. **Riesgo:** es la historia Alta más expuesta a quedar fuera si la velocidad del equipo es menor a la esperada. Para mitigarlo, el equipo debe leer los valores desde un lugar configurable desde HU-12 y HU-15, de modo que HU-13 solo agregue la edición y sus validaciones. Si el riesgo se materializa, la decisión de diferirla debe quedar escrita en la sección 5 del SRS, como exige el punto 15. |
| HU-14 (búsqueda) | Después de HU-15. | **Negocio:** con pocos reportes, la búsqueda aporta poco; el tablero, en cambio, es lo que la Administración presenta para justificar el sistema (S-07). |

## 4. Análisis de puntos clave

### 4.1 Por qué HU-03, HU-06, HU-07, HU-09 y HU-12 son centrales

Juntas forman el flujo de estados del SRS (RF-07): `Reportado → Asignado → En proceso → Terminado → Cerrado`. HU-03 crea el reporte, HU-06 lo asigna, HU-07 lo pone `En proceso`, HU-09 lo termina con evidencia y HU-12 lo cierra. Cada una depende de la anterior, y si falta cualquiera, el reporte se queda atorado en un estado y el sistema no sustituye a la libreta. Cubren cuatro de los cinco elementos del alcance mínimo de la sección 1.2: alta con fotos, clasificación y asignación, seguimiento y cierre con evidencia. Por eso el Product Owner las entrega juntas y sin interrupciones (salvo HU-04, que no bloquea el flujo y es barata). Al terminar la posición 8 hay un producto usable de punta a punta.

### 4.2 Dónde va HU-15 (tablero)

En la posición 11, después del flujo completo, la consulta del residente y los avisos. Va ahí porque:

- **Dependencia de datos:** los tiempos de primera atención y de resolución necesitan los pasos a `En proceso` y a `Terminado` (HU-07, HU-09), y la adopción necesita el medio de origen (HU-03, HU-04). Antes no hay nada que medir.
- **Riesgo:** con 13 SP es la historia más grande y compleja (cumplimiento con vencimientos, recurrencia con ventana de 90 días). No debe quedar al final de las 12 semanas sin margen para corregir cifras (RNF-16).
- **Valor de negocio:** es el quinto elemento del alcance mínimo y lo que respalda ante el comité el objetivo de adopción (la mayoría de los reportes por el sistema en 3 meses). Por eso va antes que la búsqueda (HU-14).

### 4.3 HU-05 (exportación PDF) frente a historias de valor operativo

Debe ir **después** de todas las historias de valor operativo. Sin HU-15 no hay qué exportar, y el PDF no cambia cómo se atiende ningún reporte: sirve para rendir cuentas, no para operar. Además, RF-23 es de segunda fase. La excepción sería que la asamblea anual o una sesión del comité cayera dentro de las 12 semanas. En ese caso, el Product Owner la subiría justo después de HU-15, porque cuesta solo 3 SP y la aprobación del gasto (S-07) condiciona la continuidad del sistema. El SRS no da esa fecha; es contexto que debe aportar el negocio.

### 4.4 HU-01 y HU-02 al principio

Sí deben ir al principio, aunque ningún actor obtiene de ellas valor de negocio directo: nadie quiere «iniciar sesión», quiere reportar o cerrar. Las razones son técnicas:

- **Dependencia:** toda acción del SRS requiere sesión y rol (RF-01, contrato de errores 3.0), y todo reporte requiere unidades, áreas comunes y responsables (RF-02).
- **Riesgo:** la matriz de visibilidad (RNF-05) y la seguridad de cuentas (RNF-06) son más baratas de construir desde el inicio que de agregar después a cada endpoint.
- **Integración temprana:** HU-02 obliga a conectar el servicio de correo externo (RF-14), que luego reutiliza HU-11.

Para no retrasar el valor, el Product Owner pediría implementarlas en su versión completa, pero sin pulir la interfaz del padrón más allá de lo necesario para cargar el condominio de prueba (sección 3.0 del SRS).

## 5. Justificación de las historias más y menos prioritarias

**Las 3 más prioritarias:**

1. **HU-02 (acceso):** es la condición técnica de todo lo demás y concentra decisiones de seguridad que no conviene posponer.
2. **HU-01 (padrón):** sin ubicaciones ni personas registradas no existe ningún reporte posible.
3. **HU-03 (alta del residente):** es la primera historia con valor de negocio directo, abre el flujo principal y adelanta el riesgo técnico de archivos.

**Las 3 menos prioritarias:**

1. **HU-08 (detención):** es de segunda fase y el flujo funciona sin ella. Va antes que HU-13 y HU-05 por su costo bajo y porque completa criterios del mínimo.
2. **HU-13 (parámetros):** los valores iniciales permiten operar; su valor llega cuando hay experiencia de uso. Bajarla es un riesgo controlado, siempre que el diseño lea los valores desde un lugar configurable.
3. **HU-05 (exportación PDF):** depende de HU-15, es de segunda fase y sirve para rendir cuentas, no para operar. Solo se adelantaría si hubiera una asamblea o sesión del comité dentro de las 12 semanas.

## 6. Conclusión

La prioridad del equipo resolvió bien **qué** entra en las 12 semanas porque se derivó de una regla explícita del SRS, pero dejó 13 historias empatadas. Una priorización automática, sea por regla o generada por IA, no tiene la información para ordenarlas: no sabe cuándo es la asamblea, cuántos avisos siguen llegando por WhatsApp, qué tan rápido avanza el equipo ni cuánto tolera la Administración operar con los valores iniciales. Esos factores cambiaron el orden en este documento: HU-04 sube, HU-13 baja y HU-08 supera a una historia Alta. El Product Owner aporta ese contexto de negocio y asume la responsabilidad del orden. Por eso la priorización automática sirve como punto de partida trazable, pero no sustituye la decisión del Product Owner.
