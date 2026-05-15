class Rail0ApiError(Exception):
    """Raised for non-2xx responses from the RAIL0 API."""

    status: int
    error: str

    def __init__(self, status: int, error: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.error = error
