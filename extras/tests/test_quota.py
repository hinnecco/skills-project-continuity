import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('quota',Path(__file__).parents[1]/'scripts/quota_check.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class QuotaTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'quota.json';self.now=int(time.time());self.cfg={'windows':['five_hour','seven_day'],'stale_after_minutes':30};self.args=SimpleNamespace(tool='codex',set_remaining=60,set_used=None,used=None,limit=None,source='test',window='five_hour',resets_at=None)
 def tearDown(self):self.tmp.cleanup()
 def save(self,windows,**extra):self.path.write_text(json.dumps({'windows':windows,**extra}))
 def test_partial_update_does_not_refresh_other_window(self):
  self.save({'five_hour':{'remaining_percent':70},'seven_day':{'remaining_percent':80}},observed_at=self.now-7200);self.assertEqual(q.record(str(self.path),self.args),0);self.assertEqual(q.check(str(self.path),self.cfg,self.args),4)
 def test_invalid_readings(self):
  for n in [float('nan'),float('inf'),-1,101,True,'oops']:
   self.save({'five_hour':{'remaining_percent':n,'observed_at':self.now}});self.assertNotEqual(q.check(str(self.path),{'windows':['five_hour']},self.args),0)
 def test_threshold(self):
  self.save({'five_hour':{'remaining_percent':10,'observed_at':self.now}});self.assertEqual(q.check(str(self.path),{'windows':['five_hour']},self.args),10)
 def test_stale_low_is_not_current_handoff(self):
  self.save({'five_hour':{'remaining_percent':5,'observed_at':self.now-7200}});self.assertEqual(q.check(str(self.path),{'windows':['five_hour']},self.args),4)
 def test_future_and_reset(self):
  for w in [{'remaining_percent':80,'observed_at':self.now+3600},{'remaining_percent':80,'observed_at':self.now-100,'resets_at':self.now-50}]:
   self.save({'five_hour':w});self.assertEqual(q.check(str(self.path),{'windows':['five_hour']},self.args),4)
 def test_valid(self):
  self.save({'five_hour':{'remaining_percent':60,'observed_at':self.now},'seven_day':{'remaining_percent':80,'observed_at':self.now}});self.assertEqual(q.check(str(self.path),self.cfg,self.args),0)
 def test_invalid_config(self):
  self.save({'five_hour':{'remaining_percent':60,'observed_at':self.now}});self.assertEqual(q.check(str(self.path),{'handoff_threshold_percent':float('nan')},self.args),2)
 def test_invalid_record(self):
  self.args.set_remaining=float('nan');self.assertEqual(q.record(str(self.path),self.args),2);self.assertFalse(self.path.exists())
if __name__=='__main__':unittest.main()
