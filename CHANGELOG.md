## V6.4 - Corrección de listas desplegables
- Corregido el cierre inmediato de listas al hacer clic en la flecha de QComboBox.
- Las listas ahora permanecen abiertas tras un clic normal y permiten seleccionar con otro clic.

# V6.2
- Categoría y Unidad de medida ahora muestran un botón ▼ permanente para abrir sus opciones predefinidas.
- Ambos campos continúan siendo editables para permitir categorías/unidades nuevas.
- Etiquetas y tooltips aclaran que son listas editables y reducen duplicados accidentales.

# CHANGELOG — V4

- Nuevo sistema visual global inspirado en paneles administrativos modernos de alto contraste.
- Sidebar oscura con acento lima, hover y módulo activo claramente visible.
- Botones con estados normal, hover, pressed, focus, disabled y jerarquías primaria/secundaria/peligro.
- Campos con foco claramente marcado y validación visual.
- Tablas con selección de fila notoria y hover.
- Calendarios rediseñados: fecha seleccionada y fecha de hoy visualmente diferenciadas.
- Filtros de Inventario y Dashboard con estado activo persistente.
- Estados de Inventario mediante badges suaves en lugar de pintar indiscriminadamente filas completas.
- Notificaciones de éxito tipo toast no bloqueantes.
- Modal de producto actualizado con sincronización bidireccional Precio ↔ Ganancia.
- Soporte de política `Recargo sobre costo` y `Margen sobre ventas`.
- Cambio de política recalcula porcentajes guardados sin modificar precio ni CPP.
- Validación de coherencia antes de persistir precio/porcentaje.
- Recomendador auditado: demanda, stock disponible, pedidos pendientes, plazo, seguridad, cantidad entera/fraccionaria y vencimientos.
- Opción `¿Cómo se calculó?` dentro de recomendaciones de compra.
- Productos con vencimiento próximo y productos estancados quedan excluidos de compra automática sugerida.
- Dashboard ampliado con Resumen de hoy, Atención requerida, Actividad reciente y productos destacados.
- Gráfica de ventas rediseñada visualmente sin cambiar su fuente de datos.
- Pruebas V4 añadidas para precio/margen, políticas, recomendaciones y estados UI cuando PyQt6 está disponible.

# CHANGELOG — V5

- Corrección integral de layouts para evitar superposiciones en compras, caja, dashboard y formularios.
- Nuevo control reutilizable de cantidad `QuantityInput` con botones visibles `− / +` y campo central editable; admite cantidades enteras y fraccionarias sin ocultar cifras.
- Columnas de acciones y cantidades ajustadas con `ResizeToContents` y scrollbars de tabla cuando hacen falta.
- Scrollbars globales visibles y estilizadas; Decisiones ahora declara explícitamente scroll vertical y horizontal según necesidad.
- Dashboard responsivo: KPIs pasan de 4 a 2 o 1 columna según el ancho; gráfica, resumen y paneles inferiores se reacomodan sin aplastarse.
- Actividad reciente reconstruida como lista de tarjetas compactas con descripción, fecha y monto separados; textos largos usan truncado y tooltip.
- `ProductDialog` convertido en el único formulario reutilizable para Inventario y Compras.
- El formulario de producto ahora es redimensionable, usa `QScrollArea`, footer fijo con Guardar/Cancelar y modo rápido con `Mostrar más opciones`.
- Configuración convertida a página scrollable para pantallas pequeñas.
- Reportes reorganizados con controles en grid y scrollbars de tabla visibles cuando corresponda.
- Ventana principal reduce su tamaño mínimo para mantener operabilidad en equipos de 1024×768 sin depender de coordenadas absolutas.
- Eliminados subcontroles estrechos de `QSpinBox/QDoubleSpinBox` que podían cubrir valores; los campos numéricos generales priorizan escritura directa.
- Se mantiene la paleta, estados activos, foco, hover, calendario y lenguaje visual de V4.
- Se agregaron pruebas V5 de arquitectura de UI, reutilización del formulario de producto, scrollbars y control de cantidad.

## V5.0.1 - Corrección de arranque
- Se añadió la importación faltante de `Qt` en la vista de Reportes.
- `run.bat` y `run_demo.bat` ya no intentan ejecutar `py` después de un error interno de la aplicación; solo usan `py` si `python` no existe.

## V5 corrección visual adicional
- Botones "Eliminar" reemplazados por un icono compacto de papelera con tooltip.
- Columnas de acciones y filas de tablas ajustadas para evitar solapamientos.
- Tabla de Clientes y Fiados con anchos de columnas coherentes y scroll horizontal cuando sea necesario.
- Fondo explícito claro en Dashboard y en el formulario de producto para evitar texto oscuro sobre fondos oscuros del sistema operativo.
- Formulario de producto con controles expansibles y anchos mínimos para que etiquetas, coincidencias, precio y cantidades sean legibles.
- Control de cantidad reforzado para mantener siempre visible el valor entre los botones - y +.

## 6.1 - Categorías y unidades predeterminadas
- El formulario de producto incluye categorías comunes de una tienda de abarrotes desde la primera ejecución.
- Las categorías siguen siendo editables: escribir una nueva la crea al guardar el producto.
- Se ampliaron las unidades de medida predeterminadas (unidad, paquete, bolsa, caja, botella, lata, libra, kg, gramo, litro, ml, galón, etc.).
- Las unidades también siguen siendo editables para admitir unidades especiales.
- Al reiniciar el sistema, las categorías base vuelven a estar disponibles automáticamente.

## V6.3
- Nueva Compra muestra CPP estimado y un precio de venta editable por producto.
- Al cambiar cantidad/costo, el precio sugerido se recalcula conservando la política de ganancia hasta que el usuario lo modifique manualmente.
- El precio elegido queda guardado; en compras pendientes se aplica al recibir la mercancía.
- El porcentaje de ganancia se recalcula contra el CPP definitivo, sin alterar el CPP manualmente.
- Clientes y Fiados se refresca inmediatamente después de una venta fiada o parcial, sin pasar por Dashboard.
- Los listados normales usan una flecha ▼ visible; Categoría y Unidad conservan su botón de lista editable.
