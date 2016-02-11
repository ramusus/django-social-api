import time
from django.utils.module_loading import import_string
from django.utils import lru_cache
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.test.utils import override_settings

from .storages.base import TokensStorageAbstractBase
from .exceptions import CallsLimitError


STORAGES = getattr(settings, 'SOCIAL_API_TOKENS_STORAGES', {
    'social_api.storages.oauthtokens.OAuthTokensStorage',
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
    if not issubclass(TokensStorage, TokensStorageAbstractBase):
        raise ImproperlyConfigured('TokensStorage "%s" is not a subclass of "%s"' % TokensStorageAbstractBase)
    return TokensStorage(*args, **kwargs)


def override_api_context(provider, **kwargs):
    context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', {provider: {}}).get(provider, {})
    context.update(kwargs)
    return override_settings(SOCIAL_API_CALL_CONTEXT={provider: context})


def limit_errored_calls(error, limit):

    def _inner_decorator(fn):
        fn.count = 1

        def _inner_function(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except error:
                if fn.count < limit:
                    time.sleep(1)
                    fn.count += 1
                    return _inner_function(*args, **kwargs)
                else:
                    raise CallsLimitError("Limit of calls %s method %s achieved" % (limit, fn))

        return _inner_function

    return _inner_decorator
