import unittest
from app.handoff import prepare

class HandoffTests(unittest.TestCase):
    def test_approved_handoff_matches_buildestimate_schema(self):
        result = prepare({'approved': True, 'project_name': 'Kitchen demo', 'items': [
            {'code':'CABINET','quantity':'12'}, {'code':'FLOOR','quantity':'250'},
            {'code':'PAINT','quantity':'400'}]})
        self.assertEqual(result['items'][0], {'code':'CABINET','quantity':'12'})
        self.assertEqual(result['labor_rate'], 55.0)
        self.assertEqual(result['project_name'], 'Kitchen demo')
    def test_missing_approval(self):
        with self.assertRaisesRegex(ValueError, 'approval'):
            prepare({'items':[{'code':'FLOOR','quantity':1}]})
    def test_invalid_quantity_rejected(self):
        for qty in ['NaN','0','-1','','infinity','1000001']:
            with self.subTest(qty=qty), self.assertRaises(ValueError):
                prepare({'approved':True,'items':[{'code':'FLOOR','quantity':qty}]})
    def test_unknown_code_rejected(self):
        with self.assertRaisesRegex(ValueError,'catalog'):
            prepare({'approved':True,'items':[{'code':'ELECTRIC','quantity':5}]})
    def test_invalid_markups_rejected(self):
        with self.assertRaises(ValueError):
            prepare({'approved':True,'items':[{'code':'FLOOR','quantity':5}],
                     'assumptions': {'overhead_percent':101}})
if __name__=='__main__': unittest.main()
