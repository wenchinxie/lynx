"""Custom exceptions for lynx."""


class LynxError(Exception):
    """Base exception for all lynx errors."""

    pass


class RunNotFoundError(LynxError):
    """Raised when a run ID is not found in storage.

    Attributes:
        run_id: The run ID that was not found
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        super().__init__(f"Run not found: {run_id}")


class ValidationError(LynxError):
    """Raised when data validation fails.

    Attributes:
        field: The field that failed validation (optional)
        message: Detailed error message
    """

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        self.message = message
        if field:
            super().__init__(f"Validation error in '{field}': {message}")
        else:
            super().__init__(f"Validation error: {message}")


class StorageError(LynxError):
    """Raised when storage operations fail.

    Attributes:
        operation: The operation that failed (e.g., 'save', 'load', 'delete')
        detail: Additional error details
    """

    def __init__(self, operation: str, detail: str | None = None):
        self.operation = operation
        self.detail = detail
        msg = f"Storage error during {operation}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
