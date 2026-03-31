class FrappeCloudError(Exception):
    """Base exception for Frappe Cloud SDK."""
    pass

class APIError(FrappeCloudError):
    """Exception raised for API errors (non-2xx responses)."""
    def __init__(self, message, status_code=None, raw_response=None):
        super().__init__(message)
        self.status_code = status_code
        self.raw_response = raw_response

class AuthenticationError(APIError):
    """Exception raised for invalid credentials (401/403)."""
    pass

class ValidationError(APIError):
    """Exception raised for validation failures (e.g. 417 Expectation Failed or 400 Bad Request)."""
    pass
