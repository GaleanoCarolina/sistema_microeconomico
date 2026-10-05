# Sistema de Gestión Microeconómica e Inventarios — V6

Aplicación de escritorio para una tienda minorista en Guatemala. Está construida con **Python 3, PyQt6, SQLite3 y Matplotlib**, funciona localmente y conserva una arquitectura separada por vistas, controladores, servicios, repositorios, modelos y migraciones.

## Instalación en Windows

1. Extrae todo el ZIP en una carpeta nueva.
2. Entra en la carpeta `sistema_microeconomico`.
3. Haz doble clic en `instalar.bat` una sola vez.
4. Para probar con información ficticia, abre `run_demo.bat`.
5. Para utilizar una base normal, abre `run.bat`.

También puedes abrir una terminal dentro de la carpeta y ejecutar:

```bat
python -m pip install -r requirements.txt
python main.py --demo
```

Si Windows usa `py` en lugar de `python`:

```bat
py -m pip install -r requirements.txt
py main.py --demo
```

`tzdata` está incluido en `requirements.txt` para que la zona horaria `America/Guatemala` funcione correctamente en Windows.

## Qué cambia en V4

### Rediseño visual global

V4 conserva la lógica empresarial de V3, pero adopta un sistema visual nuevo inspirado en paneles administrativos modernos: navegación oscura, tarjetas redondeadas, superficies claras, acento verde lima, jerarquía tipográfica más fuerte y retroalimentación visible en cada interacción.

El estilo se centraliza en `views/components/theme.py`. Botones, filtros, campos, tablas, calendarios, spinboxes, checkboxes, diálogos y estados de foco comparten la misma identidad visual.

Se añadieron estados claros para:

- módulo activo en la Sidebar;
- hover y pressed en botones;
- filtros seleccionados;
- fila seleccionada en tablas;
- foco de campos;
- fecha seleccionada en calendarios;
- fecha de hoy diferenciada de la fecha elegida;
- estados de inventario mediante badges suaves;
- mensajes de éxito no bloqueantes tipo toast.

### Precio ↔ porcentaje de ganancia sincronizados

En `Editar producto`, el CPP se muestra pero no se modifica desde el formulario común.

Si la política activa es **Recargo sobre costo**:

`precio = CPP × (1 + porcentaje/100)`

`porcentaje = ((precio - CPP) / CPP) × 100`

Si la política activa es **Margen sobre ventas**:

`precio = CPP / (1 - margen/100)`

`margen = ((precio - CPP) / precio) × 100`

Al cambiar el precio, el porcentaje se actualiza inmediatamente. Al cambiar el porcentaje, el precio se actualiza inmediatamente. Se bloquean señales durante la sincronización para evitar ciclos infinitos.

La política se configura en `Configuración > Precios y existencias`. Si se cambia la política global, V4 recalcula el porcentaje almacenado de cada producto usando su CPP y precio actuales, **sin modificar el CPP ni el precio**.

### Recomendaciones auditadas

Las cantidades sugeridas son deterministas. Consideran:

- demanda diaria observada;
- existencias disponibles;
- pedidos pendientes;
- plazo del proveedor;
- stock de seguridad;
- un colchón operativo de 3 días;
- tipo de cantidad entero o fraccionario;
- producto estancado;
- lotes próximos a vencer.

Fórmula base utilizada:

`stock objetivo = demanda diaria × (plazo proveedor + 3 días) + stock de seguridad`

`cantidad sugerida = máximo(0, stock objetivo - existencias disponibles - pedidos pendientes)`

Los productos enteros se redondean hacia arriba. Los fraccionarios se redondean a pasos de 0.25.

Una recomendación de compra ahora incluye `¿Cómo se calculó?`, donde se muestran las variables usadas. Los productos con riesgo de vencimiento próximo no entran simultáneamente como compra recomendada. Los productos estancados tampoco se incluyen como reabastecimiento.

### Dashboard más útil

El Dashboard conserva sus KPIs y ahora incluye:

- Ventas.
- Ganancia bruta.
- Cobrado.
- Pendiente por cobrar.
- Dinero en inventario.
- Compras del período.
- Productos por agotarse.
- Productos próximos a vencer.
- Resumen de hoy.
- Producto más vendido.
- Producto con mayor ganancia.
- Menor rotación observada cuando hay historial suficiente.
- Atención requerida.
- Actividad reciente.
- Acciones rápidas.

La gráfica mantiene la misma lógica de datos, pero fue rediseñada para integrarse con el nuevo lenguaje visual.

## Inventario y lotes

El Maestro de Inventario muestra todos los productos activos incluso con existencia cero. Las existencias físicas se derivan de los lotes activos y se reconcilian con `products.stock_qty`.

Cada recepción crea un lote independiente con:

- cantidad inicial;
- cantidad disponible;
- costo de entrada;
- fecha de recepción;
- vencimiento opcional.

FEFO decide de qué lote físico sale primero una venta. El CPP sigue siendo el costo contable para costo de mercancía vendida y ganancia bruta.

## Compras

Una compra puede ser:

- **Recibida ahora**: entra al inventario inmediatamente.
- **Pendiente de recibir**: conserva el valor y el detalle, pero no incrementa existencias hasta confirmar la recepción.

Por defecto, la fecha de recepción es igual a la fecha de compra.

Cada compra conserva subtotal, descuento, costos adicionales, total, proveedor y costos históricos por línea.

## Fiados y abonos

Las ventas fiadas forman parte de ventas, pero no del dinero cobrado mientras permanezcan pendientes. Un abono aumenta lo cobrado y reduce cuentas por cobrar sin crear una venta nueva.

## Base de datos y migraciones

La base normal se crea en `database/app.db`. Las migraciones se ejecutan automáticamente al iniciar. V4 no necesita una nueva migración estructural para precio/margen ni para el rediseño; la nueva política de ganancia se guarda en `settings`.

Antes de sustituir una instalación con datos reales, crea un respaldo desde Configuración o copia `database/app.db`.

## Respaldos

Desde Configuración se pueden crear y restaurar copias de seguridad. Los respaldos se guardan por defecto en `database/backups/`.

## Datos de demostración

`python main.py --demo` carga datos ficticios solamente si la base está vacía. La lógica empresarial no depende de nombres, IDs o productos demo.

## Pruebas

Ejecuta:

```bat
python -m pytest -q
```

V4 incorpora pruebas adicionales para:

- precio → porcentaje;
- porcentaje → precio;
- recargo sobre costo;
- margen sobre ventas;
- persistencia coherente en repositorio;
- cambio de política sin alterar precio/CPP;
- recomendaciones deterministas;
- pedidos pendientes;
- stock alto;
- productos fraccionarios;
- bloqueo de compra cuando hay vencimiento próximo;
- selección de calendario, fila de Inventario y sincronización UI cuando PyQt6 está disponible.

## Arquitectura

- `models/`: objetos del dominio.
- `views/`: interfaz PyQt6.
- `controllers/`: coordinación de interfaz y casos de uso.
- `services/`: ventas, compras, inventario, CPP, FEFO, fiados, analítica y recomendaciones.
- `repositories/`: persistencia y consultas SQL.
- `database/`: conexión, migraciones, demo y respaldos.
- `utils/`: dinero con Decimal, cantidades, fechas y normalización.
- `tests/`: pruebas automatizadas.

## Cambios principales de V5

V5 conserva la lógica empresarial de V4 y se concentra en responsividad y usabilidad visual. Los campos de cantidad de Caja y Compras usan un control claro `[-] valor [+]`; las tablas muestran scrollbars cuando el contenido no cabe; Decisiones tiene barra de desplazamiento visible; Configuración es scrollable; y el Dashboard reorganiza sus tarjetas según el ancho de la ventana.

La creación de productos se realiza desde una sola clase reutilizable tanto en Inventario como en Compras. En Compras abre en modo rápido y el botón **Mostrar más opciones** permite acceder a la configuración completa. Los formularios largos son redimensionables, contienen scroll y mantienen visibles los botones **Cancelar** y **Guardar producto**.

Resolución recomendada: 1366×768 o superior. La interfaz también está preparada para seguir siendo operable en 1024×768 mediante reflujo de tarjetas y barras de desplazamiento cuando el contenido excede el espacio.

## V6 — Reinicio total, persistencia segura y distribución como EXE

### ¿Dónde se guardan los datos?

A partir de V6, la base de datos del negocio **no se guarda dentro de la carpeta del programa**. En Windows se guarda en:

`%LOCALAPPDATA%\Sistema_Gestion_Microeconomica\app.db`

Esto significa que ventas, compras, productos, inventario, clientes, fiados, abonos y configuración **permanecen guardados al cerrar y volver a abrir el programa**. Cada computadora/usuario de Windows mantiene su propia base local. El programa no necesita Internet.

Los respaldos creados desde Configuración se guardan por defecto en:

`%LOCALAPPDATA%\Sistema_Gestion_Microeconomica\backups`

### Reiniciar todos los datos

En `Configuración > Reiniciar sistema` existe el botón **Borrar todos los datos y reiniciar**. Requiere dos confirmaciones, incluida escribir `REINICIAR`. Borra la base activa y crea una nueva vacía con la configuración predeterminada. Los archivos de respaldo ya existentes no se borran.

### Crear el EXE para otra persona

La forma más fácil es hacer doble clic en `crear_exe.bat`. El script instala PyInstaller solo si hace falta y genera:

`dist\Sistema Gestion Microeconomica\`

Para compartir el programa, comprime **toda esa carpeta** en ZIP y envíala. La otra persona extrae el ZIP y abre `Sistema Gestion Microeconomica.exe`. No necesita Python instalado.

Si prefieres hacerlo manualmente desde CMD en la carpeta donde está `main.py`:

```bat
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name "Sistema Gestion Microeconomica" --add-data "assets;assets" --add-data "database\migrations;database\migrations" main.py
```

No compartas únicamente el `.exe` de una compilación `onedir`; comparte toda la carpeta generada dentro de `dist`.

### Categorías y unidades predeterminadas
Al crear o editar un producto, el sistema ofrece categorías comunes de una tienda de abarrotes y unidades de medida frecuentes. Ambos campos siguen siendo editables: si necesitas una categoría o unidad diferente, simplemente escríbela. Las categorías nuevas quedan guardadas para usos posteriores.

### Cambio de costo y precio al comprar (V6.3)
En **Nueva compra**, cada línea muestra el costo unitario de entrada, el CPP estimado después de recibirla y el precio de venta que quedará vigente. El sistema propone un precio que conserva el porcentaje de ganancia configurado; el usuario puede escribir otro. Al registrar una compra recibida, el CPP se calcula con la fórmula ponderada y el precio elegido se guarda con un porcentaje coherente. Si la compra queda pendiente, ese precio se conserva en el detalle y se aplica cuando la mercancía se recibe.
