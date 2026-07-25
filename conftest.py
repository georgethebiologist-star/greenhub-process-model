"""Lightweight root hooks used before the GreenHub test suite is collected."""

from pytest_shard_plugin import pytest_cmdline_main

__all__ = ("pytest_cmdline_main",)
