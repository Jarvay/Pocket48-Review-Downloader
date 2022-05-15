import requests


class Api:
    base_url = 'https://pocketapi.48.cn'

    @staticmethod
    def request(path, body):
        return requests.post(Api.base_url + path, data=body, headers={'Content-Type': 'application/json'}).content

    @staticmethod
    def lives(body):
        return Api.request('/live/api/v1/live/getLiveList', body)

    @staticmethod
    def reviews(body):
        return Api.request('/live/api/v1/live/getLiveList', body)

    @staticmethod
    def live(body):
        return Api.request('/live/api/v1/live/getLiveOne', body)

