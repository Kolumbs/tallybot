"""Tallybot tests package.

Tests are organized by major logical areas:
    agents - direct integration tests with openai agents
    main - command line and main module tests
    brain - tests for brain interface
    email - tests for email interface
    units - direct unit tests for any classes or functions


Units are preferred wherever possible, integration tests only when necessary. Units must
avoid using external calls they must be mocked. Units folder structure should mirror
tallybot package structure as much as possible.
"""

import os


def load_tests(loader, standard_tests, pattern):
    """Loads all tests automatically from tests module.

    Unittest calls this function to load tests from package. Recurses
    into tests directory and assumes all .py extensions to be test
    files, except ones that start with _
    """
    pattern = "[!_]*.py"
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
    standard_tests.addTests(package_tests)
    return standard_tests
