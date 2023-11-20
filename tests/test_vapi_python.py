#!/usr/bin/env python

"""Tests for `vapi_python` package."""


import unittest
from click.testing import CliRunner

from vapi_python import vapi_python
from vapi_python import cli


class TestVapi_python(unittest.TestCase):
    """Tests for `vapi_python` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'vapi_python.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
