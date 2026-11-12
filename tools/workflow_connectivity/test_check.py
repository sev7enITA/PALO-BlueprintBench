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

if __name__ == '__main__': unittest.main()
