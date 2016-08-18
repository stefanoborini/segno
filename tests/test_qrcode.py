# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 -- Lars Heuer - Semagia <http://www.semagia.com/>.
# All rights reserved.
#
# License: BSD License
#
"""\
QR Code tests.

:author:       Lars Heuer (heuer[at]semagia.com)
:organization: Semagia - http://www.semagia.com/
:license:      BSD License
"""
from __future__ import absolute_import, unicode_literals
import os
import io
from itertools import chain
import tempfile
import pytest
import segno
from segno import ModeError, VersionError, ErrorLevelError, DataOverflowError
from segno import consts
from codecs import open

_LEGAL_MICRO_VERSIONS = tuple(chain(consts.MICRO_VERSION_MAPPING.keys(),
                                    [v.lower() for v in consts.MICRO_VERSION_MAPPING.keys()]))
_LEGAL_VERSIONS = tuple(chain(range(1, 41), [str(v) for v in range(1, 41)]))

_LEGAL_ERROR_LEVELS = tuple(chain(consts.ERROR_MAPPING.keys(),
                                  [e.lower() for e in consts.ERROR_MAPPING.keys()]))


def test_illegal_mode_micro():
    def check(version, mode):
        with pytest.raises(ModeError):
            segno.make(1, version=version, mode=mode)
    illegal_micro_modes = (
        # version, illegal mode
        ('M1', 'alphanumeric'),
        ('M1', 'byte'),
        ('M2', 'byte'),
    )
    for version, mode in illegal_micro_modes:
        yield check, version, mode
        yield check, version.lower(), mode


def test_micro_version_contradicts_micro():

    def check(version):
        with pytest.raises(VersionError):
            qr = segno.make(1, version=version, micro=False)

    for version in _LEGAL_MICRO_VERSIONS:
        yield check, version


def test_version_contradicts_micro():

    def check(version):
        with pytest.raises(VersionError):
            segno.make(1, version=version, micro=True)
    for version in _LEGAL_VERSIONS:
        yield check, version


def test_illegal_version():

    def check(version):
        with pytest.raises(VersionError):
            segno.make('a', version=version)

    for version in ('M0', 'M5', -1, 0, 41, 'M1 ', object()):
        yield check, version


def test_valid_mirco_versions():
    def check(version):
        qr = segno.make(1, version=version)
        assert version.upper() == qr.version
        assert qr.is_micro
    for version in _LEGAL_MICRO_VERSIONS:
        yield check, version


def test_valid_versions():
    def check(version):
        qr = segno.make(1, version=version)
        assert int(version) == qr.version
        assert not qr.is_micro
    for version in _LEGAL_VERSIONS:
        yield check, version


def test_legal_error_levels():
    def check(error):
        qr = segno.make(1, error=error)
        assert error.upper() == qr.error
    for error in _LEGAL_ERROR_LEVELS:
        yield check, error


def test_illegal_error_level():

    def check(error):
        with pytest.raises(ErrorLevelError):
            segno.make(1, error=error)

    for error in ('R', 'M ', ' L'):
        yield check, error


def test_illegal_error_level_micro():
    with pytest.raises(ErrorLevelError):
        segno.make('test', error='H', micro=True)


def test_data_too_large():

    def check(data, wrong_version):
        with pytest.raises(DataOverflowError):
            segno.make(data, version=wrong_version)

    test_data = (
        ('abcdefghijklmno', 1),
        (123456, 'M1'),
    )
    for data, wrong_version in test_data:
        yield check, data, wrong_version


def _calc_size(dim, border, scale=1):
    return (dim + 2 * border) * scale


def test_symbol_size():
    qr = segno.make('Hello world', micro=False)
    width, height = 21, 21
    border = 0
    assert (width, height) == qr.symbol_size(border=border)
    border = 1
    assert (_calc_size(width, border) == _calc_size(width, border)), qr.symbol_size(border=border)
    border = 4  # (default border)
    assert (_calc_size(width, border) == _calc_size(width, border)), qr.symbol_size()
    assert (_calc_size(width, border) == _calc_size(width, border)), qr.symbol_size(scale=1)
    assert (_calc_size(width, border, 4), _calc_size(width, border, 4)) == qr.symbol_size(scale=4)
    border = 0
    assert (_calc_size(width, border, 4), _calc_size(width, border, 4)) == qr.symbol_size(border=border, scale=4)


def test_symbol_size_micro():
    qr = segno.make('A', version='m2')
    width, height = 13, 13  # Micro QR Code Version M2 size
    border = 0
    assert (width, height) == qr.symbol_size(border=border)
    border = 1
    dim = _calc_size(width, border)
    assert (dim, dim) == qr.symbol_size(border=border)
    border = 2  # (default border)
    dim = _calc_size(width, border)
    assert (dim, dim) == qr.symbol_size()
    assert (dim, dim) == qr.symbol_size(scale=1)
    dim = _calc_size(width, border, 4)
    assert (dim, dim) == qr.symbol_size(scale=4)
    border = 0
    dim = _calc_size(width, border, 4)
    assert (dim, dim) == qr.symbol_size(border=border, scale=4)


def test_symbol_size_scale_int():
    qr = segno.make_qr('test')
    assert (21, 21) == qr.symbol_size(border=0)


def test_symbol_size_scale_int2():
    qr = segno.make_qr('test')
    border = 2
    dim = 21 + 2 * border
    assert (dim, dim) == qr.symbol_size(border=border)


def test_symbol_size_scale_float():
    qr = segno.make_qr('test')
    dim = 21 * 2.5
    assert (dim, dim) == qr.symbol_size(scale=2.5, border=0)


def test_symbol_size_scale_float2():
    qr = segno.make_qr('test')
    border = 2
    dim = (21 + 2 * border) * 1.5
    assert (dim, dim) ==  qr.symbol_size(scale=1.5, border=border)


def test_designator():
    qr = segno.make('test', version=40, error='L')
    assert '40-L' == qr.designator


def test_designator2():
    qr = segno.make('test', version=8, error='m')
    assert '8-M' == qr.designator


def test_designator_micro():
    qr = segno.make('test', version='M4', error='L')
    assert 'M4-L' == qr.designator


def test_designator_micro2():
    qr = segno.make('12', version='M1')
    assert 'M1' == qr.designator


def test_error_m1():
    qr = segno.make('12')
    assert 'M1' == qr.version
    assert qr.error is None


def test_default_border():
    qr = segno.make_qr(12)
    assert 4 == qr.default_border_size


def test_default_border_mirco():
    qr = segno.make_micro(12, version='m4')
    assert 2 == qr.default_border_size


def test_eq():
    qr = segno.make('Hello')
    qr2 = segno.make('Hello')
    assert qr == qr2


def test_neq():
    qr = segno.make('Hello')
    qr2 = segno.make('hello')
    assert qr == qr
    assert qr2 == qr2
    assert qr != qr2


def test_save_png_buffer():
    qr = segno.make_qr('test')
    out = io.BytesIO()
    qr.save(out, kind='png')
    out.seek(0)
    expected = b'\211PNG\r\n\032\n'  # PNG magic number
    val = out.read(len(expected))
    assert expected == val


def test_save_png_filestream():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
    qr.save(f)
    f.close()
    f = open(f.name, mode='rb')
    expected = b'\211PNG\r\n\032\n'  # PNG magic number
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_png_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='rb')
    expected = b'\211PNG\r\n\032\n'  # PNG magic number
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_svg_filestream():
    def check(suffix):
        qr = segno.make_qr('test')
        f = tempfile.NamedTemporaryFile('wb', suffix='.' + suffix, delete=False)
        qr.save(f)
        f.close()
        f = open(f.name, mode='rb')
        val = f.read(6)
        f.close()
        os.unlink(f.name)
        assert b'<?xml ' == val

    # Check usual file extension and if QRCode.save is case insensitive
    yield check, 'svg'
    yield check, 'SvG'
    yield check, 'SVG'
    yield check, 'Svg'


def test_save_svg_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.svg', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='rb')
    val = f.read(6)
    f.close()
    os.unlink(f.name)
    assert b'<?xml ' == val


def test_save_svgz_filename():
    import gzip
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.svgz', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='rb')
    expected = b'\x1f\x8b\x08'  # gzip magic number
    val = f.read(len(expected))
    f.close()
    f = gzip.open(f.name)
    try:
        content = f.read(6)
    finally:
        f.close()
    os.unlink(f.name)
    assert expected == val
    assert b'<?xml ' == content


def test_save_pdf_filestream():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.pdf', delete=False)
    qr.save(f)
    f.close()
    f = open(f.name, mode='rb')
    val = f.read(5)
    f.close()
    os.unlink(f.name)
    assert b'%PDF-' == val


def test_save_pdf_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('wb', suffix='.pdf', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='rb')
    val = f.read(5)
    f.close()
    os.unlink(f.name)
    assert b'%PDF-' == val


def test_save_eps_filestream():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.eps', delete=False)
    qr.save(f)
    f.close()
    f = open(f.name, mode='r')
    expected = '%!PS-Adobe-3.0 EPSF-3.0'
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_eps_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.eps', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='r')
    expected = '%!PS-Adobe-3.0 EPSF-3.0'
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_txt_filestream():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False)
    qr.save(f)
    f.close()
    f = open(f.name, mode='r')
    expected = '000000'
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_txt_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False)
    f.close()
    qr.save(f.name)
    f = open(f.name, mode='r', encoding='utf-8')
    expected = '000000'
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_kind_filestream():
    def check(kind):
        qr = segno.make_qr('test')
        f = tempfile.NamedTemporaryFile('w', suffix='.murks', delete=False)
        qr.save(f, kind=kind)
        f.close()
        f = open(f.name, mode='r')
        expected = '%!PS-Adobe-3.0 EPSF-3.0'
        val = f.read(len(expected))
        f.close()
        os.unlink(f.name)
        assert expected == val

    # Check if "kind" is recognized and if QRCode.save is case insensitive
    yield check, 'eps'
    yield check, 'EpS'
    yield check, 'EPS'
    yield check, 'Eps'


def test_save_kind_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.murks', delete=False)
    f.close()
    qr.save(f.name, kind='eps')
    f = open(f.name, mode='r')
    expected = '%!PS-Adobe-3.0 EPSF-3.0'
    val = f.read(len(expected))
    f.close()
    os.unlink(f.name)
    assert expected == val


def test_save_invalid_filename():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.murks', delete=True)
    with pytest.raises(ValueError):
        qr.save(f.name)


def test_save_invalid_filename2():
    qr = segno.make_qr('test')
    f = tempfile.NamedTemporaryFile('w', suffix='.murks', delete=True)
    with pytest.raises(ValueError):
        qr.save(f)


def test_unknown_converter():
    qr = segno.make_qr('test')
    with pytest.raises(AttributeError):
        qr.to_murks()


if __name__ == '__main__':
    pytest.main(['-x', __file__])

