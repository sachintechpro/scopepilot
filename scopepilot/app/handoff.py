"""Validate a human-reviewed scope before exporting BuildEstimate request JSON."""
from decimal import Decimal, InvalidOperation
from .core import catalog, validated_quantity

DEFAULTS = {
    'labor_rate': 55,
    'waste_percent': 10,
    'overhead_percent': 12,
    'profit_markup_percent': 15,
    'material_tax_percent': 0,
}

def prepare(payload):
    if not isinstance(payload, dict) or payload.get('approved') is not True:
        raise ValueError('Explicit contractor approval is required before export.')
    name = payload.get('project_name', 'Reviewed scope draft')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
        raise ValueError('Provide a project name of 1 to 120 characters.')
    rows = payload.get('items')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError('Select at least one and no more than 100 approved items.')
    allowed = catalog()
    results = []
    for row in rows:
        if not isinstance(row, dict) or row.get('code') not in allowed:
            raise ValueError('One or more selected item codes are not in the catalog.')
        qty = validated_quantity(row.get('quantity'))
        if qty is None:
            raise ValueError(f"Enter a valid positive quantity for {row.get('code')}.")
        results.append({'code': row['code'], 'quantity': qty})
    assumptions = {}
    source = payload.get('assumptions', {})
    if not isinstance(source, dict):
        raise ValueError('Assumptions must be an object.')
    for key, default in DEFAULTS.items():
        raw = source.get(key, default)
        try:
            val = Decimal(str(raw))
        except (ValueError, TypeError, InvalidOperation):
            raise ValueError(f'{key} must be numeric.') from None
        maximum = 100000000 if key == 'labor_rate' else 100
        if not val.is_finite() or val < 0 or val > maximum:
            raise ValueError(f'{key} must be between 0 and {maximum}.')
        assumptions[key] = float(val)
    return {'project_name': name.strip(), **assumptions, 'items': results}
