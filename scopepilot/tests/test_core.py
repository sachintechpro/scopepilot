import unittest
from app.core import review, normalize_llm, catalog, validated_quantity

class ScopeReviewTests(unittest.TestCase):
    def test_explicit_quantities(self):
        result=review('Install 250 sqft of LVP flooring and paint 400 sqft of walls in Woodland Hills next month.')
        codes={i['code']:i['quantity'] for i in result['items']}
        self.assertEqual(codes['FLOOR'],'250')
        self.assertEqual(codes['PAINT'],'400')
    def test_missing_quantity_is_not_invented(self):
        result=review('Replace kitchen cabinets and repaint the interior walls at the house.')
        self.assertTrue(result['items'])
        self.assertTrue(all(i['quantity'] is None for i in result['items']))
        self.assertGreaterEqual(len(result['questions']),2)
    def test_unknown_scope_generates_question(self):
        result=review('Please provide a quote for the project next month at our home.')
        self.assertFalse(result['items'])
        self.assertTrue(any('work items' in q.lower() for q in result['questions']))
    def test_invalid_request(self):
        with self.assertRaises(ValueError): review('Hi')
    def test_invalid_quantities(self):
        self.assertIsNone(validated_quantity('NaN'))
        self.assertIsNone(validated_quantity('-5'))
        self.assertIsNone(validated_quantity('infinite'))
    def test_ai_filters_bad_catalog_and_fabricated_evidence(self):
        source='Install 200 sqft LVP flooring in the kitchen.'
        result=normalize_llm({'items':[
            {'code':'FLOOR','quantity':200,'evidence':'LVP flooring'},
            {'code':'WIRING','quantity':1,'evidence':'install'},
            {'code':'ROOF','quantity':3,'evidence':'roof mentioned by model'}],
            'questions':['What is the location?']},source)
        self.assertEqual([x['code'] for x in result['items']],['FLOOR'])
    def test_catalog_matches_estimator(self):
        self.assertEqual(len(catalog()),7)
if __name__=='__main__':unittest.main()
