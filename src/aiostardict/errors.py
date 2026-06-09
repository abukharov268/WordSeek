class StarDictError(Exception):
    """Exception raised for errors in of reading StarDict files."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
