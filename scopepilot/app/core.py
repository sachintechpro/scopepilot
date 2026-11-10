"""Structured scope review. Rule-based demo never guesses quantities.
Optional LLM proposals are independently validated against the price catalog.
"""
from __future__ import annotations
import csv
import re
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / 'data' / 'catalog.csv'
PATTERNS = {
    'CABINET': r'\b(cabinet(?:s|ry)?|kitchen units?)\b',
    'FLOOR': r'\b(lvp|vinyl flooring|vinyl plank|flooring|floors?)\b',
    'PAINT': r'\b(paint(?:ing)?|repaint)\b',
    'DRYWALL': r'\b(drywall|sheetrock|wallboard)\b',
    'BASEBOARD': r'\b(baseboards?|skirting|trim)\b',
    'ROOF': r'\b(roof(?:ing)?|shingles?)\b',
    'WINDOW': r'\b(windows?|glazing)\b',
}
UNIT_PATTERNS = {
    'sqft': r'(?:sq\.?\s*ft\.?|square\s+feet|square\s+foot|sqft|sf)\b',
    'linear_ft': r'(?:linear\s+(?:feet|foot|ft)|lin\.?\s*ft|lf)\b',
    'each': r'(?:windows?|units?|pieces?|pcs|ea)\b',
}


def catalog():
    with CATALOG_PATH.open(newline='', encoding='utf-8') as handle:
        return {row['code']: row for row in csv.DictReader(handle)}


def validated_quantity(raw):
    if raw is None or raw == '':
        return None
    try:
        from decimal import Decimal
        value = Decimal(str(raw))
    except Exception:
        return None
    if not value.is_finite() or value <= 0 or value > 1000000:
        return None
    return format(value, 'f')


def unit_mentions(text, unit):
    """Return quantities explicitly adjacent to a measurement unit."""
    pat = UNIT_PATTERNS[unit]
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r'\b\d+(?:\.\d+)?\s*' + pat, text, re.I)]


def near_quantity(text, hit, unit):
    """Only associate a quantity close to a named task; avoid global guesses."""
    matches = unit_mentions(text, unit)
    close = []
    for start, end, snippet in matches:
        distance = min(abs(hit.start() - end), abs(start - hit.end()))
        # Do not cross sentence boundaries; cap distance to reduce bad pairings.
        between = text[min(start, hit.start()):max(end, hit.end())]
        if distance <= 55 and not re.search(r'[.;\n]', between):
            close.append((distance, snippet))
    if not close:
        return None
    close.sort(key=lambda x: x[0])
    # Avoid choosing between nearly equidistant measurements.
    if len(close) > 1 and close[1][0] - close[0][0] < 8:
        return None
    num = re.match(r'\d+(?:\.\d+)?', close[0][1])
    return validated_quantity(num.group(0)) if num else None


def location_followup(text):
    """Recognize ZIPs and explicit site-location phrasing, without geocoding.

    A named city/neighborhood is not a street address: ask for exact site address.
    Ignore vague words like 'in the kitchen' as evidence of a job location.
    """
    # A street address takes priority over any ZIP code or city mention.
    if re.search(r'\b\d{1,6}\s+[A-Za-z0-9 .-]+\s+'
                 r'(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|court|ct)\b',text,re.I):
        return None
    if re.search(r'\b\d{5}(?:-\d{4})?\b', text):
        return 'Please confirm the complete job-site street address (ZIP provided).'
    # Narrow location phrases, not generic 'in <noun>'.
    site = re.search(
        r'\b(?:house|home|property|job\s*site|site|project|building)\s+(?:is\s+)?'
        r'(?:located\s+)?(?:in|at|near)\s+([A-Za-z][A-Za-z .-]{2,55})', text, re.I)
    if site:
        place = re.split(r'[,.;!?\n]|\s+(?:and|but|could|please|with|where|which)\b',
                         site.group(1), maxsplit=1, flags=re.I)[0].strip()
        if place and not re.fullmatch(r'(?:the|our|my)\s+(?:kitchen|bathroom|living room|bedroom|house|home)', place, re.I):
            return f'What is the full job-site street address? Location mentioned: {place}.'
    # Direct explicit postal address or city/location labels.
    if re.search(r'\b\d{1,6}\s+[A-Za-z0-9 .-]+\s+'
                 r'(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|court|ct)\b',text,re.I):
        return None
    return 'What is the job-site location (city or ZIP code) and street address?'


def review(text):
    if not isinstance(text, str) or not 10 <= len(text.strip()) <= 6000:
        raise ValueError('Enter a project request between 10 and 6,000 characters.')
    entries = catalog()
    items = []
    missing = []
    evidence = []
    for code, pattern in PATTERNS.items():
        hit = re.search(pattern, text, re.I)
        if not hit:
            continue
        entry = entries[code]
        qty = near_quantity(text, hit, entry['unit'])
        items.append({'code':code, 'description':entry['description'], 'unit':entry['unit'],
                      'quantity':qty, 'source':'rule-based match', 'evidence':hit.group(0)})
        evidence.append(f"{entry['description']}: matched ‘{hit.group(0)}’")
        if qty is None:
            missing.append(f"What is the quantity of {entry['description'].lower()} ({entry['unit'].replace('_',' ')})?")
    if not items:
        missing.append('Which work items are needed? Give quantities and units for each.')
    general_questions = [
        (r'\b(permit|inspection)\b', 'Are permits and inspection fees included in the scope?'),
        (r'\b(urgent|asap|rush)\b', 'What is the required start date and deadline?'),
    ]
    for pattern, question in general_questions:
        if re.search(pattern, text, re.I):
            missing.append(question)
    location_question = location_followup(text)
    if location_question:
        missing.append(location_question)
    if not re.search(r'\b(by|before|start|deadline|schedule|week|month|date)\b', text, re.I):
        missing.append('What is the target schedule?')
    return {'mode':'Rules demo — no AI model', 'items':items, 'questions':missing,
            'evidence':evidence, 'status':'Needs review',
            'warnings':['Matched terms are suggestions, not confirmed scope. Confirm quantities and units before estimating.',
                        'No pricing or schedule commitments are generated by this assistant.']}


def normalize_llm(parsed, original):
    """Constrain model suggestions to known catalog codes and explicit evidence."""
    if not isinstance(parsed, dict) or not isinstance(parsed.get('items'), list):
        raise ValueError('AI response was not in the expected structured format.')
    entries = catalog()
    cleaned = []
    for item in parsed['items'][:20]:
        if not isinstance(item, dict):
            continue
        code = item.get('code')
        if code not in entries:
            continue
        # Treat all AI quantities as proposals, not source-verified facts.
        evidence = str(item.get('evidence',''))[:120]
        if not evidence or evidence.lower() not in original.lower():
            continue
        row = entries[code]
        cleaned.append({'code':code,'description':row['description'],'unit':row['unit'],
                        'quantity':validated_quantity(item.get('quantity')),
                        'source':'AI proposal — verify', 'evidence':evidence})
    unique = list({x['code']:x for x in cleaned}.values())
    questions = [str(q)[:220] for q in parsed.get('questions',[]) if isinstance(q,str)][:12]
    for item in unique:
        if item['quantity'] is None:
            questions.append(f"Confirm quantity for {item['description']} ({item['unit']}).")
    return {'mode':'AI-assisted proposal — human review required','items':unique,
            'questions':questions,'evidence':[f"{x['code']}: ‘{x['evidence']}’" for x in unique],
            'status':'Needs review','warnings':['AI may misunderstand quantities, scope, or context. Independently verify all proposed items and measurements.',
            'Catalog unit prices are illustrative and are not live supplier quotes.']}
