# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


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

        from .utils import Utils
        return Utils.get_sha256_hash(val)

    return _decorator
