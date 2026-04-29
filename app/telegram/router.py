from aiogram import Dispatcher

from app.telegram.handlers.menu import router as menu_router
from app.telegram.handlers.requests import router as requests_router


def setup_routers(dispatcher: Dispatcher) -> None:
    
    dispatcher.include_router(menu_router)
    dispatcher.include_router(requests_router)
