# Reflexión sobre deuda técnica — S09-A1

**Equipo 5 · TC5062 · Parte 5 · Backend de ReportaYa**

Usamos «deuda técnica» en el sentido de Fowler: el costo extra que pagaremos al cambiar el código en el futuro por decisiones (o descuidos) de hoy. **No** contamos como deuda lo que todavía no se construye: las 23 operaciones del contrato sin implementar (transiciones de estado, archivos, métricas) son alcance pendiente del Product Backlog, no deuda.

---

## 1. ¿Cuánta deuda técnica tiene el proyecto y cómo la medimos?

### 1.1 Indicadores medidos (antes de la Parte 4)

| Indicador | Valor | Fuente |
|---|---|---|
| Bugs funcionales o de seguridad conocidos | **2**: H-1 (un Residente ve y modifica reportes ajenos) y CR-1 (`Idempotency-Key` ignorada) | `code_review.md`, `clasificacion_problemas.md` |
| Calificación de pylint | 7.91/10 | `output_linter.txt` |
| Mensajes de análisis estático | 426 (1 % críticos, 10 % importantes, 88 % menores) | `clasificacion_problemas.md` |
| Funciones con complejidad ciclomática > 10 | 5 (la peor, `create_report`, con 26) | flake8 C901 |
| Errores de tipos | 18 | mypy |
| Principios SOLID no cumplidos | ISP y DIP (SRP y OCP parcialmente) | `code_review.md` §5 |
| Desviaciones de la arquitectura acordada | SQLite en lugar de PostgreSQL; sin outbox, worker ni tabla de idempotencia | `arquitectura_equipo.md` (AR-4, AR-7) |
| Cobertura del contrato por las pruebas | 49 de 72 operaciones (759 verificaciones) | `test_contrato.py` |

### 1.2 Estimación en horas (lo que le diríamos al Product Owner)

Estimamos el esfuerzo para corregir cada deuda, **sin** incluir funciones nuevas:

| Deuda | Esfuerzo estimado |
|---|---|
| H-1 · Control de acceso por registro (matriz 2.3) en reportes, con pruebas por rol | 8 h |
| CR-1 · Idempotencia real (tabla, 5 endpoints, pruebas de reintento) | 6 h |
| Migrar de SQLite a PostgreSQL, como decidió la arquitectura | 12 h |
| DIP · `AlmacenArchivos` (RNF-08) | 4 h |
| SRP restante · 4 funciones complejas y consultas fuera de `serial.py` (problema N+1) | 9 h |
| OCP · tablas de despacho por rol y por tipo de historial | 3 h |
| Tipos y excepciones (IM-2, IM-3, IM-4) | 2 h |
| Menores (docstrings, líneas largas, imports; gran parte automática) | 5 h |
| **Total** | **≈ 49 h** |

**Respuesta directa: unas 49 horas de trabajo**, de las cuales **14 h (H-1 y CR-1) son urgentes** porque ya afectan a los usuarios. Para un equipo que dedica entre 8 y 9 h por persona a la semana, es casi un sprint completo de una persona.

### 1.3 Cómo la mediríamos de forma continua

- **Razón de deuda técnica (método SQALE, el que usa SonarQube):** costo de corregir ÷ costo de desarrollar. Con el valor por omisión de SonarQube (30 min por línea), desarrollar 2,176 líneas equivale a unas 1,088 h; 49 h ÷ 1,088 h ≈ **4.5 %**, que SonarQube calificaría con **A** (≤ 5 %).
- **Lo que aprendimos de ese número:** una «A» con un bug de control de acceso abierto muestra que la razón **no pesa la severidad**. Por eso no basta un solo número: medimos tres cosas por sprint, en este orden:
  1. **Bugs críticos abiertos** (meta: 0).
  2. **Horas estimadas de deuda** y si suben o bajan entre sprints.
  3. **Métricas automáticas**: calificación de pylint, funciones con complejidad > 10 y errores de mypy.
- **Ya bajó:** las tres refactorizaciones de la Parte 4 pagaron unas 5 h de deuda (pylint 7.91 → 8.03; complejidad > 10: 5 → 4 funciones; mypy: 18 → 17) sin romper ninguna de las 759 verificaciones.

---

## 2. ¿Qué deuda fue intencional y cuál involuntaria?

### 2.1 Intencional: la decidimos para avanzar más rápido

| Deuda | Evidencia de que fue decisión | Por qué fue razonable entonces | Interés que ya pagamos o pagaremos |
|---|---|---|---|
| **`Idempotency-Key` aceptada pero no aplicada** (CR-1) | `revision_sql.md` §3: «se acepta pero **no se aplica**… hace falta una tabla `idempotencia`». Comentario en `reportes.py`: «aceptado; ver revision_sql.md». | La entrega S05-S06-A1 era de CRUD; la tabla no estaba en el diagrama de clases. | Bloquea el modo sin conexión (RNF-11): con señal intermitente, cada reintento duplica reportes. |
| **23 operaciones y la matriz de visibilidad pospuestas** | `revision_sql.md` §3: «No implementado por pertenecer a seguridad (siguiente actividad)», incluida «la matriz de visibilidad 2.3». | Dividir por actividades del curso: CRUD primero, seguridad y reglas después. | Ver 2.3: una parte de esta deuda se olvidó. |
| **SQLite en lugar de PostgreSQL** | `arquitectura_equipo.md` decide PostgreSQL (AR-4, AR-7); el backend usa SQLite y el README lo declara. No encontramos un documento que explique el cambio; **inferimos** que fue para no depender de un servidor de base de datos durante el desarrollo. | Arranque inmediato: `init_db.py` crea la base en un archivo. | La outbox (AR-4) y el bloqueo por fila dependen de PostgreSQL; hoy no hay worker de correo. La migración cuesta ≈ 12 h, y crece con cada consulta escrita para SQLite. |
| **Parámetros en `camelCase`** (`pageSize`, `ubicacionTipo`) | Coinciden con los nombres del contrato OpenAPI. | El contrato manda en el API. | Bajo: 29 avisos de estilo; se corrige con `Query(alias=...)`. |
| **Pruebas que escriben directo en la base** | `revision_sql.md` §3: «la prueba deja el reporte en `Asignado`/`Cerrado` escribiendo directamente en la BD». | Sin transiciones implementadas, era la única forma de probar notas y persistencia. | Las pruebas no detectarán un error en las transiciones cuando existan. |

### 2.2 Involuntaria: nadie la decidió; apareció al revisar

| Deuda | Cómo la encontramos | Causa probable |
|---|---|---|
| **La regla RF-17 copiada en dos funciones** (H-3, ya pagada en R-1) | Code review | Copiar y pegar una consulta que ya funcionaba al crear el segundo endpoint. |
| **`create_report` con complejidad 26** (H-2, ya pagada en R-2) | flake8 C901 | Crecimiento por acumulación: cada regla del SRS se agregó donde ya estaba el código. |
| **Hash de la contraseña inyectado en cada endpoint** (ISP, ya pagada en R-3) | Evaluación SOLID | `SELECT *` por comodidad al escribir `usuario_actual`. |
| **Regex de UUID copiada 6 veces y más débil que `util.UUID_RE`** (H-7) | Code review | El archivo se escribió sin revisar qué ya existía en `util.py`. |
| **Consultas N+1 en el listado** (SOLID-SRP) | Evaluación SOLID | Reutilizar `report_summary` del detalle en el listado sin medir cuántas consultas hacía. |
| **Excepciones sin `from` y datos faltantes que terminan en 500** (IM-2, H-4) | pylint W0707, code review | No había una convención de manejo de errores internos. |
| **11 imports sin usar** | flake8 F401 | Código que se movió o borró sin limpiar. |

### 2.3 El caso más importante: deuda intencional que se volvió involuntaria

**H-1 empezó como deuda intencional y terminó como olvido.** En S05-S06-A1 el equipo escribió explícitamente que la matriz de visibilidad 2.3 quedaba para la actividad de seguridad. En S05-S06-A2 se implementó la autorización **por rol** (`PERMISOS` en `security.py`), pero no la autorización **por registro**, y nadie volvió a revisar la lista de pendientes. El resultado es el hallazgo más grave de esta auditoría: un Residente lee los horarios en que un departamento ajeno está vacío y puede modificar ese reporte.

**Lección:** la deuda intencional solo es segura si queda **registrada en el Product Backlog** con dueño y fecha. Escrita en una sección de pendientes de un documento de entrega, se pierde.

---

## 3. ¿Cómo integraríamos la calidad y SOLID en el flujo de Scrum?

Elegimos prácticas que un equipo de estudiantes con 8–9 h por semana sí va a sostener: **las que son automáticas o cuestan minutos**.

### 3.1 Product Backlog: la deuda se vuelve visible

Cada deuda se registra como un ítem del backlog con el mismo formato que las historias, para que el Product Owner la priorice frente a funciones nuevas:

| ID | Ítem | Prioridad | SP |
|---|---|---|---|
| DT-01 | Aplicar la matriz de visibilidad 2.3 en reportes (H-1) | **Alta** (seguridad) | 5 |
| DT-02 | Idempotencia real con tabla de claves (CR-1) | **Alta** (bloquea RNF-11) | 5 |
| DT-03 | Migrar a PostgreSQL según la arquitectura | Media | 8 |
| DT-04 | `AlmacenArchivos` (DIP, RNF-08) | Media | 3 |
| DT-05 | Resumen de reportes en una consulta (N+1) | Baja | 3 |

### 3.2 Sprint Planning: capacidad reservada

- **20 % de la capacidad de cada sprint** se reserva para ítems `DT-`. Con una capacidad de 10 SP por sprint, como en el Sprint 1, son 2 SP: poco, pero constante.
- **Regla:** un bug de seguridad (como DT-01) no espera al 20 %; entra al siguiente sprint como prioridad 1.

### 3.3 Durante el sprint: automatizar lo que se olvida

Un flujo de **GitHub Actions** que corre en cada `push` y en cada pull request:

```yaml
# .github/workflows/calidad.yml
name: calidad
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install -r requirements.txt flake8 mypy pylint
      - run: flake8 --select=E9,F,C901 app scripts      # errores, código sin usar y complejidad > 10
      - run: mypy app scripts
      - run: pylint app scripts --fail-under=8.0         # no se acepta bajar de la calificación actual
      - run: |                                           # pruebas de contrato
          cp .env.example .env && sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$(python -c 'import secrets;print(secrets.token_urlsafe(48))')/" .env
          python scripts/init_db.py --reset --demo
          (uvicorn app.main:app --port 8000 &) && sleep 3
          python tests/test_contrato.py
```

La configuración de las herramientas ya está en `backend/setup.cfg`, así que todos usan los mismos criterios.

### 3.4 Definition of Done: tres puntos nuevos

Además de los puntos actuales de la DoD (`S03_A2/definition_of_done.md`), una historia está Done solo si:

1. **El flujo de calidad pasa en verde**: análisis estático sin errores nuevos y 0 fallos en las pruebas de contrato.
2. **No agrega hallazgos críticos** según los criterios de `clasificacion_problemas.md`, y ninguna función nueva pasa de complejidad 10.
3. **Si deja deuda a propósito, la registra** como ítem `DT-` en el Product Backlog antes de cerrarse. (Esta regla habría evitado H-1.)

### 3.5 Revisión de código entre compañeros

Cada pull request lo revisa otro integrante con una lista corta de cinco preguntas, una por principio SOLID más seguridad:

- ¿Esta función hace una sola cosa que se pueda nombrar? (SRP)
- ¿Agregar un caso nuevo obliga a modificar un `if/elif` existente? (OCP)
- ¿El endpoint recibe solo los datos que usa? (ISP)
- ¿El código de negocio depende de un detalle concreto (disco, SQLite) en lugar de una abstracción? (DIP)
- ¿Revisa no solo el **rol** sino **qué registro** puede ver o cambiar ese usuario? (seguridad, H-1)

### 3.6 Sprint Review y Retrospective

- **Review:** junto con las historias terminadas se muestran los tres indicadores de 1.3 (bugs críticos, horas de deuda, métricas automáticas) y su tendencia. El Product Owner ve la deuda igual que ve el avance.
- **Retrospective:** una pregunta fija: «¿qué deuda creamos este sprint y fue a propósito?». La deuda involuntaria que aparezca se registra como `DT-` y se busca su causa (por ejemplo, copiar código sin revisar `util.py`).

### 3.7 Qué esperamos que sí se sostenga

De todo lo anterior, lo que más confianza nos da es lo **automático**: el flujo de CI y la regla de la DoD no dependen de que alguien se acuerde. La reserva del 20 % y la lista de revisión dependen de disciplina, así que las revisaremos en cada Retrospective para ver si se cumplen.
