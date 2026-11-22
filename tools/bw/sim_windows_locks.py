#!/usr/bin/env python3
"""Run a BW tool on Linux under Windows' file-sharing rules, to find MPQ handles that are kept open too long.

    python3 tools/bw/sim_windows_locks.py tools/bw/predelivery_check.py output/example_mission/Example_Mission.scx

Why: StormLib (behind eudplib's mpqapi) opens a map read-write and on Windows shares it for reading only. While
one handle is alive, every further open of the same map fails with Windows error 32 (ERROR_SHARING_VIOLATION),
in this process (another MPQ.open, eudplib.LoadMap) and in child processes (a check run as a subprocess); the
file can't be deleted either. Linux has no such locks, so these bugs only show on Windows. This wrapper makes
them visible on Linux: it raises the same error when a map that is still open in this process is opened again,
handed to a subprocess or removed. Release a handle with `del` (or by leaving the function that holds it);
CPython closes it at once, gc.collect() is not needed.
Linux only (it reads /proc/self/fd). Exit code and output are the wrapped tool's."""
import os, sys, runpy, subprocess

if not os.path.isdir('/proc/self/fd'):
    sys.exit('sim_windows_locks.py needs Linux (/proc/self/fd); on Windows just run the tool itself.')

from eudplib.bindings._rust import mpqapi

_Real = mpqapi.MPQ
MAPS = ('.scx', '.scm')


def _held_maps():
    out = set()
    for fd in os.listdir('/proc/self/fd'):
        try: p = os.path.realpath(os.path.join('/proc/self/fd', fd))
        except OSError: continue
        if p.lower().endswith(MAPS): out.add(p)
    return out


def _violation(what, path):
    return RuntimeError(f'UnknownCode(ErrorCode(32)) [simulated Windows sharing violation: {what} {path!r} '
                        f'while this process still holds an MPQ handle on it]')


def _check(what, path):
    p = os.path.realpath(os.fsdecode(path))
    if p in _held_maps(): raise _violation(what, path)


class _MPQ:
    """Stand-in for mpqapi.MPQ that checks for an existing handle before opening."""
    def __init__(self, real): self._real = real
    def __getattr__(self, name): return getattr(self._real, name)

    @staticmethod
    def open(path, *a, **k):
        _check('MPQ.open', path); return _MPQ(_Real.open(path, *a, **k))

    @staticmethod
    def create(path, *a, **k):
        _check('MPQ.create', path); return _MPQ(_Real.create(path, *a, **k))

    @staticmethod
    def clone_with_sector_size(path, *a, **k):
        _check('MPQ.clone_with_sector_size', path); return _MPQ(_Real.clone_with_sector_size(path, *a, **k))


mpqapi.MPQ = _MPQ
_popen_init, _remove = subprocess.Popen.__init__, os.remove


def _checked_popen_init(self, args, *a, **k):
    held = _held_maps()
    if held:
        argv = [args] if isinstance(args, (str, bytes)) else list(args)
        text = ' '.join(os.fsdecode(x) for x in argv)
        for p in held:
            if p in text or os.path.basename(p) in text:
                raise _violation(f'subprocess {os.path.basename(os.fsdecode(argv[0]))} gets', p)
    return _popen_init(self, args, *a, **k)


def _checked_remove(path, *a, **k):
    _check('os.remove', path); return _remove(path, *a, **k)


subprocess.Popen.__init__ = _checked_popen_init
os.remove = _checked_remove

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    runpy.run_path(script, run_name='__main__')
