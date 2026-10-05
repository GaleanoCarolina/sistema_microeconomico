# Validación V6.3

- Compilación estática: `python -m compileall -q .` — correcta.
- Pruebas automatizadas: **54 aprobadas, 2 omitidas** (las omitidas requieren PyQt6/entorno gráfico disponible).
- Se verificó específicamente:
  - compra recibida con nuevo costo recalcula CPP y permite fijar un nuevo precio de venta;
  - el porcentaje de ganancia queda coherente con el CPP definitivo y el precio elegido;
  - compra pendiente conserva el precio elegido y lo aplica al recibir;
  - una venta fiada/parcial dispara refresco de Clientes y Fiados inmediatamente;
  - los QComboBox visibles usan indicador de lista ▼ o, en Categoría/Unidad, su botón externo de lista editable;
  - migración 004 agrega el precio deseado por detalle de compra sin borrar información existente.
