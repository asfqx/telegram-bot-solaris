from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from loguru import logger

from app.bitrix import BitrixAPIError, BitrixClient
from app.catalog import RENT_SPACES, RENT_STAY
from app.services.helper import HandlersHelper
from app.services.lead_requests import LeadRequestService
from app.telegram.const import CORPORATE_GROUP_LABELS
from app.telegram.keyboards import (
    comment_skip_keyboard,
    main_menu_keyboard,
    phone_keyboard,
    request_confirmation_keyboard,
    request_people_count_keyboard,
)
from app.telegram.states import RequestLeadState


router = Router()
RENT_TARGETS = {item.key for item in (*RENT_STAY, *RENT_SPACES)}


async def request_age_or_comment(message: Message, state: FSMContext) -> None:
    target_raw = (await state.get_data()).get("target")
    target = str(target_raw) if isinstance(target_raw, str) else ""

    if target in RENT_TARGETS:
        await state.update_data(age=None)
        await state.set_state(RequestLeadState.waiting_for_comment)
        await message.answer(
            "Если у вас есть пожелания, напишите их следующим сообщением. Если комментарий не нужен, нажмите «Пропустить».",
            reply_markup=comment_skip_keyboard(),
        )
        return

    await state.set_state(RequestLeadState.waiting_for_age)
    await message.answer("Подскажите, пожалуйста, возраст участников. Если возраст разный, можно написать диапазон.")


@router.callback_query(F.data == "request:skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    current_state = await state.get_state()
    if current_state != RequestLeadState.waiting_for_comment.state:
        await callback.answer()
        return

    await state.update_data(comment=None)
    await state.set_state(RequestLeadState.waiting_for_booking_datetime)
    await message.answer("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")
    await callback.answer("Комментарий пропущен")


@router.callback_query(F.data == "request:submit")
async def confirm_request_submission(callback: CallbackQuery, state: FSMContext, bitrix: BitrixClient) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    current_state = await state.get_state()
    if current_state != RequestLeadState.waiting_for_confirmation.state:
        await callback.answer()
        return

    data = await state.get_data()
    phone = data.get("phone")
    if not isinstance(phone, str) or not phone:
        await callback.answer("Не удалось найти ваш телефон для отправки", show_alert=True)
        return

    submission = await LeadRequestService.build_submission(message=message, state=state, phone=phone)
    logger.info(
        "Submitting lead: target={target}, title={title}, name={name}, phone={phone}, people_count={people_count}, age={age}, booking_datetime={booking_datetime}, additional_services={additional_services}, selection_path={selection_path}, comment={comment}, event_details={event_details}",
        target=submission.target,
        title=submission.title,
        name=submission.name,
        phone=submission.phone,
        people_count=submission.people_count,
        age=submission.age,
        booking_datetime=submission.booking_datetime,
        additional_services=", ".join(submission.selected_additional_services),
        selection_path=" -> ".join(submission.selection_path),
        comment=submission.comment,
        event_details=submission.event_details,
    )
    logger.info("Lead comments payload:\n{comments}", comments=submission.comments)

    try:
        await LeadRequestService.submit_lead_request(bitrix=bitrix, submission=submission)
    except BitrixAPIError as exc:
        logger.exception("Bitrix API error")
        await message.answer(
            f"Не получилось отправить вашу заявку в Bitrix24: {exc}",
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.answer()
        return
    except Exception:
        logger.exception("Unexpected error during lead submission")
        await message.answer(
            "Не получилось отправить вашу заявку. Попробуйте, пожалуйста, еще раз чуть позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.answer()
        return

    await state.clear()
    await callback.answer("Ваша заявка отправлена")
    await message.answer(
        "Спасибо, ваша заявка отправлена. Мы свяжемся с вами после обработки.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "Выберите, что вас интересует, а я помогу сориентироваться и оставить заявку.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "request:restart")
async def restart_request(callback: CallbackQuery, state: FSMContext) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    current_state = await state.get_state()
    if current_state != RequestLeadState.waiting_for_confirmation.state:
        await callback.answer()
        return

    data = await state.get_data()
    target = data.get("target")
    selection_path = [str(value) for value in data.get("selection_path", []) if isinstance(value, str)]
    corporate_group_label = data.get("corporate_group_label")
    selected_additional_services = [
        str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    if not isinstance(target, str) or not target:
        await callback.answer("Не получилось начать заполнение заново", show_alert=True)
        return

    await callback.answer("Заполняем заново")
    await HandlersHelper.start_request_flow(
        message=message,
        state=state,
        target=target,
        selection_path=selection_path,
        corporate_group_label=corporate_group_label if isinstance(corporate_group_label, str) else None,
        requester_label=LeadRequestService.telegram_user_label(callback.from_user),
        requester_id=callback.from_user.id,
        selected_additional_services=selected_additional_services,
    )


@router.callback_query(F.data.startswith("request:size:"))
async def request_people_count_selected(callback: CallbackQuery, state: FSMContext) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    current_state = await state.get_state()
    if current_state != RequestLeadState.waiting_for_people_count.state:
        await callback.answer()
        return

    group_key = data.split(":", 2)[2]
    group_label = CORPORATE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer("Не удалось определить количество гостей", show_alert=True)
        return

    await state.update_data(people_count=group_label)
    await request_age_or_comment(message, state)
    await callback.answer(f"Вы выбрали: {group_label}")


@router.callback_query(F.data.startswith("request:") & ~(F.data.startswith("request:size:")) & (F.data != "request:skip_comment") & (F.data != "request:submit") & (F.data != "request:restart"))
async def start_request(callback: CallbackQuery, state: FSMContext) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    target = data.split(":", 1)[1]
    existing_data = await state.get_data()
    selection_path = [str(value) for value in existing_data.get("selection_path", []) if isinstance(value, str)]
    corporate_group_label = existing_data.get("corporate_group_label")
    selected_additional_services = [
        str(value) for value in existing_data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    await HandlersHelper.start_request_flow(
        message=message,
        state=state,
        target=target,
        selection_path=selection_path,
        corporate_group_label=corporate_group_label if isinstance(corporate_group_label, str) else None,
        requester_label=LeadRequestService.telegram_user_label(callback.from_user),
        requester_id=callback.from_user.id,
        selected_additional_services=selected_additional_services,
    )
    await callback.answer()


@router.message(RequestLeadState.waiting_for_event_details)
async def process_event_details(message: Message, state: FSMContext) -> None:
    details = (message.text or "").strip()
    if not details:
        await message.answer("Пожалуйста, опишите ваше мероприятие одним сообщением.")
        return

    await state.update_data(event_details=details)
    await state.set_state(RequestLeadState.waiting_for_name)
    await message.answer("Подскажите, пожалуйста, как к вам обращаться?")


@router.message(RequestLeadState.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, напишите, как к вам обращаться.")
        return

    await state.update_data(name=name)

    data = await state.get_data()
    people_count = data.get("people_count")
    if isinstance(people_count, str) and people_count:
        await request_age_or_comment(message, state)
        return

    await state.set_state(RequestLeadState.waiting_for_people_count)
    await message.answer(
        "Сколько человек планируется? Выберите, пожалуйста, подходящий вариант кнопкой ниже.",
        reply_markup=request_people_count_keyboard(),
    )


@router.message(RequestLeadState.waiting_for_people_count)
async def process_people_count(message: Message) -> None:
    await message.answer(
        "Пожалуйста, выберите количество гостей кнопкой ниже.",
        reply_markup=request_people_count_keyboard(),
    )


@router.message(RequestLeadState.waiting_for_age)
async def process_age(message: Message, state: FSMContext) -> None:
    age = (message.text or "").strip()
    if not age:
        await message.answer("Пожалуйста, укажите возраст участников или возрастной диапазон.")
        return

    await state.update_data(age=age)
    await state.set_state(RequestLeadState.waiting_for_comment)
    await message.answer(
        "Если у вас есть пожелания, напишите их следующим сообщением. Если комментарий не нужен, нажмите «Пропустить».",
        reply_markup=comment_skip_keyboard(),
    )


@router.message(RequestLeadState.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    comment = (message.text or "").strip()
    if not comment:
        await message.answer("Напишите, пожалуйста, ваши пожелания сообщением или нажмите «Пропустить».")
        return

    if comment.lower() in {"пропустить", "skip", "-"}:
        await state.update_data(comment=None)
        await state.set_state(RequestLeadState.waiting_for_booking_datetime)
        await message.answer("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")
        return

    await state.update_data(comment=comment)
    await state.set_state(RequestLeadState.waiting_for_booking_datetime)
    await message.answer("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")


@router.message(RequestLeadState.waiting_for_booking_datetime)
async def process_booking_datetime(message: Message, state: FSMContext) -> None:
    booking_datetime = (message.text or "").strip()
    if not booking_datetime:
        await message.answer("Пожалуйста, напишите дату и время брони одним сообщением.")
        return

    await state.update_data(booking_datetime=booking_datetime)
    await state.set_state(RequestLeadState.waiting_for_phone)
    await message.answer(
        "Теперь отправьте, пожалуйста, ваш номер телефона. Можно нажать кнопку ниже или написать его сообщением.",
        reply_markup=phone_keyboard(),
    )


@router.message(RequestLeadState.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact is None:
        await message.answer("Не получилось получить ваш контакт. Пожалуйста, отправьте номер телефона сообщением.")
        return

    await HandlersHelper.show_preview(message, state, contact.phone_number)


@router.message(RequestLeadState.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if len(phone) < 6:
        await message.answer("Похоже, номер слишком короткий. Пожалуйста, отправьте корректный телефон.")
        return

    await HandlersHelper.show_preview(message, state, phone)


@router.message(RequestLeadState.waiting_for_confirmation)
async def process_confirmation_text(message: Message) -> None:
    await message.answer(
        "Пожалуйста, проверьте данные в предпросмотре и выберите действие кнопкой ниже.",
        reply_markup=request_confirmation_keyboard(),
    )
