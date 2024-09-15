# event_decorators.py

from functools import wraps
from typing import Callable, Any


def event_handler(event_name: str) -> Callable:
    """
    事件處理裝飾器，用於註冊事件並自動注入 RecordingSys

    參數：
    - event_name: 事件名稱
    """

    def decorator(func: Callable) -> Callable:
        func._event_name = event_name

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator
