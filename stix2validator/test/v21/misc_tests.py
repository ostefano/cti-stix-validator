from io import open
import logging
import os
import re
import sys

import pytest

from ... import (NoJSONFileFoundError, ValidationOptions, print_results,
                 run_validation, validate_file, validate_string)
from .tool_tests import VALID_TOOL

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

EXAMPLE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                       '..', '..', 'schemas-2.1', 'examples',
                       'indicator-to-campaign-relationship.json')
CUSTOM = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      'test_examples', 'tlp-amber.json')
CUSTOM_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          'test_schemas')
RELATIVE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_examples', 'tool.json')
RELATIVE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'test_schemas')
IDENTITY = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_examples', 'identity.json')
IDENTITY_CUSTOM = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'test_examples', 'identity_custom.json')
IDENTITY_UNICODE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'test_examples', 'identity_unicode.json')
INVALID_BRACES = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'test_examples', 'invalid_braces.json')
INVALID_COMMA = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'test_examples', 'invalid_comma.json')
INVALID_IDENTITY = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'test_examples', 'invalid_identity.json')
INVALID_TIMESTAMP = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'test_examples', 'invalid_timestamp.json')


def test_run_validation(caplog):
    caplog.set_level('INFO')
    options = ValidationOptions(files=[EXAMPLE])
    results = run_validation(options)

    assert results[0].is_valid

    print_results(results)
    assert 'STIX JSON: Valid' in caplog.text


def test_run_validation_nonexistent_file():
    options = ValidationOptions(files=['asdf.json'])
    with pytest.raises(NoJSONFileFoundError):
        run_validation(options)


def test_run_validation_silent(caplog):
    options = ValidationOptions(files=[EXAMPLE], silent=True)
    results = run_validation(options)
    print_results(results)
    assert caplog.text == ''


def test_validate_file(caplog):
    caplog.set_level('INFO')
    results = validate_file(EXAMPLE)
    assert results.is_valid

    print_results(results)
    assert 'STIX JSON: Valid' in caplog.text


def test_validate_file_custom(caplog):
    caplog.set_level('INFO')
    results = validate_file(CUSTOM, options=ValidationOptions(schema_dir=CUSTOM_DIR))
    assert results.is_valid

    print_results(results)
    assert 'STIX JSON: Valid' in caplog.text


def test_validate_file_custom_relative(caplog):
    caplog.set_level('INFO')
    results = validate_file(RELATIVE, options=ValidationOptions(schema_dir=RELATIVE_DIR))
    assert results.is_valid

    print_results(results)
    assert 'STIX JSON: Valid' in caplog.text


def test_validate_file_warning(caplog):
    results = validate_file(IDENTITY_CUSTOM)
    assert results.is_valid

    print_results(results)
    assert re.search("Custom property .+ should ", caplog.text)


def test_validate_file_unicode(caplog):
    results = validate_file(IDENTITY_UNICODE)
    assert results.is_valid


def test_validate_file_invalid_brace(caplog):
    results = validate_file(INVALID_BRACES)
    assert not results.is_valid

    print_results(results)
    assert 'Fatal Error: Invalid JSON input' in caplog.text


def test_validate_file_invalid_comma(caplog):
    results = validate_file(INVALID_COMMA)
    assert not results.is_valid

    print_results(results)
    assert 'Fatal Error: Expecting property name' in caplog.text


def test_validate_file_invalid_missing_modified(caplog):
    results = validate_file(INVALID_IDENTITY)
    assert not results.is_valid

    print_results(results)
    assert "'modified' is a required property" in caplog.text


def test_validate_string(caplog):
    caplog.set_level('INFO')
    with open(IDENTITY, encoding='utf-8') as f:
        results = validate_string(f.read())
    assert results.is_valid

    print_results(results)
    assert 'STIX JSON: Valid' in caplog.text


def test_validate_string_warning(caplog):
    with open(IDENTITY_CUSTOM, encoding='utf-8') as f:
        results = validate_string(f.read())
    assert results.is_valid

    print_results(results)
    assert re.search("Custom property .+ should ", caplog.text)


def test_validate_string_invalid_timestamp(caplog):
    with open(INVALID_TIMESTAMP, encoding='utf-8') as f:
        results = validate_string(f.read())
    assert not results.is_valid

    print_results(results)
    assert re.search("'modified' .+ must be later than or equal to 'created'", caplog.text)


def test_print_results_invalid_parameter():
    with pytest.raises(ValueError) as excinfo:
        print_results('these results are valid')
    assert 'Argument to print_results() must be' in str(excinfo.value)


def test_run_validation_stdin(monkeypatch):
    monkeypatch.setattr(sys.stdin, 'read', lambda: VALID_TOOL)
    options = ValidationOptions(files=sys.stdin)
    results = run_validation(options)
    assert results[0].is_valid
