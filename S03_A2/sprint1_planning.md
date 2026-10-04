# ReportaYa · Sprint 1 Planning

**Sprint 1** · semanas 1–2 · Fuente de orden: `priorizacion_comparada.md` (WSJF)

## 1. Sprint Goal

> Al cierre del Sprint 1, la Administración puede entrar al sistema desplegado con la cuenta inicial, iniciar sesión con acceso limitado a su rol, cargar el padrón de unidades y áreas comunes, y cambiar los plazos y umbrales sin tocar código.

### Cómo se verifica (demo de ≤5 min)

1. Se crea la primera cuenta de Administración en un entorno limpio, y el sistema no permite crear una segunda por la misma vía.
2. Se inicia sesión con esa cuenta, y un rol sin permiso recibe rechazo en las rutas restringidas. Se prueba con una matriz de al menos un caso por rol y 0 accesos indebidos.
3. Se da de alta una unidad y un área común, se edita una, y quedan guardadas tras cerrar sesión.
4. Se cambia un plazo (por ejemplo, 72 h a 48 h), y el valor nuevo se refleja en la configuración sin redeploy.
5. Las 4 historias cumplen su Definition of Done: criterios de aceptación probados, código en `main` mediante PR revisado y desplegado.

### Por qué este objetivo

Es el primer paso del ciclo reportar → asignar → cerrar. Sin cuenta, login y padrón no se puede probar nada de lo que sigue, y HU-10 (reportar) depende de ellos.

## 2. Capacidad estimada

Supuesto: equipo de 3 personas (tres SRS individuales consolidados en `SRS_equipo.md`). Si el número cambia, la cuenta cambia proporcionalmente.

| Concepto | Cálculo | Horas |
|---|---|---|
| Horas brutas | 3 personas × 8.5 h/semana × 2 semanas | 51 |
| Ceremonias y coordinación | Planning, review, retro y syncs cortos | −9 |
| Margen por imprevistos y otras materias | ~20 % de lo restante | −8 |
| **Horas netas de desarrollo** | | **~34** |

Equivalencia inicial: **1 SP ≈ 2.5 h** (código, pruebas y PR). Capacidad: **~14 SP** (rango 12–16). Es un supuesto sin velocidad histórica; se recalibra al cerrar el sprint.

## 3. Historias seleccionadas

| Historia | Épica | SP | WSJF | Por qué entra |
|---|---|---|---|---|
| **HU-06** · Crear la primera cuenta de Administración | E1 | 2 | 10.5 | Mayor WSJF; sin ella nadie entra al sistema. |
| **HU-01** · Iniciar sesión según mi rol | E1 | 3 | 9.7 | Puerta de todo el sistema y base de la matriz de visibilidad; un error aquí es de seguridad. |
| **HU-02** · Mantener el padrón de unidades y áreas comunes | E1 | 3 | 6.0 | HU-10 necesita una unidad válida para cada reporte. |
| **HU-09** · Ajustar los plazos y umbrales del sistema | E1 | 3 | 5.0 | Los plazos vienen de entrevistas y no son firmes (SRS S-04); conviene no codificarlos fijos. |
| **Compromiso** | | **11 SP** | | ~79 % de la capacidad central de 14 SP. |
| *Meta extendida:* **HU-03** · Dar de alta y desactivar usuarios | E1 | 5 | 4.2 | Solo si el compromiso va adelantado a mitad de sprint. |

### Decisiones de selección

- **No se toman los 21 SP del plan original** (`priorizacion_comparada.md` §5). Esa cifra salía de un supuesto de ~24 SP por sprint, incompatible con 8–9 h/semana por persona, y no considera la curva de arranque del primer sprint (repositorio, entorno, despliegue, convenciones).
- **HU-03 y HU-05 quedan fuera del compromiso.** Son importantes, pero juntas suman 10 SP y desbordarían el sprint. Pasan al Sprint 2 junto con el arranque de HU-10, o antes si el equipo avanza más rápido de lo previsto.

## 4. Implicación para el calendario

Con ~14 SP por sprint, los 131 SP del alcance mínimo tomarían unos **9–10 sprints (18–20 semanas)** en lugar de 6. Si el cierre del curso está en 12 semanas, hay que decidir entre:

- **Recortar el mínimo.** HU-39 (búsqueda), HU-31 (cancelar) y HU-41 (tablero, partido en dos) ya estaban marcadas como lo primero en salir.
- **Subir las horas** de trabajo del equipo.
- **Recalibrar tras el Sprint 1** con la velocidad real, y reordenar entonces.

Conviene fijar esa decisión en la planificación del Sprint 1, no en el Sprint 4.

## 5. Riesgos y supuestos

1. Tamaño del equipo (3) y equivalencia 1 SP ≈ 2.5 h son supuestos sin datos históricos.
2. El primer sprint incluye trabajo de arranque técnico que no aparece como historia; si consume más de lo previsto, se recorta primero HU-09.
3. La matriz de roles de HU-01 debe acordarse con el equipo al inicio del sprint, porque las pruebas de acceso dependen de ella.
