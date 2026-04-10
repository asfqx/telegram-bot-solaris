import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.bitrix import BitrixClient
from app.core.db import engine
from app.core.settings import settings
from app.services.reminder import ReminderService
from app.telegram import setup_routers


async def main() -> None:
    
    logger.info(
        "Starting Telegram bot with Bitrix source_id={source_id}, lead_status_id={lead_status_id}, webhook={webhook}",
        source_id=settings.bitrix_source_id,
        lead_status_id=settings.bitrix_lead_status_id,
        webhook=settings.bitrix_webhook_url,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dispatcher = Dispatcher(storage=MemoryStorage())
    setup_routers(dispatcher)
    weekly_reminder = ReminderService()

    async with BitrixClient(
        webhook_url=settings.bitrix_webhook_url,
        source_id=settings.bitrix_source_id,
        assigned_by_id=settings.bitrix_assigned_by_id,
        lead_status_id=settings.bitrix_lead_status_id,
    ) as bitrix:
        
        dispatcher["bitrix"] = bitrix
        dispatcher["weekly_reminder"] = weekly_reminder
        reminder_task = asyncio.create_task(weekly_reminder.run(bot))

        try:
            await dispatcher.start_polling(bot)
        finally:
            reminder_task.cancel()
            await asyncio.gather(reminder_task, return_exceptions=True)
            await bot.session.close()
            await engine.dispose()


if __name__ == "__main__":
    
    asyncio.run(main())
