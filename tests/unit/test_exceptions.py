"""Tests for lynx exceptions."""
from lynx.exceptions import LynxError, RunNotFoundError, StorageError, ValidationError


class TestExceptions:
    def test_lynx_error_is_base(self):
        """LynxError should be the base exception."""
        assert issubclass(RunNotFoundError, LynxError)
        assert issubclass(ValidationError, LynxError)
        assert issubclass(StorageError, LynxError)

    def test_run_not_found_error(self):
        """RunNotFoundError should include run_id."""
        err = RunNotFoundError("test_run_123")
        assert err.run_id == "test_run_123"
        assert "test_run_123" in str(err)

    def test_validation_error_with_field(self):
        """ValidationError should include field info."""
        err = ValidationError("must be positive", field="price")
        assert err.field == "price"
        assert "price" in str(err)

    def test_validation_error_without_field(self):
        """ValidationError should work without field."""
        err = ValidationError("invalid data")
        assert err.field is None
        assert "invalid data" in str(err)

    def test_storage_error(self):
        """StorageError should include operation info."""
        err = StorageError("save", detail="disk full")
        assert err.operation == "save"
        assert "save" in str(err)
        assert "disk full" in str(err)
