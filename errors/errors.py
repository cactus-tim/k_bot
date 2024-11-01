class CustomError(Exception):
    pass


class DatabaseConnectionError(CustomError):
    def __init__(self, message="Error with connection to db"):
        self.message = message
        super().__init__(self.message)