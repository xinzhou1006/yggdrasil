import copy
import numpy as np
import nose.tools as nt
from cis_interface import backwards
from cis_interface.metaschema.datatypes.ContainerMetaschemaType import (
    ContainerMetaschemaType)


_vallist = [np.float32(1),
            backwards.unicode2bytes('hello'),
            backwards.bytes2unicode('hello'),
            {'nested': np.int64(2)},
            [np.complex128(4), np.uint8(0)]]
_deflist = [{'type': 'float',
             'precision': 32,
             'units': ''},
            {'type': 'bytes',
             'precision': 40,
             'units': ''},
            {'type': 'unicode',
             'precision': 40,
             'units': ''},
            {'type': 'object',
             'properties': {'nested': {'type': 'int',
                                       'precision': 64,
                                       'units': ''}}},
            {'type': 'array',
             'items': [{'type': 'complex',
                        'precision': 128,
                        'units': ''},
                       {'type': 'uint',
                        'precision': 8,
                        'units': ''}]}]
_typedef = []
for v in _deflist:
    itypedef = {'type': v['type']}
    if v['type'] == 'object':
        itypedef['properties'] = copy.deepcopy(v['properties'])
    elif v['type'] == 'array':
        itypedef['items'] = copy.deepcopy(v['items'])
    _typedef.append(itypedef)
_count = len(_vallist)


def test_container_errors():
    r"""Test implementation errors on bare container class."""
    nt.assert_raises(NotImplementedError, ContainerMetaschemaType._iterate, None)
    nt.assert_raises(NotImplementedError, ContainerMetaschemaType._assign,
                     None, None, None)
    nt.assert_raises(NotImplementedError, ContainerMetaschemaType._has_element,
                     None, None)
