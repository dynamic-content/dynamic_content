import unittest

from dyc.core.mvc._pathmapper import PathHandlerException
from dyc import core

__author__ = 'justusadam'


class TestPathMapper(unittest.TestCase):
    def test_add_path(self):
        p = core.get_component('pathmapper')
        testpaths = [
            [
                'hello/bla', lambda : 4, 'hello/bla', 4
            ],
            [
                'hello/loko/nunu', lambda : 7, 'hello/loko/nunu', 7
            ],
            [
                'tryi/{int}', lambda a: a, 'tryi/4', 4
            ],
            [
                'tryit/**', lambda s: s, 'tryit/lolo', 'tryit/lolo'
            ],
            [
                'horn/{int}/tee/**', lambda a, b: (a,b), 'horn/4/tee/tree/branch', (4,'horn/4/tee/tree/branch')
            ]
        ]
        for path, handler, teststring, result in testpaths[0:4]:
            p.add_path(path, handler)
            self.assertEqual(p(teststring), result)

        for path, handler, teststring, result in testpaths[4:]:
            p.add_path(path, handler)
            self.assertTupleEqual(p(teststring), result)

        for path, handler, teststring, result in testpaths[0:2]:
            self.assertRaises(PathHandlerException, p.add_path, path, handler)