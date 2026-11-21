#!/usr/bin/env python3
"""Showcase check for Brood War maps: same rule and code as tools/wc3/check_showcase.py (every new unit, hero or ability
gets a SHOWCASE line in the Design_Note with a concrete map situation). Usage: python3 tools/bw/check_showcase.py MAP.scx
A plain wrapper instead of a symlink, so the repository also works on Windows checkouts."""
import os, runpy
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wc3', 'check_showcase.py'), run_name='__main__')
