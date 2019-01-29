class NotFound(Exception):
    def __init__(self, message):
        super(NotFound, self).__init__()
        self.message = message

    def to_dict(self):
        return {'result': 'error', 'message': self.message}
