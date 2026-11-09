# Evaluación básica de accesibilidad (WCAG 2.1)

**S07-S08-A1 · Parte 3**

## Cómo se evaluó

1. Le pedí al agente que revisara `Button`, `Input`, `Card` y `Navbar` contra tres puntos de WCAG 2.1: contraste mínimo, nombre accesible en elementos sin texto visible y manejo del foco.
2. Medí el contraste de cada par de colores de Tailwind con la fórmula de luminancia relativa de WCAG (la misma que usa WebAIM Contrast Checker).
3. Corrí **axe-core** (reglas `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`) sobre la página de muestra a 375 px de ancho, con un error de inicio de sesión visible, antes y después de las correcciones:
   - **Antes:** 2 tipos de violación, `button-name` (1 nodo) y `color-contrast` (3 nodos).
   - **Después:** 0 violaciones.
4. Recorrí la página con `Tab` para revisar el foco a mano. axe no detecta todo lo de foco.

Meta del proyecto: **RNF-09**, contraste de al menos 4.5:1 (WCAG 2.1 AA) y texto base de 16 px.

## Problemas encontrados y correcciones

| # | Problema | Criterio WCAG 2.1 | Severidad | Corrección |
|---|---|---|---|---|
| 1 | Subtítulo de `Card` en `slate-400` sobre blanco: **2.63:1** | 1.4.3 Contraste mínimo (AA) | Alta | `slate-600`: **7.58:1** |
| 2 | Mensaje de error del `Input` en `red-500` sobre blanco: **3.81:1** | 1.4.3 Contraste mínimo (AA) | Alta | `red-700`: **6.42:1** (también el asterisco y el borde de error) |
| 3 | Nombre de usuario en la `Navbar` en `blue-200` sobre `blue-600`: **3.69:1** | 1.4.3 Contraste mínimo (AA) | Alta | Fondo `blue-700` y texto `blue-50`: **6.28:1**; los enlaces blancos quedan en 6.83:1 |
| 4 | El botón de menú móvil solo tiene un ícono SVG: un lector de pantalla lo anuncia como «botón» sin nombre, y no informa si el menú está abierto | 4.1.2 Nombre, función, valor (A) | Alta | `aria-label` («Abrir menú» / «Cerrar menú»), `aria-expanded`, `aria-controls="menu-principal"` y `aria-hidden` en el SVG |
| 5 | `Input` con `outline-none`: al recibir foco solo cambiaba el color del borde, de `slate-300` a `blue-500`, un cambio difícil de notar | 2.4.7 Foco visible (AA) | Alta | Contorno `focus-visible:outline-2` en `blue-700` en el `Input`, el `Button` y los enlaces y botones de la `Navbar` (blanco sobre el fondo azul) |
| 6 | El error del `Input` solo se veía: el campo no quedaba marcado como inválido ni ligado a su mensaje | 3.3.1 Identificación de errores (A), 1.3.1 Información y relaciones (A) | Media | `aria-invalid` y `aria-describedby` apuntando al `id` del mensaje |
| 7 | Borde del `Input` en `slate-300`: **1.49:1**, y el usuario no distingue dónde está el campo | 1.4.11 Contraste de componentes no textuales (AA, mínimo 3:1) | Media | Borde `slate-500`: **4.76:1** |
| 8 | El spinner del `Button` en estado de carga no comunica nada a un lector de pantalla | 4.1.2 Nombre, función, valor (A) | Baja | `aria-busy` en el botón, spinner con `aria-hidden` y texto `sr-only` «(cargando)» |

Las dos correcciones más críticas, las que bloquean a un usuario y no solo lo incomodan, son:

1. **Contraste (problemas 1 a 3):** RNF-09 lo exige explícitamente, y el texto que fallaba incluye los mensajes de error de los formularios. Mantenimiento los va a leer en el celular, en campo y a veces a pleno sol.
2. **Botón de menú sin nombre (problema 4):** en móvil es la única forma de llegar a la navegación. Sin nombre accesible, un usuario de lector de pantalla no sabe que existe.

## Lo que se revisó y ya cumplía

- El texto del botón primario (blanco sobre `blue-600`) tiene **5.25:1**.
- Todos los controles son elementos nativos (`<button>`, `<a>`, `<input>`), así que son alcanzables con teclado sin `tabindex`.
- Todos los `Input` tienen `<label for>` ligado al campo; quedó garantizado con `useId` en la revisión de componentes.
- `<html lang="es">` y texto base de 16 px (RNF-09).
- El botón deshabilitado (`opacity-60`) no se corrigió: WCAG 1.4.3 exceptúa los componentes inactivos.

## Pendiente

- Probar con VoiceOver en iPhone, que es el dispositivo que usará el personal en campo. axe solo detecta parte de los problemas.
- Volver a pasar axe cuando existan las pantallas reales de reportes.
