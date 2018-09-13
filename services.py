import time

import requests
import requests.auth
from requests import Response


class TwitCastingApiService:
    def __init__(self, base_url, client_id, client_secret, logger) -> None:
        """

        :param str base_url:
        :param str client_id:
        :param str client_secret:
        :param logger:
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.basic_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        self.logger = logger

    def get_webhooks(self):
        """

        :return:
        :rtype: TwitCastingApiResponse
        """
        response = requests.get(self.base_url + '/webhooks', auth=self.basic_auth)
        self.__log(response)
        if response.status_code == 200:
            return GetWebhookOkResponse(response)

        return TwitCastingApiErrorResponse(response)

    def post_webhooks(self, user_id, live_start, live_end):
        """

        :param str user_id:
        :param bool live_start:
        :param bool live_end:
        :return:
        """
        events = []
        if live_start:
            events.append('livestart')
        if live_end:
            events.append('liveend')

        response = requests.post(self.base_url + '/webhooks', auth=self.basic_auth, json={
            'user_id': user_id,
            'events': events
        })
        self.__log(response)
        if response.status_code == 200 or response.status_code == 201:
            return PostWebhookOkResponse(response)

        return TwitCastingApiErrorResponse(response)

    def delete_webhooks(self, user_id, live_start, live_end):
        """

        :param str user_id:
        :param bool live_start:
        :param bool live_end:
        :return:
        """
        events = []
        if live_start:
            events.append('livestart')
        if live_end:
            events.append('liveend')

        response = requests.delete(self.base_url + '/webhooks', auth=self.basic_auth, params={
            'user_id': user_id,
            'events[]': events
        })
        self.__log(response)
        if response.status_code == 200:
            return DeleteWebhookOkResponse(response)

        return TwitCastingApiErrorResponse(response)

    def get_user(self, user_id):
        response = requests.get(self.base_url + "/users/%s" % user_id, auth=self.basic_auth)
        self.__log(response)
        if response.status_code == 200:
            return GetUserOkResponse(response)

        return TwitCastingApiErrorResponse(response)

    def __log(self, response: Response):
        rate_limit = RateLimit(response)
        remaining_time = int(int(rate_limit.reset) - time.time())
        self.logger.debug('%s: status %s: limit: %s/%s(%s) text %s', rate_limit.api_name, response.status_code,
                          rate_limit.remaining, rate_limit.limit, remaining_time, response.text)


class TwitCastingApiResponse:
    def __init__(self, response) -> None:
        """

        :param Response response:
        """
        self.rate_limit = RateLimit(response)


class GetUserOkResponse(TwitCastingApiResponse):
    def __init__(self, response) -> None:
        """

        :param Response response:
        """
        json = response.json()
        self.id = str(json["user"]["id"])
        self.screen_id = str(json["user"]["screen_id"])
        self.image = str(json["user"]["image"])
        self.name = str(json["user"]["name"])
        super().__init__(response)


class GetWebhookOkResponse(TwitCastingApiResponse):
    def __init__(self, response) -> None:
        """

        :param Response response:
        """
        json = response.json()
        self.all_count = int(json['all_count'])
        self.webhooks = list(map(lambda w: Webhook(w['user_id'], w['event']), json['webhooks']))
        super().__init__(response)


class PostWebhookOkResponse(TwitCastingApiResponse):
    def __init__(self, response) -> None:
        """

        :param Response response:
        """
        super().__init__(response)


class DeleteWebhookOkResponse(TwitCastingApiResponse):
    def __init__(self, response) -> None:
        """

        :param Response response:
        """
        super().__init__(response)


class TwitCastingApiErrorResponse(TwitCastingApiResponse):
    def __init__(self, response):
        """

        :param Response response:
        """
        json: dict = response.json()
        self.code = int(json['error']['code'])
        self.message = str(json['error']['message'])
        super().__init__(response)


class Webhook:
    def __init__(self, user_id, event):
        """

        :param str user_id:
        :param str event:
        """
        self.user_id = user_id
        self.event = event


class RateLimit:
    def __init__(self, response):
        """

        :param Response response:
        """
        self.api_name = response.request.method + " " + response.request.path_url
        self.limit = int(response.headers['X-RateLimit-Limit']) if 'X-RateLimit-Limit' in response.headers else 0
        self.remaining = int(response.headers['X-RateLimit-Remaining']) if 'X-RateLimit-Remaining' in response.headers else 0
        self.reset = int(response.headers['X-RateLimit-Reset']) if 'X-RateLimit-Reset' in response.headers else 0
