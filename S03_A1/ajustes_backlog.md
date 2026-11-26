# Ajustes al Product Backlog — ReportaYa

| Campo | Valor |
|---|---|
| Actividad | S03-A1 · Product Backlog de SCRUM |
| Documento final | `backlog_completo.md` |
| Fuente de verdad | `SRS_equipo.md` (v2.0) |
| Fecha | 4 de octubre de 2026 |

## 1. Introducción

El Product Backlog de ReportaYa se construyó a partir de una propuesta inicial generada por un agente de IA: 5 épicas y 15 historias de usuario (97 SP) derivadas de `SRS_equipo.md`. Antes de aceptarla, el equipo la revisó críticamente contra el SRS y contra los objetivos del condominio, y pidió ajustes concretos. Este documento registra esos ajustes y su justificación. El resultado es la versión final de `backlog_completo.md` (15 historias, 92 SP).

## 2. Ajustes realizados

| Elemento ajustado | Propuesta inicial | Ajuste realizado | Justificación |
|---|---|---|---|
| HU-05 | Detección y unión de reportes duplicados (RF-17), prioridad Baja, 8 SP, en EP-02. | Se sustituyó por la exportación del tablero a PDF (RF-23), prioridad Media, 3 SP, en EP-05. | RF-23 pertenece formalmente a la segunda fase, pero permite presentar las métricas al comité o a la asamblea y apoya el supuesto S-07 (el comité aprueba el gasto si se le presentan métricas). Aporta más valor de negocio inmediato por menos esfuerzo que RF-17. |
| RF-17 (duplicados) | Tenía historia propia (HU-05). | Quedó sin historia y se difiere explícitamente a segunda fase. | El alcance mínimo funciona sin RF-17: el reporte duplicado no se pierde y la Administración puede cancelarlo con motivo (RF-07-AC-5). Los criterios que dependen de `Unido` (RF-10-AC-5 y parte de RF-07-AC-3) quedan anotados en el backlog. |
| HU-08 (detención, RF-18) | Prioridad Media. | Se mantuvo en Media. | RF-18 pertenece a la segunda fase, pero hay criterios del alcance mínimo que dependen parcialmente de la marca de detenido (campo de RF-16, RF-10-AC-6 y RF-13-AC-5). Por eso queda por encima del resto de la segunda fase, sin llegar a Alta. |
| Referencia del alcance mínimo de 12 semanas | Había dos definiciones posibles: la resumida de la sección 1.2 (cinco funciones) y la de la sección 5, punto 15 (RF-01 a RF-16 y RF-27). | Se adoptó RF-01 a RF-16 y RF-27 como referencia formal; la sección 1.2 se cita como su expresión resumida. | La sección 5, punto 15 asigna RF concretos, lo que permite asignar la prioridad Alta de forma objetiva y trazable. |
| HU-15 (tablero, RF-13) | 13 SP. | Se mantuvo en 13 SP. | Está en el límite superior de la escala de Fibonacci usada, pero no lo supera. Dividirla habría llevado el backlog a más de 15 historias y separado indicadores que la Administración consulta juntos. |
| Distribución de prioridades | Alta: 13 historias, 86 SP · Media: 1 historia, 3 SP · Baja: 1 historia, 8 SP. | Alta: 13 historias, 86 SP · Media: 2 historias, 6 SP · Baja: ninguna. | Al sustituir la única historia Baja (duplicados) por una Media (exportación), no quedaron historias Baja. La categoría se conserva en la leyenda para las funciones de segunda fase que se agreguen después. |

## 3. Criterio de revisión

La propuesta inicial se revisó con estos criterios:

- **Valor de negocio:** cada historia debe aportar valor a un actor del sistema (Residente, Vigilancia, Mantenimiento o Administración) y no ser solo una tarea técnica.
- **Alcance de 12 semanas:** las historias Alta deben cubrir completo el alcance mínimo (RF-01 a RF-16 y RF-27), y lo que no cabe se difiere de forma explícita.
- **Trazabilidad con el SRS:** cada historia referencia RF y criterios `RF-XX-AC-Y` existentes, sin inventar, renombrar ni modificar identificadores, y respeta las exclusiones EX-01 a EX-14.
- **Tamaño de historias:** las estimaciones usan solo 1, 2, 3, 5, 8 o 13 SP, y ninguna historia supera 13.
- **Verificabilidad de los criterios de aceptación:** los criterios conservan los umbrales, mensajes, estados, permisos y actores del SRS, de modo que se puedan probar.

## 4. Conclusión

La versión final del Product Backlog no es una aceptación automática de lo que generó el agente de IA, sino el resultado de una revisión humana de su propuesta. El equipo comparó cada historia con `SRS_equipo.md` y cambió la prioridad relativa entre funciones de segunda fase según su valor de negocio. Además, fijó una referencia formal para el alcance mínimo y validó el tamaño y la trazabilidad de cada historia. Con esos ajustes, el backlog cubre completo el alcance mínimo de 12 semanas y documenta de forma explícita lo que se difiere a segunda fase.
