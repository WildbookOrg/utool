#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import utool as ut


def run_tests():
    # Build module list and run tests
    import sys
    exclude_doctests_fnames = set(['__init__.py'])

    exclude_dirs = [
        '_broken',
        'old',
        'tests',
        'timeits',
        '_scripts',
        '_timeits',
        '_doc',
        'notebook',
    ]
    dpath_list = ['utool']
    doctest_modname_list = ut.find_doctestable_modnames(
        dpath_list, exclude_doctests_fnames, exclude_dirs)

    for modname in doctest_modname_list:
        exec('import ' + modname, globals(), locals())
    module_list = [sys.modules[name] for name in doctest_modname_list]
    ut.doctest_module_list(module_list)

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    run_tests()
