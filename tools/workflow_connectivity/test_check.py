import unittest
from check import assess, dependency_graph, transition_graph

class ConnectivityTests(unittest.TestCase):
    def test_join_and_disconnected_island(self):
        self.assertEqual(assess({'a','b','c'}, [('a','c'),('b','c')])['status'], 'connected')
        self.assertEqual(assess({'a','b','c'}, [('a','b')])['status'], 'disconnected')
    def test_single_step_and_unknown(self):
        self.assertEqual(dependency_graph({'process':[{'id':'a','requires':[]}]})['status'], 'connected')
        self.assertEqual(dependency_graph({'process':[{'id':'a','requires':['missing']}]})['status'], 'unassessed')
        self.assertEqual(dependency_graph({'process':[]})['status'], 'unassessed')
        self.assertEqual(dependency_graph([])['status'], 'unassessed')
    def test_transition_components(self):
        d={'process_transitions':[{'from_state':'a','to_state':'b'},{'from_state':'c','to_state':'d'}]}
        self.assertEqual(transition_graph(d)['status'], 'disconnected')
        self.assertEqual(transition_graph({'process_transitions':[]})['status'], 'unassessed')
    def test_duplicate_step_ids_are_unassessed(self):
        self.assertEqual(dependency_graph({'process':[{'id':'a','requires':[]},{'id':'a','requires':[]}]})['status'], 'unassessed')

class RepresentationInvarianceTests(unittest.TestCase):
    def test_dependency_order_and_identifier_bijection(self):
        original = {'process': [
            {'id': 'start', 'requires': []},
            {'id': 'review', 'requires': ['start']},
            {'id': 'finish', 'requires': ['review']},
        ]}
        transformed = {'process': [
            {'id': 'z3', 'requires': ['z2']},
            {'id': 'z1', 'requires': []},
            {'id': 'z2', 'requires': ['z1']},
        ]}
        left, right = dependency_graph(original), dependency_graph(transformed)
        self.assertEqual((left['status'], left['nodes'], left['edges']),
                         (right['status'], right['nodes'], right['edges']))
        self.assertEqual(sorted(map(len, left['components'])), sorted(map(len, right['components'])))

    def test_transition_order_and_identifier_bijection(self):
        original = {'process_transitions': [
            {'from_state': 'A', 'to_state': 'B'},
            {'from_state': 'C', 'to_state': 'D'},
        ]}
        transformed = {'process_transitions': [
            {'from_state': 'r', 'to_state': 's'},
            {'from_state': 'x', 'to_state': 'y'},
        ]}
        left, right = transition_graph(original), transition_graph(transformed)
        self.assertEqual((left['status'], left['nodes'], left['edges']),
                         (right['status'], right['nodes'], right['edges']))
        self.assertEqual(sorted(map(len, left['components'])), sorted(map(len, right['components'])))

    def test_disconnected_node_changes_connectivity(self):
        connected = {'process': [{'id': 'a', 'requires': []}, {'id': 'b', 'requires': ['a']}]}
        with_island = {'process': connected['process'] + [{'id': 'island', 'requires': []}]}
        self.assertEqual(dependency_graph(connected)['status'], 'connected')
        self.assertEqual(dependency_graph(with_island)['status'], 'disconnected')

if __name__ == '__main__': unittest.main()
