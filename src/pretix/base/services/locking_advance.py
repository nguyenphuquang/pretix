import logging
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from pretix.base.models import EventLock

logger = logging.getLogger('pretix.base.locking_advance')
LOCK_TIMEOUT = 120

class AdvanceLockManager:
    def __init__(self, keys):
        self.keys = keys

    def __enter__(self):
        lock_keys(self.keys)
        return now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        release_keys(self.keys)
        if exc_type is not None:
            return False


class LockTimeoutException(Exception):
    pass


class LockReleaseException(Exception):
    pass

global_lock = {}

def lock_keys(keys):
    # if hasattr(event, '_lock_advance') and event._lock:
        # return True

    if settings.HAS_REDIS:
        return lock_keys_redis(keys)
    else:
        raise NotImplementedError()


def release_keys(keys):
    # if not hasattr(event, '_lock') or not event._lock:
        # raise LockReleaseException('Lock is not owned by this thread')
    if settings.HAS_REDIS:
        return release_keys_redis(keys)
    else:
        raise NotImplementedError()


def redis_lock_from_keys(keys):
    from django_redis import get_redis_connection
    from redis.lock import Lock

    rc = get_redis_connection("redis")
    return [Lock(redis=rc, name='lock_%s' % key, timeout=LOCK_TIMEOUT) for key in keys]


def lock_keys_redis(keys):
    from redis.exceptions import RedisError

    locks = redis_lock_from_keys(keys)
    count = len(locks)

    if count == 0: return True

    retries = 5
    locked = [False for lock in locks]
    for i in range(retries):
        for i_lock in range(locks):
            if locked[i_lock]: continue
            try:
                if lock.acquire(False):
                    locked[i_lock] = True
                    count -= 1
            except RedisError:
                logger.exception('Error locking an event')
                for j in range(locked):
                    if locked[j]:
                        try:
                            locks[j].release()
                        except Error:
                            pass
                raise LockTimeoutException()
        if count == 0: return True
        time.sleep(2 ** i / 100)

    for j in range(locked):
        if locked[j]:
            try:
                locks[j].release()
            except Error:
                pass
    raise LockTimeoutException()


def release_keys_redis(keys):
    from redis import RedisError

    locks = redis_lock_from_keys(keys)
    has_error = False
    for lock in locks:
        try:
            lock.release()
        except RedisError:
            has_error = True
            logger.exception('Error releasing an event lock')

    if has_error:
        raise LockTimeoutException()

