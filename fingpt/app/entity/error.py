class MissingResponseError(Exception):
    pass


class MissingStateDataError(Exception):
    pass


class MissingConfigDataError(Exception):
    pass


class MissingExpectedInputError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class EbpInternalError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidInputError(Exception):
    pass


class InterruptionNotAllowedError(Exception):
    pass


class GuardrailInputError(Exception):
    def __init__(self, message, trace):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.trace = trace
