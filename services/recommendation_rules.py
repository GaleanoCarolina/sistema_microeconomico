"""Reglas cuantitativas separadas para facilitar auditoría y pruebas."""
def is_low_stock(stock, reorder_point): return stock <= reorder_point
def is_stagnant(days_since_sale, threshold, stock): return stock > 0 and days_since_sale >= threshold
def confidence(units_sold): return 'Alta' if units_sold >= 20 else ('Media' if units_sold >= 5 else 'Baja')
