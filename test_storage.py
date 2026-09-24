import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import requests
from storage import LocalStore, SupabaseStore, StorageError, ConflictError, validate_entry, filter_entries


def entry(title='금리 조정 판단'):
    return validate_entry(dict(date='2026-09-24', ticker='GOOGL', action='Hold', title=title,
                               reasoning='핵심 논리 유지', thesis='현금흐름', risk='미국 금리', check_again='실적', notes='테스트'))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'journal.sqlite3'
        self.store = LocalStore(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_crud_reopen_and_conflict(self):
        r = self.store.save('journal', entry())
        self.assertEqual(LocalStore(self.path).list('journal')[0]['payload']['title'], '금리 조정 판단')
        changed = self.store.save('journal', entry('수정'), r['id'], r['revision'])
        self.assertEqual(changed['revision'], 2)
        self.assertEqual(self.store.list('journal')[0]['payload']['title'], '수정')
        with self.assertRaises(ConflictError):
            self.store.save('journal', entry('오래된 수정'), r['id'], 1)
        with self.assertRaises(ConflictError):
            self.store.delete(r['id'], 1)
        self.store.delete(r['id'], 2)
        self.assertEqual(self.store.list('journal'), [])
        with self.store.connect() as con:
            self.assertEqual(con.execute('SELECT deleted FROM documents').fetchone()[0], 1)

    def test_isolation(self):
        self.store.save('journal', entry())
        other = LocalStore(Path(self.temp.name)/'other.sqlite3')
        self.assertEqual(other.list('journal'), [])

    def test_filters_and_validation(self):
        self.store.save('journal', entry())
        rows = self.store.list('journal')
        self.assertEqual(len(filter_entries(rows, '2026-09-24','2026-09-24','GOOGL','Hold','금리')),1)
        for args in [dict(start='2026-09-25'),dict(end='2026-09-23'),dict(ticker='NEE'),dict(action='Buy'),dict(keyword='없음')]:
            self.assertEqual(filter_entries(rows, **args), [])
        with self.assertRaises(ValueError):
            validate_entry(dict(date='bad', title='x', action='Hold'))
        with self.assertRaises(ValueError):
            validate_entry(dict(date='2026-09-24', title='', ticker='GOOGL', action='Hold'))

    def test_portfolio_document(self):
        self.store.save('portfolio', {'GOOGL': {'shares':2}}, 'portfolio')
        self.assertEqual(len(self.store.list('portfolio')), 1)
        self.assertEqual(self.store.list('journal'), [])

    def test_remote_contract_and_failure(self):
        store = SupabaseStore('https://test.supabase.co','sb_secret_test')
        response = Mock(status_code=201, content=b'[]')
        response.json.return_value = [{'id':'abc','revision':1}]
        with patch('storage.requests.request', return_value=response) as call:
            self.assertEqual(store.save('journal', entry(), 'abc')['id'], 'abc')
            self.assertEqual(call.call_args.kwargs['headers']['apikey'], 'sb_secret_test')
            self.assertNotIn('Authorization', call.call_args.kwargs['headers'])
            self.assertEqual(call.call_args.kwargs['json']['payload']['ticker'], 'GOOGL')
        with patch('storage.requests.request', side_effect=requests.Timeout):
            with self.assertRaises(StorageError):
                store.list('journal')
        response.status_code = 403
        with patch('storage.requests.request', return_value=response):
            with self.assertRaises(StorageError):
                store.list('journal')
        response.status_code = 200
        response.json.return_value = []
        with patch('storage.requests.request', return_value=response):
            with self.assertRaises(ConflictError):
                store.delete('abc', 1)


if __name__ == '__main__':
    unittest.main()
