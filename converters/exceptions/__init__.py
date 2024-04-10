class ConversionError(RuntimeError):
    """
    Custom exception to be raised when the code could not be converted
    """
    ...


class OutputTooLongException(ConversionError):
    """
    Exception to be raised if the input is too long to be used by the FM
    """


class BackendTimeoutError(ConversionError):
    """
    Exception raised when the backend times out
    """
