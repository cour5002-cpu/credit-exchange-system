class BusinessError(ValueError):
    """Business rule violation that can be translated to an API response."""

    def __init__(self, message, code=40001, status=400):
        super().__init__(message)
        self.code = code
        self.status = status
