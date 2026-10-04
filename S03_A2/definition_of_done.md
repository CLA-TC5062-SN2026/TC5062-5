# ReportaYa · Definition of Done (DoD)

**Versión 1.0** · Aplica desde el Sprint 1 · Se revisa en cada retrospectiva.

La DoD es la lista de condiciones que debe cumplir un trabajo para considerarse **terminado**. Sirve para que "hecho" signifique lo mismo para las tres personas del equipo y para que lo mostrado en la review sea realmente utilizable.

**Reglas de uso**

1. **Todo o nada.** Una historia que no cumple la DoD completa no se marca como Hecho ni suma story points a la velocidad. Vuelve al Backlog con los puntos restantes re-estimados.
2. **Cada punto es verificable.** Si no se puede comprobar con un enlace, una captura, un resultado de CI o una prueba, no cuenta.
3. **Por niveles.** La DoD de un nivel incluye la del nivel anterior.
4. Esta DoD **reemplaza y amplía** la "DoD común" de `sprint1_tareas.md`, que equivale solo al nivel 1.

## 1. Nivel tarea (cada PR)

- [ ] Trabajo hecho en una rama propia (`feature/<id>-descripcion`) y enlazado al issue de la tarea (`Closes #N`).
- [ ] Cumple el **criterio de done específico** de la tarea (el de `sprint1_tareas.md`).
- [ ] El PR fue **revisado y aprobado por una persona distinta al autor**.
- [ ] **CI en verde**: lint y pruebas pasan.
- [ ] La lógica nueva tiene **pruebas automáticas**: el caso normal y al menos un caso de error o límite.
- [ ] Sin secretos, contraseñas ni datos reales en el repositorio, y sin código de depuración ni comentado.
- [ ] Si cambia la forma de instalar o correr el proyecto, el README está actualizado.
- [ ] Los pendientes que se descubren quedan como issues enlazados, no como notas sueltas.
- [ ] Fusionado a `main` y rama eliminada.

## 2. Nivel historia de usuario

- [ ] Todas las **tareas (sub-issues)** de la historia están cerradas.
- [ ] **Todos los criterios de aceptación** de la historia (`RF-XX-AC-Y` del SRS) pasan, y cada uno tiene evidencia: una prueba automática o un caso manual registrado en el issue.
- [ ] **Desplegada en el entorno de pruebas** y verificada ahí, no solo en la computadora de quien la desarrolló.
- [ ] **QA cruzado** hecho por alguien que no escribió el backend de la historia.
- [ ] Sin defectos **críticos o altos** abiertos; los menores quedan como issues con etiqueta (ver §6).
- [ ] Los **requisitos no funcionales aplicables** del SRS se cumplen. Como mínimo:
  - Seguridad: la autorización por rol está verificada, las contraseñas se guardan con hash y los errores no revelan datos sensibles.
  - Uso en celular, en las pantallas que debe usar el residente o el personal desde el teléfono.
- [ ] Los cambios en la base de datos tienen **migración** que se aplica y se revierte sin perder datos.
- [ ] La historia es **demostrable** en la review con datos de ejemplo.
- [ ] El **Product Owner** la aceptó y el issue está en **Hecho** en el tablero, con sus story points.

## 3. Nivel sprint

- [ ] El **Sprint Goal** se verificó con la demo definida en la planeación.
- [ ] `main` está estable: el pipeline pasa y el entorno de pruebas corresponde a `main`.
- [ ] El tablero está al día: no quedan tarjetas "En progreso" sin dueño; lo no terminado volvió al Backlog y se re-estimó.
- [ ] Se registró la **velocidad real** (story points hechos y horas reales) para recalibrar la capacidad del siguiente sprint.
- [ ] La retrospectiva dejó **al menos una acción concreta** con responsable y fecha.
- [ ] El documento de planeación del sprint refleja lo que realmente se hizo.

## 4. Nivel entrega final (alcance mínimo)

- [ ] Las historias de prioridad Alta del alcance mínimo cumplen la DoD de historia, o se declaró y justificó cuáles se recortaron.
- [ ] El **flujo completo** (reportar → asignar → terminar con evidencia → cerrar) funciona de punta a punta con datos de ejemplo.
- [ ] Otra persona puede **instalar y desplegar** el sistema siguiendo solo el README.
- [ ] Hay **trazabilidad** entre requisito del SRS, historia, issue y prueba.
- [ ] Los defectos conocidos están listados, con su severidad.
- [ ] Hay una versión etiquetada (`tag`) en el repositorio.

## 5. Lo que no cuenta como "hecho"

- "Funciona en mi computadora" sin despliegue en el entorno de pruebas.
- Código fusionado sin revisión de otra persona.
- Pruebas desactivadas o marcadas como omitidas para que el CI pase.
- Criterios de aceptación "casi" cumplidos, o cumplidos solo para el caso feliz.
- Historias sin pruebas por falta de tiempo; el tiempo de pruebas ya está dentro de la estimación.
- Una pantalla sin su backend, o un endpoint sin forma de probarlo.

## 6. Severidad de defectos

| Severidad | Criterio | Efecto en la DoD |
|---|---|---|
| **Crítico** | Bloquea el flujo principal, pierde datos o permite un acceso indebido. | La historia no está hecha. |
| **Alto** | Una función de la historia no se puede usar o da un resultado incorrecto, sin alternativa razonable. | La historia no está hecha. |
| **Menor** | Defecto visual, texto o caso poco frecuente con alternativa. | Se puede aceptar si queda como issue. |

## 7. Checklist para la plantilla de PR

Se puede pegar en `.github/pull_request_template.md`:

```markdown
## Qué cambia
Closes #

## Verificación
- [ ] Cumple el criterio de done de la tarea
- [ ] Pruebas automáticas nuevas (caso normal y caso de error)
- [ ] CI en verde
- [ ] Revisado por otra persona
- [ ] Sin secretos ni código de depuración
- [ ] README actualizado (si aplica)
- [ ] Pendientes registrados como issues

## Si cierra la última tarea de una historia
- [ ] Criterios de aceptación (RF-XX-AC-Y) con evidencia
- [ ] Desplegado y verificado en el entorno de pruebas
- [ ] QA cruzado hecho
- [ ] Aceptada por el Product Owner
```

## 8. Cómo evoluciona

- La DoD se **revisa en cada retrospectiva**. Cualquier persona puede proponer un cambio.
- Un cambio se aprueba por **acuerdo del equipo** y aplica desde el siguiente sprint, no con efecto retroactivo.
- La DoD solo debería **endurecerse**, no relajarse, para cerrar un sprint. Si no alcanza el tiempo, se recorta alcance, no calidad.
- Se registra el cambio y la fecha en la tabla de abajo.

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-10-03 | Versión inicial para el Sprint 1. |

## Supuestos a confirmar con el equipo

1. **Quién es el Product Owner** que acepta las historias (aquí se asume la persona que priorizó el backlog).
2. **Cobertura mínima de pruebas:** esta versión pide pruebas para la lógica nueva, pero no fija un porcentaje. Conviene acordar uno cuando haya datos reales.
3. **Stack y herramientas de CI:** la DoD no depende de ninguno, pero el punto "lint y pruebas" requiere que el pipeline de S-3 ya exista.
4. **Entorno de pruebas:** la DoD supone que el despliegue de S-3 está operando. Antes de eso, el punto de despliegue no es verificable.
5. **Historias del Release 2:** la DoD aplica igual, pero no se evaluó con ellas.
