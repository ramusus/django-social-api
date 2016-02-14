from social.apps.django_app.default.models import UserSocialAuth
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import TokensStorageAbstractBase


PROVIDERS_MAP = getattr(settings, 'SOCIAL_API_SOCIAL_AUTH_PROVIDERS_MAP', {
    'vkontakte': 'vk-oauth2',
    'instagram': 'instagram',
    'facebook': 'facebook',
    'odnoklassniki': 'odnoklassniki-oauth2',
    'twitter': 'twitter',
})


class SocialAuthTokensStorage(TokensStorageAbstractBase):

    name = 'social_auth'

    def __init__(self, *args, **kwargs):
        super(SocialAuthTokensStorage, self).__init__(*args, **kwargs)
        self.user = self.get_from_context('user')
        self.only_this = bool(self.user)

    def get_provider(self):
        try:
            return PROVIDERS_MAP[self.provider]
        except KeyError:
            raise ImproperlyConfigured("Specify SOCIAL_API_SOCIAL_AUTH_PROVIDERS_MAP in settings "
                                       "with value for provider %s", self.provider)

    def get_tokens(self):
        queryset = UserSocialAuth.objects.filter(provider=self.get_provider())
        if self.user:
            queryset = queryset.filter(user=self.user)
        return [s.extra_data['access_token'] for s in queryset]

    def update_tokens(self):
        pass

    def refresh_tokens(self):
        pass
