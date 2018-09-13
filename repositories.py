from typing import Optional, List

from werkzeug.contrib.cache import BaseCache

from services import GetWebhookOkResponse, TwitCastingApiService, GetUserOkResponse


class WebhookRepository:
    def __init__(self, twit_casting_api_service: TwitCastingApiService, logger):
        """

        :param TwitCastingApiService twit_casting_api_service:
        """
        self.twit_casting_api_service = twit_casting_api_service
        self.logger = logger

    def get_all(self, user_repository: "UserRepository") -> List["Webhook"]:
        response = self.twit_casting_api_service.get_webhooks()
        if isinstance(response, GetWebhookOkResponse):
            result = {}
            for webhook in response.webhooks:
                if webhook.user_id in result:
                    result[webhook.user_id].append(webhook.event)
                else:
                    result[webhook.user_id] = [webhook.event]
            webhooks = []
            for user_id, events in result.items():
                user = user_repository.get_by_id(user_id)
                webhooks.append(Webhook(user, "livestart" in events, "liveend" in events))
            return webhooks

        return []


class UserRepository:

    def __init__(self, twit_casting_api_service: TwitCastingApiService, cache: BaseCache):
        """

        :param TwitCastingApiService twit_casting_api_service:
        """
        self.twit_casting_api_service = twit_casting_api_service
        self.cache = cache

    def get_by_id(self, user_id: str) -> Optional["User"]:
        """

        :param str user_id: user_id と、実は screen_id でもいける
        :return:
        """

        cached_user: User = self.cache.get('user::%s' % user_id)
        if cached_user is not None:
            return cached_user

        response = self.twit_casting_api_service.get_user(user_id)
        if isinstance(response, GetUserOkResponse):
            user = User(response)
            self.cache.set('user::%s' % user_id, value=user, timeout=24 * 60 * 60)
            return user

        return None

    def get_by_screen_id(self, screen_id: str):
        self.get_by_id(screen_id)


class User:
    def __init__(self, response: GetUserOkResponse):
        self.id = response.id
        self.screen_id = response.screen_id
        self.image = response.image
        self.name = response.name


class Webhook:
    def __init__(self, user: User, live_start: bool, live_end: bool):
        self.user = user
        self.live_start = live_start
        self.live_end = live_end
