# Revisión de los componentes generados por el agente

**S07-S08-A1 · Parte 2**

Le pedí al agente (Claude) los cuatro componentes en React + Tailwind. Su propuesta quedó en el commit `fe81aa1` («propuesta inicial del agente») y mis ajustes en el commit siguiente, así que el diff entre ambos muestra exactamente qué cambié. Los problemas de accesibilidad los dejé para `accesibilidad.md`.

## Parámetros de cada componente (versión final)

| Componente | Props | Responsivo |
|---|---|---|
| `Button` | `variante` (`primario` \| `secundario`), `cargando`, `disabled`, `type`, `className`, resto de atributos de `<button>` | Ancho completo en móvil (`w-full`), ancho del contenido desde `sm` |
| `Input` | `label`, `id` (opcional), `error`, `required`, resto de atributos de `<input>` | Columna flexible que ocupa el ancho del contenedor |
| `Card` | `titulo`, `subtitulo`, `pie`, `children` | Padding `p-4` en móvil y `sm:p-6`; en la página se acomodan en 1, 2 o 3 columnas (`sm:grid-cols-2 lg:grid-cols-3`) |
| `Navbar` | `marca`, `enlaces` (`{ to, label, roles? }`), `usuario`, `onLogout` | Menú hamburguesa debajo de `md`, fila horizontal desde `md` |

El estado autenticado/no autenticado sale de `AuthContext` (Context API, como decidimos en `decision_stack_frontend.md`): sin `usuario`, la Navbar muestra «Iniciar sesión»; con `usuario`, muestra sus enlaces, su nombre y rol, y «Salir».

## Qué cambié y por qué

### 1. Navbar: enlaces filtrados por rol

- **Propuesta del agente:** mostraba todos los enlaces a cualquier usuario autenticado. La marca «ReportaYa» estaba fija en el código, y el menú móvil se quedaba abierto después de elegir un enlace.
- **Cambio:** cada enlace acepta `roles` opcional y la Navbar solo muestra los que corresponden a `usuario.rol`. Agregué la prop `marca` y el menú se cierra al navegar o al salir.
- **Por qué:** ReportaYa tiene cuatro roles con vistas distintas (RF-01, matriz de visibilidad 2.3 del SRS). Ofrecerle «Usuarios» a un Residente para que después el backend le responda 403 es mala experiencia. El backend sigue siendo quien autoriza (RNF-05); el filtro solo evita mostrar opciones que no puede usar. Lo probé con `admin@reportaya.demo`, que ve «Usuarios», y con `residente@reportaya.demo`, que no lo ve. Los nombres de rol los tomé de lo que devuelve `/auth/login` (`Administracion`, sin acento).

### 2. Input: `id` generado automáticamente y prop `required`

- **Propuesta del agente:** el `<label htmlFor>` dependía de que quien usara el componente pasara un `id`. Si se olvidaba, el label quedaba desligado del campo.
- **Cambio:** si no llega `id`, se genera uno con `useId()` de React. Agregué `required`, que marca el campo como obligatorio y pone un asterisco en la etiqueta.
- **Por qué:** un componente reutilizable no debe depender de que cada uso recuerde un detalle así. `useId` genera ids únicos aunque haya varios formularios en la misma pantalla. Los formularios del proyecto (alta de reporte, unidades, parámetros) tienen campos obligatorios, y el usuario tiene que saber cuáles son antes de enviar.

### 3. Button: acepta `className` y valida la variante

- **Propuesta del agente:** usaba `{...props}` después de `className`, así que si alguien pasaba `className` se sustituía la cadena completa y el botón perdía todos sus estilos. Una variante mal escrita (`"primaria"`) dejaba la clase `undefined`.
- **Cambio:** saqué `className` de `props` y lo concateno al final. Si la variante no existe, se usa la primaria.
- **Por qué:** para reutilizar el botón con un margen o un ancho específico (`className="mt-4"`) sin perder el diseño base. Que caiga en la primaria es un fallo visible y razonable, no un botón sin estilos.

### 4. Sesión en `sessionStorage`

- **Propuesta del agente:** el token vivía solo en memoria (estado de React), así que se perdía al recargar la página.
- **Cambio:** `AuthContext` guarda `{ token, usuario }` en `sessionStorage` y la lee al iniciar; `logout` la borra.
- **Por qué:** perder la sesión con cada recarga no es usable. Elegí `sessionStorage` en lugar de `localStorage` porque se borra al cerrar la pestaña, y eso encaja con la sesión corta de RNF-06 (30 minutos); el token tampoco sobrevive más allá de esa pestaña. Sé que cualquier almacenamiento accesible desde JavaScript queda expuesto si hubiera XSS. La protección real es que el backend valida la expiración y la sesión (`sid`, AR-8). Revisaremos esta decisión en la integración frontend-backend.

## Qué acepté sin cambios

- `Card`: genérica (título, subtítulo, contenido y pie opcionales), sin lógica; cumple lo que pedía la actividad.
- El estado de carga del `Button`: deshabilita el botón mientras `cargando` es verdadero y así evita envíos dobles. Es importante para las altas que más adelante llevarán `Idempotency-Key` (AR-7).
- Las clases responsivas propuestas por el agente; las verifiqué a 375 px y a 1100 px de ancho.
