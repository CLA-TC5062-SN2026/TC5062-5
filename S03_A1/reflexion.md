# Reflexión — IA, Product Owner y calidad del SRS

| Campo | Valor |
|---|---|
| Actividad | S03-A1 · Product Backlog de SCRUM |
| Contexto | `SRS_equipo.md`, `backlog_completo.md`, `ajustes_backlog.md`, `priorizacion_comparada.md` |
| Fecha | 4 de octubre de 2026 |

## 1. Ventajas y riesgos de usar IA para construir un Product Backlog

La ventaja más evidente fue la velocidad en el trabajo de trazabilidad. `SRS_equipo.md` tiene 27 requerimientos funcionales y 161 criterios de aceptación. El agente leyó el documento completo, agrupó los RF en cinco épicas y propuso una primera versión de 15 historias con sus criterios ya referenciados a identificadores `RF-XX-AC-Y`. Después comprobó que los 129 identificadores distintos citados en el backlog existen en el SRS, una verificación lenta y propensa a errores si se hace a mano. La IA aceleró cuatro tareas: el análisis, la trazabilidad, la redacción y la comparación entre versiones.

El riesgo principal es que la IA toma decisiones con el contexto que tiene, y ese contexto es incompleto. En la propuesta inicial, HU-05 correspondía a la detección y unión de duplicados (RF-17), con prioridad Baja y 8 SP. Era una decisión defendible desde el texto del SRS, porque la sección 1.2 menciona que «dos personas reportan lo mismo». Al revisarla, el equipo la sustituyó por la exportación del tablero (RF-23, Media, 3 SP), porque esa función permite presentar métricas al comité y apoya el supuesto S-07, del que depende la aprobación del gasto. El agente había mencionado esa alternativa como posible, pero no la eligió por sí mismo, y no tenía cómo saber cuál de las dos importaba más al condominio. Un segundo riesgo es que una propuesta bien redactada y con muchas referencias parezca más correcta de lo que es. Por eso el equipo documentó en `ajustes_backlog.md` qué cambió y por qué, en lugar de aceptar la primera versión.

## 2. ¿Puede un agente de IA reemplazar al Product Owner?

El trabajo realizado sugiere que no. El ejercicio de `priorizacion_comparada.md` lo muestra con claridad. El equipo asignó la prioridad con una regla explícita del SRS: Alta si el RF está en el alcance mínimo. El resultado fue de 13 historias Alta empatadas. Cuando se pidió ordenar el backlog desde la perspectiva de un Product Owner, el orden cambió: HU-04 (captura de terceros) subió al cuarto lugar, HU-13 (parámetros) bajó a la posición 14 a pesar de ser Alta, y HU-08, que es Media, quedó por encima de ella. Las dos priorizaciones las produjo el mismo agente con criterios distintos. Esto indica que el orden depende de los criterios que se le den, y elegir esos criterios es justamente la responsabilidad del Product Owner.

Además, varias decisiones dependen de información que el SRS no contiene. Por ejemplo, adelantar HU-05 solo tendría sentido si la asamblea o una sesión del comité cayera dentro de las 12 semanas, y esa fecha no aparece en ningún documento. Tampoco se conoce la velocidad del equipo ni cuántos avisos siguen llegando por WhatsApp. La IA puede argumentar bien una priorización, pero no conoce por sí sola las prioridades reales del cliente ni responde por el resultado. El Product Owner sigue siendo quien maximiza el valor del producto y quien asume las consecuencias de cada decisión. La IA funciona mejor como apoyo que prepara opciones y argumentos para que esa persona decida.

## 3. Cómo afecta la calidad del SRS a la calidad del backlog

La relación fue directa. Donde el SRS era claro y verificable, las historias salieron claras, estimables y comprobables. Los criterios en formato Dado que – cuando – entonces, con datos de prueba comunes (unidad `B-502`, folio `RY-000124`), mensajes de error exactos y un reloj controlable (RNF-10), se tradujeron casi directamente en criterios de aceptación. Así fue posible estimar con argumentos: HU-15 recibió 13 SP porque RF-13 detalla seis indicadores con reglas precisas de cumplimiento, y HU-13 recibió 3 SP porque RF-27 es una tabla fija de parámetros.

Donde el SRS era ambiguo, la ambigüedad pasó al backlog. Había dos formas de expresar el alcance mínimo: la sección 1.2 lista cinco funciones y la sección 5, punto 15 lista RF-01 a RF-16 y RF-27. Elegir una u otra cambiaba la prioridad de cuatro historias, y el equipo tuvo que decidir de forma explícita que la referencia formal sería la segunda. El SRS también cita secciones 6 y 7 que no existen en el archivo, por lo que la matriz de equivalencias con los SRS individuales no está disponible. Además, había dependencias ocultas: RF-13, del alcance mínimo, calcula el tiempo detenido que define RF-18, de segunda fase. Esa dependencia obligó a discutir la prioridad de HU-08 y a anotar criterios que solo se pueden verificar cuando exista otra función.
La IA fue útil para detectar estas inconsistencias porque revisó el documento completo y cruzó referencias que una lectura rápida pasaría por alto. Sin embargo, encontrar una ambigüedad no la resuelve: en cada caso la decisión final quedó en el equipo.

## Conclusión

La experiencia muestra que la IA es una herramienta eficaz para acelerar el análisis, la trazabilidad, la redacción y la comparación de un Product Backlog, y también para encontrar inconsistencias en el SRS. Sin embargo, puede proponer decisiones razonables con un contexto incompleto y no conoce las prioridades reales del cliente. La calidad del backlog depende primero de la calidad del SRS: un requerimiento claro, consistente y verificable produce historias claras, estimables y comprobables, y uno ambiguo produce historias ambiguas, dependencias ocultas y prioridades discutibles. Entre ambos, el Product Owner y el equipo siguen siendo los responsables de decidir qué se construye y en qué orden para maximizar el valor.
