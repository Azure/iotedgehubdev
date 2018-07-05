import hashlib
from functools import wraps


def suppress_all_exceptions(fallback_return=None):
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                if fallback_return:
                    return fallback_return
                else:
                    pass

        return _wrapped_func

    return _decorator


def call_once(factory_func):
    """"
    When a function is annotated by this decorator, it will be only executed once. The result will
    be cached and return for following invocations.
    """
    factory_func.executed = False
    factory_func.cached_result = None

    def _wrapped(*args, **kwargs):
        if not factory_func.executed:
            factory_func.cached_result = factory_func(*args, **kwargs)

        return factory_func.cached_result
    return _wrapped


def hash256_result(func):
    """Secure the return string of the annotated function with SHA256 algorithm. If the annotated
    function doesn't return string or return None, raise ValueError."""
    @wraps(func)
    def _decorator(*args, **kwargs):
        val = func(*args, **kwargs)
        if not val:
            raise ValueError('Return value is None')
        elif not isinstance(val, str):
            raise ValueError('Return value is not string')
        hash_object = hashlib.sha256(val.encode('utf-8'))
        return str(hash_object.hexdigest())
    return _decorator