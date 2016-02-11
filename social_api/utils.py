from django.utils.module_loading import import_string
from django.utils import lru_cache
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.test.utils import override_settings

from .storages.base import TokensStorageAbstractBase


STORAGES = getattr(settings, 'SOCIAL_API_TOKENS_STORAGES', {
    'social_api.storages.oauth_tokens.OAuthTokensStorage',
    'social_api.storages.social_auth.SocialAuthTokensStorage',
})


def get_storages(*args, **kwargs):
    for import_path in STORAGES:
        yield get_storage(import_path, *args, **kwargs)


@lru_cache.lru_cache(maxsize=None)
def get_storage(import_path, *args, **kwargs):
    """
    Imports the staticfiles finder class described by import_path, where
    import_path is the full Python path to the class.
    """
    TokensStorage = import_string(import_path)
    if not issubclass(TokensStorageAbstractBase):
        raise ImproperlyConfigured('TokensStorage "%s" is not a subclass of "%s"' % TokensStorageAbstractBase)
    return TokensStorage(*args, **kwargs)


def override_api_context(provider, **kwargs):
    context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', {provider: {}}).get(provider, {})
    context.update(kwargs)
    return override_settings(SOCIAL_API_CALL_CONTEXT={provider: context})
