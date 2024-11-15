class CustomError(Exception):
    pass


class Error404(CustomError):
    def __init__(self, message="Error with status code 404"):
        self.message = message
        super().__init__(self.message)


class Error409(CustomError):
    def __init__(self, message="Error with status code 409"):
        self.message = message
        super().__init__(self.message)


class DatabaseConnectionError(CustomError):
    def __init__(self, message="Error with connection to db"):
        self.message = message
        super().__init__(self.message)


class ContentError(CustomError):
    def __init__(self, message="GPT response is incorrect"):
        self.message = message
        super().__init__(self.message)


class FileError(CustomError):
    user_id: int

    def __init__(self, user_id, message="GPT response is incorrect"):
        self.user_id = user_id
        self.message = message
        super().__init__(self.message)


class ProxyError(CustomError):
    def __init__(self, message="Proxy fallen"):
        self.message = message
        super().__init__(self.message)


class NumberError(CustomError):
    def __init__(self, user_id, dialog_id, message="Number dont in range"):
        self.user_id = user_id
        self.dialog_id = dialog_id
        self.message = message
        super().__init__(self.message)
