"""UI integration tests with synthetic market data and isolated temporary storage."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from storage import LocalStore

APP = Path(__file__).with_name('app.py')


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalStore(Path(self.tmp.name)/'app.sqlite3')
        index = pd.date_range(end=pd.Timestamp.now(tz='America/New_York').normalize(), periods=400, freq='B')
        s = pd.Series(range(100,500), index=index, dtype=float)
        self.payload = dict(raw=s, adjusted=s, fetched=datetime.now(timezone.utc))
        self.patches = [patch('access.settings', return_value={}),
                        patch('access.get_store', return_value=(self.store,'TEST STORAGE')),
                        patch('data.load', return_value=(self.payload,None))]
        for p in self.patches:
            p.start()
        self.at = AppTest.from_file(str(APP)).run(timeout=30)

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def check_ok(self):
        self.assertEqual(len(self.at.exception),0)
        self.assertEqual(len(self.at.error),0, [e.value for e in self.at.error])

    def page(self, value):
        self.at.selectbox[0].select(value).run(timeout=30)
        self.check_ok()

    def button(self, label):
        return next(b for b in self.at.button if b.label == label)

    def test_all_pages_and_holdings(self):
        self.check_ok()
        self.page('Market')
        self.page('Asset Details')
        self.page('Holdings')
        self.button('종목 편집 열기').click().run()
        next(n for n in self.at.number_input if n.label=='보유 수량').set_value(2.)
        next(n for n in self.at.number_input if n.label=='평균 매수가 (USD)').set_value(100.)
        self.button('보유정보 저장').click().run()
        self.check_ok()
        self.assertEqual(self.store.list('portfolio')[0]['payload']['GOOGL']['shares'],2)
        self.page('Portfolio')
        self.assertEqual(self.at.metric[0].value,'$998.00')

    def test_journal_add_edit_delete_and_past_decisions(self):
        self.page('Investment Journal')
        next(t for t in self.at.text_input if t.label=='제목').set_value('UI 기록')
        self.button('저장').click().run()
        self.check_ok()
        self.assertEqual(len(self.store.list('journal')),1)
        self.button('수정 / 삭제').click().run()
        titles = [t for t in self.at.text_input if t.label=='제목']
        titles[-1].set_value('UI 수정')
        [b for b in self.at.button if b.label=='저장'][-1].click().run()
        self.check_ok()
        self.assertEqual(self.store.list('journal')[0]['payload']['title'],'UI 수정')
        self.page('Asset Details')
        self.assertTrue(any('UI 수정' in e.label for e in self.at.expander))
        self.page('Investment Journal')
        self.button('수정 / 삭제').click().run()
        next(c for c in self.at.checkbox if c.label=='이 기록을 삭제하겠습니다.').check().run()
        self.button('기록 삭제').click().run()
        self.check_ok()
        self.assertEqual(self.store.list('journal'),[])

    def test_provider_failure(self):
        with patch('data.load', return_value=(None,'테스트 조회 실패')):
            self.at.run(timeout=30)
            self.check_ok()
            self.page('Market')
            self.page('Asset Details')

    def test_access_gate(self):
        # Keep the store spy: no private data read until authentication succeeds.
        with patch('access.settings', return_value={'access':{'password':'unit-test-owner-password'}}), patch('access.get_store') as spy:
            self.at.run()
            self.assertTrue(any(t.label=='소유자 비밀번호' for t in self.at.text_input))
            spy.assert_not_called()


if __name__ == '__main__':
    unittest.main()
