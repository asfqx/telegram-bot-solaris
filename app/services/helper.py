from typing import cast

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from app.catalog import CORPORATE_INFO, ITEMS_BY_KEY, RENT_SPACE_TARGETS
from app.telegram.const import (
    ADDITIONAL_SERVICE_LABELS,
    ADDITIONAL_SERVICES_TEXT,
    CORPORATE_ACTIVITY_LABELS,
    EXTRAS_SOURCE_CONFIG,
)
from app.telegram.keyboards import (
    additional_services_keyboard,
    corporate_activities_keyboard,
    request_confirmation_keyboard,
)
from app.telegram.states import RequestLeadState

from .lead_requests import LeadRequestService


class HandlersHelper:
    @staticmethod
    def callback_message(callback: CallbackQuery) -> Message | None:
        
        message = callback.message
        
        if message is None or isinstance(message, InaccessibleMessage):
            return None
        
        return cast(Message, message)

    @staticmethod
    async def safe_edit_text(
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        
        try:
            await message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise

    @staticmethod
    async def show_preview(message: Message, state: FSMContext, phone: str) -> None:
        
        submission = await LeadRequestService.build_submission(message=message, state=state, phone=phone)
        await state.update_data(phone=phone)
        await state.set_state(RequestLeadState.waiting_for_confirmation)
        
        await message.answer(
            LeadRequestService.build_preview_text(submission),
            reply_markup=request_confirmation_keyboard(),
        )

    @staticmethod
    async def start_request_flow(
        *,
        message: Message,
        state: FSMContext,
        target: str,
        selection_path: list[str],
        corporate_group_label: str | None = None,
        requester_label: str | None = None,
        requester_id: int | None = None,
        selected_additional_services: list[str] | None = None,
        skip_additional_services_step: bool = False,
    ) -> None:
        
        await state.clear()
        await state.update_data(target=target, selection_path=selection_path)

        if requester_label:
            await state.update_data(requester_label=requester_label)

        if requester_id is not None:
            await state.update_data(requester_id=requester_id)

        if selected_additional_services:
            await state.update_data(selected_additional_services=selected_additional_services)

        if corporate_group_label:
            await state.update_data(people_count=corporate_group_label, corporate_group_label=corporate_group_label)

        if target == "event":
            if not selection_path:
                await state.update_data(selection_path=["Мероприятие"])
            await state.set_state(RequestLeadState.waiting_for_event_details)
            await message.answer(
                "Расскажите, пожалуйста, какое мероприятие вы планируете. Например: корпоратив на 30 человек, свадьба, семейный выезд или активный отдых.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if target in RENT_SPACE_TARGETS and not skip_additional_services_step:
            back_callback = f"item:{target}"
            await state.update_data(additional_services_back_callback=back_callback)
            await HandlersHelper.show_additional_services(message, state, "rent_space_request")
            return

        item_title = "Корпоратив" if target == "corporate" else ITEMS_BY_KEY[target].title
        await message.answer(
            f"Помогу вам оформить заявку на «{item_title}». Для начала напишите, как к вам обращаться.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(RequestLeadState.waiting_for_name)

    @staticmethod
    async def show_corporate_activities(message: Message, state: FSMContext) -> None:
        
        data = await state.get_data()
        group_label = data.get("corporate_group_label") if isinstance(data.get("corporate_group_label"), str) else None
        activity_keys = [str(value) for value in data.get("corporate_activities", []) if isinstance(value, str)]
        selected_services = [str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)]

        activity_labels = [CORPORATE_ACTIVITY_LABELS[key] for key in activity_keys if key in CORPORATE_ACTIVITY_LABELS]
        service_labels = [ADDITIONAL_SERVICE_LABELS[key] for key in selected_services if key in ADDITIONAL_SERVICE_LABELS]

        lines = [
            "<b>Корпоратив</b>",
            "",
            CORPORATE_INFO,
            "",
            f"Ваш размер группы: {group_label or 'пока не выбран'}",
            f"Что вам интересно: {', '.join(activity_labels) if activity_labels else 'пока ничего не выбрано'}",
            f"Дополнительные услуги: {', '.join(service_labels) if service_labels else 'не выбраны'}",
            "",
            "Вы можете выбрать несколько активностей и сразу собрать удобный запрос для менеджера.",
        ]

        await HandlersHelper.safe_edit_text(
            message,
            "\n".join(lines),
            reply_markup=corporate_activities_keyboard(activity_keys),
        )

    @staticmethod
    async def show_additional_services(message: Message, state: FSMContext, source: str) -> None:
        
        data = await state.get_data()
        selected = [str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)]

        if source == "rent_space_request":
            back_callback_raw = data.get("additional_services_back_callback")
            back_callback = back_callback_raw if isinstance(back_callback_raw, str) else "rent:spaces"
        else:
            back_callback = EXTRAS_SOURCE_CONFIG[source]["back"]

        selected_labels = [ADDITIONAL_SERVICE_LABELS[key] for key in selected if key in ADDITIONAL_SERVICE_LABELS]
        lines = [ADDITIONAL_SERVICES_TEXT]
        if selected_labels:
            lines.extend(["", f"<b>Вы добавили:</b> {', '.join(selected_labels)}"])

        await HandlersHelper.safe_edit_text(
            message,
            "\n".join(lines),
            reply_markup=additional_services_keyboard(source, back_callback, selected),
        )
