import requests

class request_sender:
    def send_request(self, url: str, method: str = "GET", headers: dict = {}, payload: dict = {}) -> str:
        response = requests.request(method, url, headers=headers, data=payload)
        return response.text