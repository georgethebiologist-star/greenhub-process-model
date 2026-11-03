"""Structured application-layer exceptions."""


class GreenHubApplicationError(RuntimeError):
    code = "application_error"


class RequestValidationError(GreenHubApplicationError):
    code = "request_validation_failed"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code


class RunNotFoundError(GreenHubApplicationError):
    code = "run_not_found"


class RunStateError(GreenHubApplicationError):
    code = "invalid_run_state"
