"""Source structure hints, never business approval or formula execution."""
import re
from collections import defaultdict
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.formula.translate import Translator


def annotate_worksheet(units):
    """Keep uncertain labels private until a reviewer confirms their structural role."""
    rows = defaultdict(list)
    for unit in units:
        rows[unit['cell_row']].append(unit)
    headers = {}
    for row_number, row in sorted(rows.items()):
        labels = [u for u in row if u.get('cell_type') == 's' and len(u['text']) < 160]
        band = len(labels) >= 3 and sum(bool(u.get('bold')) for u in labels) >= len(labels) * .7
        for unit in row:
            candidate = unit in labels and (band or (unit.get('bold') and unit['text'].endswith(':')))
            unit['source_role'] = 'structure_candidate' if candidate else 'formula' if unit.get('cell_type') == 'f' else 'unclassified_value'
            if candidate:
                unit['role_reason'] = 'Styled header band' if band else 'Styled form label'
                if band:
                    headers[unit['cell_column']] = {'unit_id': unit['id'], 'text': unit['text']}
            elif unit.get('cell_column') in headers:
                unit['column_header'] = headers[unit['cell_column']]
    return units


def formula_metadata(units):
    """Resolve literal references only. Never fetch links, evaluate, or expand huge ranges."""
    cells = {u['location']: u for u in units if u.get('source_kind') == 'cell'}
    for unit in cells.values():
        if unit.get('cell_type') != 'f':
            continue
        sheet, address = unit['location'].rsplit('!', 1)
        dependencies = []
        try:
            for token in Tokenizer(unit['text']).items:
                if token.type != 'OPERAND' or token.subtype != 'RANGE':
                    continue
                value = token.value
                target_sheet, target = value.rsplit('!', 1) if '!' in value else (sheet, value)
                target_sheet = target_sheet.strip("'").replace("''", "'")
                target = target.replace('$', '')
                if '[' in value or not re.fullmatch(r'[A-Z]+[1-9]\d*', target):
                    dependencies.append({'reference': value, 'state': 'range-or-external-not-evaluated'})
                    continue
                referenced = cells.get(target_sheet + '!' + target)
                dependencies.append({'reference': value, 'state': 'present' if referenced else 'blank-or-absent',
                    'unit_id': referenced['id'] if referenced else None,
                    'header': referenced.get('column_header') if referenced else None})
            unit['formula_dependencies'] = dependencies
            # Positive translation avoids negative row/column indices; retain absolute refs.
            unit['formula_pattern'] = Translator(unit['text'], origin=address).translate_formula('ZZ100001')
        except Exception:
            unit['formula_dependencies'] = dependencies
            unit['formula_pattern'] = unit['text']
            unit['formula_parse_warning'] = 'Formula structure could not be normalised; retained verbatim.'


def inference_units(units):
    """One representative per relative formula pattern; all original anchors remain stored."""
    seen = set()
    result = []
    for unit in units:
        if unit.get('cell_type') == 'f' and unit.get('formula_pattern'):
            key = (unit.get('document'), unit['location'].rsplit('!', 1)[0], unit.get('cell_column'), unit['formula_pattern'],
                   tuple(d['state'] for d in unit.get('formula_dependencies', [])))
            if key in seen:
                continue
            seen.add(key)
        # Normalised coordinates are internal deduplication keys, not source evidence.
        # Sending them to the model caused it to describe synthetic ZZ100001 cells.
        result.append({k:v for k,v in unit.items() if k!='formula_pattern'})
    return result


def visual_inventory(page):
    """Flag raster and vector material even when the page also has extractable text."""
    contents = page.get_contents()
    operations = contents.operations if contents is not None else []
    drawn = sum(op in (b're', b'l', b'c', b'v', b'y') for _, op in operations)
    objects = sum(op in (b'Do', b'INLINE IMAGE') for _, op in operations)
    return {'drawing_operations': drawn, 'embedded_objects': objects,
            'review_required': bool(objects or drawn >= 5),
            'limitation': 'Text extraction does not establish diagram branches, table alignment or actor assignments.'}
