import pytest
from tests.helpers import FakeDataStore, FakeFileStore


@pytest.fixture
def fake_ds():
    return FakeDataStore()


@pytest.fixture
def fake_fs():
    return FakeFileStore()
