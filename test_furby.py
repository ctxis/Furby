#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

import demo
from furby import dlc

STOCK_DLC = "./dlc/dlc2/tu003410.dlc"


class TestDLC(unittest.TestCase):

	def setUp(self):
		self.tmp = tempfile.mkdtemp()

	def tearDown(self):
		shutil.rmtree(self.tmp)

	def test_empty(self):
		self.assertEqual(dlc().dlc_sections, {})

	def test_self_test(self):
		# Re-encodes every section and checks it matches the original bytes
		dlc(STOCK_DLC, self_test=True)

	def test_round_trip(self):
		out = os.path.join(self.tmp, "out.dlc")
		dlc(STOCK_DLC).build(out)
		with open(STOCK_DLC, "rb") as a, open(out, "rb") as b:
			self.assertEqual(a.read(), b.read())

	def test_demo(self):
		# Exercises extract_palette() and quarterize() on the demo GIFs
		out = os.path.join(self.tmp, "newdlc.dlc")
		demo.make_hacked_inverting(dlc_out=out)
		self.assertEqual(sorted(dlc(out).dlc_sections), ["AMF", "APL", "CEL", "LPS", "MTR", "PAL", "SEQ", "SPR", "XLS"])


if __name__ == "__main__":
	unittest.main()
