"""Structured application-layer exceptions."""


class GreenHubApplicationError(RuntimeError):
    code = "application_error"


class RequestValidationError(GreenHubApplicationError):
    code = "request_validation_failed"


class RunNotFoundError(GreenHubApplicationError):
    code = "run_not_found"


class RunStateError(GreenHubApplicationError):
    code = "invalid_run_state"
