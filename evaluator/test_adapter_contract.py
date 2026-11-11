"""Satisfiability checks for the unchanged historical PALO checker, not model quality."""
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evidence/development-2026-11-10'))
from palo_workbench.models import Claim
from palo_workbench.pipeline import validate_claims


class AdapterContractTests(unittest.TestCase):
    def candidates(self):
        text = 'A Buyer approves an Order.'
        source = {'unit_id': 's1', 'quote': text}
        values = [('entity', 'Buyer', '', ''), ('entity', 'Order', '', ''), ('relationship', 'approves', 'Buyer', 'Order')]
        claims = [Claim(kind=kind, name=name, description=text, entity=entity, target=target, sources=[source]).model_dump() for kind, name, entity, target in values]
        return claims, [{'id': 's1', 'text': text}]

    def test_relationship_is_satisfiable_with_three_candidates(self):
        claims, units = self.candidates()
        result = validate_claims(claims, units, SimpleNamespace(classes=[]))
        self.assertLessEqual(len(result), 16)
        self.assertTrue(all(c['valid'] for c in result), result)

    def test_missing_target_is_a_contract_failure(self):
        claims, units = self.candidates()
        result = validate_claims([claims[0], claims[2]], units, SimpleNamespace(classes=[]))
        self.assertIn('Target entity is missing from the extracted domain model', result[-1]['issues'])

    def test_cooccurrence_does_not_validate_semantic_relation(self):
        claims, units = self.candidates()
        claims[-1]['description'] = 'An Order approves a Buyer.'
        result = validate_claims(claims, units, SimpleNamespace(classes=[]))
        self.assertTrue(result[-1]['valid'])
        # Precisely the limitation: passing this checker is not semantic validity.


if __name__ == '__main__':
    unittest.main()
