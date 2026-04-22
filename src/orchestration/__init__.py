import functools

from .chat import ChatController
from src.services import get_services


@functools.lru_cache(maxsize=1)
def get_chat_controller() -> ChatController:
    return ChatController(get_services())


__all__ = ["ChatController", "get_chat_controller"]
