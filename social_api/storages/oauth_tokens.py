import time
from oauth_tokens.models import AccessToken, AccessTokenGettingError, AccessTokenRefreshingError

from ..lock import distributedlock, LockNotAcquiredError
from .base import TokensStorageAbstractBase


class OAuthTokensStorage(TokensStorageAbstractBase):

    name = 'oauth_tokens'

    def __init__(self, *args, **kwargs):
        super(OAuthTokensStorage, self).__init__(*args, **kwargs)
        self.tag = self.get_from_context('tag')
        self.only_this = bool(self.tag)

    def get_tokens(self):
        queryset = AccessToken.objects.filter(provider=self.provider).order_by('-granted_at')
        if self.tag:
            queryset = queryset.filter(tag=self.tag)
        return queryset.values_list('access_token', flat=True)

    @limit_errored_calls(AccessTokenGettingError, 5)
    def update_tokens(self):
        lock_name = 'update_tokens_for_%s' % self.provider
        try:
            # the first call of method will update tokens, all others will just wait for releasing the lock
            with distributedlock(lock_name, blocking=False):
                # self.logger.info("Updating access tokens, method: %s, recursion count: %d" % (self.method,
                #                                                                               self.recursion_count))
                AccessToken.objects.fetch(provider=self.provider)
                return True
        except LockNotAcquiredError:
            # wait until lock will be released and return
            updated = False
            while not updated:
                # self.logger.info("Updating access tokens, waiting for another execution, method: %s, recursion "
                #                  "count: %d" % (self.method, self.recursion_count))
                try:
                    with distributedlock(lock_name, blocking=False):
                        updated = True
                except LockNotAcquiredError:
                    time.sleep(1)
            return True

    @limit_errored_calls(AccessTokenRefreshingError, 5)
    def refresh_tokens(self):
        # TODO: implement the same logic of distributedlock as in update_tokens method
        return AccessToken.objects.refresh(self.provider)


def limit_errored_calls(error, limit):
    count = [0]

    def _inner_decorator(fn):
        def _inner_function(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except error:
                if count[0] <= limit:
                    time.sleep(1)
                    count[0] += 1
                    return _inner_function(*args, **kwargs)
                else:
                    raise Exception("Limit of calls %s method %s achieved" % (limit, fn))

        return _inner_function

    return _inner_decorator
