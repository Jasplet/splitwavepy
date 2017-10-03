#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the fundamental routines - based on the MSAT test cases
"""

# help run this code without installation
import sys
sys.path.append("..")

import unittest
import numpy as np
import numpy.testing as npt

import splitwavepy as sw


class CoreTestCases(unittest.TestCase):
    
    def test_lag(self):
        
        # shifting works
        x = np.array([0,1,2])
        y = np.array([3,4,5])
        
        npt.assert_array_equal(sw.core.lag(x,y,2), np.array([[2],[3]]))
        npt.assert_array_equal(sw.core.lag(x,y,-2), np.array([[0],[5]]))


def suite():
    asuit = unittest.makeSuite(CoreTestCases, 'test')
    return asuit
    
if __name__ == '__main__':
    unittest.main(defaultTest='suite')