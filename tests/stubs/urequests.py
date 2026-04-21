class Response:
    def __init__(self, status_code=200, json_body=None, text=""):
        self.status_code = status_code
        self._json = json_body
        self.text = text

    def json(self):
        return self._json

    def close(self):
        pass


def get(url, headers=None, timeout=None):
    raise NotImplementedError("patch urequests.get in tests")
