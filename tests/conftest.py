import pathlib

import pytest
from click.testing import CliRunner


@pytest.fixture()
def data_fixtures():
    """Load a data fixture."""
    return pathlib.Path(__file__).parent / "test_data"


@pytest.fixture()
def runner():
    """Load a data fixture."""
    return CliRunner()
