#!/usr/bin/env python3
"""Small synthetic unit tests; no experimental samples are changed."""
import unittest,math
from analyze_best_last import aggregate,flags
class TestStats(unittest.TestCase):
 def test_distinct_weighting(self):
  out=aggregate([dict(pixels=1,mae_mm=10.,sq_sum_m2=.0001,over50_pixels=0),dict(pixels=9,mae_mm=2.,sq_sum_m2=.000036,over50_pixels=0)])
  self.assertEqual(out['E_mae_mm'],6.)
  self.assertAlmostEqual(out['Q_rmse_mm'],math.sqrt(.000136/10)*1000)
 def test_leave_one_can_fail_despite_overall_pass(self):
  p=dict(E_mae_mm=10.2,Q_rmse_mm=20,over50_fraction=.01);v=dict(E_mae_mm=10,Q_rmse_mm=20,over50_fraction=.01)
  lo=[dict(omitted_scene=1,P_V_MAE_ratio=1.031,P_V_RMSE_ratio=1.)]
  out=flags(p,v,lo);self.assertTrue(out['overall_MAE_ok']);self.assertFalse(out['full_G4'])
 def test_global_tail_units(self):
  p=dict(E_mae_mm=10,Q_rmse_mm=20,over50_fraction=.0121);v=dict(E_mae_mm=10,Q_rmse_mm=20,over50_fraction=.01)
  lo=[dict(omitted_scene=1,P_V_MAE_ratio=1.,P_V_RMSE_ratio=1.)]
  out=flags(p,v,lo);self.assertFalse(out['global_tail_ok']);self.assertAlmostEqual(out['P_minus_V_over50_percentage_points'],.21)
 def test_do_not_round_before_gate(self):
  p=dict(E_mae_mm=1.0300000001,Q_rmse_mm=1,over50_fraction=0);v=dict(E_mae_mm=1.,Q_rmse_mm=1,over50_fraction=0)
  lo=[dict(omitted_scene=1,P_V_MAE_ratio=1.,P_V_RMSE_ratio=1.)]
  self.assertFalse(flags(p,v,lo)['overall_MAE_ok'])
 def test_exact_bound_inclusive(self):
  p=dict(E_mae_mm=1.03,Q_rmse_mm=1.03,over50_fraction=.002);v=dict(E_mae_mm=1.,Q_rmse_mm=1.,over50_fraction=0.)
  lo=[dict(omitted_scene=1,P_V_MAE_ratio=1.03,P_V_RMSE_ratio=1.03)]
  self.assertTrue(flags(p,v,lo)['full_G4'])
if __name__=='__main__':unittest.main()
