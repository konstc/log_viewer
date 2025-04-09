""" Log viewer's exceptions module """

from typing import Optional

class LogViewerError(Exception):
    """
    Base class for all Log viewer related exceptions
    """

    def __init__(
        self,
        message: str = "",
        error_code: Optional[int] = None,
    ) -> None:
        self._error_code = error_code
        super().__init__(
            message if error_code is None else 
            f"{message} [Error Code {error_code}]"
        )

class LogViewerInvalidConfig(LogViewerError):
    """
    Indicates that the app configuration is invalid
    """

class LogViewerInvalidFile(LogViewerError):
    """
    Indicates that the opened file is invalid
    """
