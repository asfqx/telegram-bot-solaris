import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from loguru import logger

from app.telegram.keyboards import main_menu_keyboard
from app.users import User, UserRepository
from app.constants import REMINDER_MESSAGES
from app.core import AsyncSessionLocal


class ReminderService:
    
    def __init__(
        self,
        *,
        reminder_interval: timedelta = timedelta(days=3),
        poll_interval_seconds: int = 3600,
    ) -> None:
        
        self._reminder_interval = reminder_interval
        self._poll_interval_seconds = poll_interval_seconds

    async def subscribe_chat(
        self,
        *,
        chat_id: int,
        username: str | None,
        full_name: str | None,
    ) -> None:
        
        next_reminder_at = datetime.now(timezone.utc) + self._reminder_interval

        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_chat_id(chat_id=chat_id, session=session)

            if not user:
                user = User(
                    chat_id=chat_id,
                    username=username,
                    full_name=full_name,
                    next_reminder_at=next_reminder_at,
                )
                await UserRepository.add(user=user, session=session)
            else:
                user.username = username
                user.full_name = full_name
                user.next_reminder_at = next_reminder_at

                await session.commit()

    async def unsubscribe_chat(self, chat_id: int) -> bool:
        
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_chat_id(session=session, chat_id=chat_id)
            
            if user is None:
                return False

            await UserRepository.delete(session=session, user=user)

            return True

    async def run(self, bot: Bot) -> None:
        
        logger.info("Weekly reminder loop started")
        try:
            while True:
                try:
                    await self.send_due_reminders(bot)
                except Exception:
                    logger.exception("Weekly reminder iteration failed")
                    
                await asyncio.sleep(self._poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info("Weekly reminder loop stopped")
            raise

    async def send_due_reminders(self, bot: Bot) -> None:

        async with AsyncSessionLocal() as session:
            recipients = await UserRepository.list_due(session=session, due_before=datetime.now(timezone.utc))

        for recipient in recipients:
            reminder_index = (recipient.last_reminder_index + 1) % len(REMINDER_MESSAGES)
            reminder_text = REMINDER_MESSAGES[reminder_index]

            try:
                await bot.send_message(
                    recipient.chat_id,
                    reminder_text,
                    reply_markup=main_menu_keyboard(),
                )
            except TelegramForbiddenError:
                logger.info("Removing chat {chat_id} from reminders after bot block", chat_id=recipient.chat_id)
                await self._delete_recipient(user_uuid=recipient.uuid)
                continue
            
            except TelegramBadRequest as exc:
                error_text = str(exc).lower()
                
                if "chat not found" in error_text or "user is deactivated" in error_text:
                    logger.info("Removing chat {chat_id} from reminders after Telegram error: {error}", chat_id=recipient.chat_id, error=exc)
                    await self._delete_recipient(user_uuid=recipient.uuid)
                    continue
                
                raise

            reminded_at = datetime.now(timezone.utc)
            next_reminder_at = reminded_at + self._reminder_interval

            async with AsyncSessionLocal() as session:
                user = await UserRepository.get_by_uuid(session=session, user_uuid=recipient.uuid)
                
                if not user:
                    continue

                user.last_reminder_sent_at = reminded_at
                user.next_reminder_at = next_reminder_at
                user.last_reminder_index = reminder_index
                
                await session.commit()

    async def _delete_recipient(self, *, user_uuid: UUID) -> None:
        
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_uuid(session=session, user_uuid=user_uuid)
            
            if not user:
                return

            await UserRepository.delete(session=session, user=user)
