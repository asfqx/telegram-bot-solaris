from typing import Any, TYPE_CHECKING

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.catalog import (
    CORPORATE_CATERING_INFO,
    CORPORATE_INFO,
    CORPORATE_MENU_FILE_PATH,
    EVENT_INFO,
    ITEMS_BY_KEY,
    KARTING_FAQ,
    ROUTE_TEXT,
    SUPPORT_PHONE,
)

from app.services.helper import HandlersHelper
from app.telegram.const import (
    ADDITIONAL_SERVICE_LABELS,
    CORPORATE_ACTIVITY_LABELS,
    CORPORATE_GROUP_LABELS,
    EXTRAS_SOURCE_CONFIG,
    RENT_SPACE_GROUP_LABELS,
)
from app.telegram.keyboards import (
    about_club_back_keyboard,
    about_club_keyboard,
    activities_keyboard,
    corporate_group_keyboard,
    karting_info_keyboard,
    main_menu_keyboard,
    rent_keyboard,
    rent_spaces_group_keyboard,
    rent_spaces_keyboard,
    rent_stay_keyboard,
    request_button,
    route_keyboard,
)

if TYPE_CHECKING:
    from app.services.reminder import ReminderService


router = Router()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, weekly_reminder: "ReminderService") -> None:
    
    await state.clear()

    if message.chat.type == ChatType.PRIVATE:
        await weekly_reminder.subscribe_chat(
            chat_id=message.chat.id,
            username=message.from_user.username if message.from_user is not None else None,
            full_name=message.from_user.full_name if message.from_user is not None else None,
        )

    await message.answer(
        "Здравствуйте! Выберите, что вас интересует, а я помогу сориентироваться и оставить заявку.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("stop"))
async def command_stop(message: Message, state: FSMContext, weekly_reminder: "ReminderService") -> None:
    
    await state.clear()

    if message.chat.type == ChatType.PRIVATE:
        await weekly_reminder.unsubscribe_chat(message.chat.id)

    await message.answer(
        "Хорошо, больше не буду вас беспокоить 😞 Если захотите вернуться, просто отправьте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(F.data == "menu:root")
async def menu_root(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await state.clear()
    await HandlersHelper.safe_edit_text(message, "Выберите, что вас интересует:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def menu_about(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(
        message,
        "<b>О нашем клубе</b>\n\nВыберите, что хотите узнать:",
        reply_markup=about_club_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "about:support")
async def about_support(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Связь с поддержкой</b>\n\nЕсли вам удобнее связаться напрямую, позвоните по номеру: {SUPPORT_PHONE}",
        reply_markup=about_club_back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "about:route")
async def about_route(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Как добраться</b>\n\n{ROUTE_TEXT}",
        reply_markup=route_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:activities")
async def menu_activities(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(
        message,
        "Выберите активность, которая вам интересна, и я покажу основную информацию.",
        reply_markup=activities_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:rent")
async def menu_rent(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(
        message,
        "Выберите, что вам нужно: проживание или площадка для отдыха.",
        reply_markup=rent_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "rent:stay")
async def menu_rent_stay(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.safe_edit_text(message, "Выберите вариант проживания:", reply_markup=rent_stay_keyboard())
    await callback.answer()


@router.callback_query(F.data == "rent:spaces")
async def menu_rent_spaces(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    data = await state.get_data()
    corporate_group_label = data.get("corporate_group_label") if isinstance(data.get("corporate_group_label"), str) else None
    corporate_activities = [str(value) for value in data.get("corporate_activities", []) if isinstance(value, str)]
    requester_label = data.get("requester_label") if isinstance(data.get("requester_label"), str) else None
    requester_id = data.get("requester_id") if isinstance(data.get("requester_id"), int) else None

    await state.clear()
    
    restore_payload: dict[str, Any] = {}
    
    if corporate_group_label:
        restore_payload["corporate_group_label"] = corporate_group_label
        
    if corporate_activities:
        restore_payload["corporate_activities"] = corporate_activities
        
    if requester_label:
        restore_payload["requester_label"] = requester_label
        
    if requester_id is not None:
        restore_payload["requester_id"] = requester_id
        
    if restore_payload:
        await state.update_data(**restore_payload)

    await HandlersHelper.safe_edit_text(
        message,
        "Сколько человек планируется? Выберите диапазон, и я покажу подходящие площадки.",
        reply_markup=rent_spaces_group_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rent:spaces:size:"))
async def rent_spaces_group_selected(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    group_key = data.split(":", 3)[3]
    group_label = RENT_SPACE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer("Не удалось определить количество гостей", show_alert=True)
        return

    await state.update_data(rent_space_group_key=group_key, rent_space_group_label=group_label)
    await HandlersHelper.safe_edit_text(
        message,
        f"Подходящие площадки для группы {group_label}:",
        reply_markup=rent_spaces_keyboard(group_key),
    )
    await callback.answer()


@router.callback_query(F.data == "extras:corporate")
async def extras_corporate(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await HandlersHelper.show_additional_services(message, state, "corporate")
    await callback.answer()


@router.callback_query(F.data.startswith("extras:toggle:"))
async def extras_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    _, _, source, service_key = data.split(":", 3)
    valid_sources = set(EXTRAS_SOURCE_CONFIG) | {"rent_space_request"}
    if source not in valid_sources or service_key not in ADDITIONAL_SERVICE_LABELS:
        await callback.answer("Не удалось определить услугу", show_alert=True)
        return

    state_data = await state.get_data()
    selected = [str(value) for value in state_data.get("selected_additional_services", []) if isinstance(value, str)]

    if service_key in selected:
        selected = [value for value in selected if value != service_key]
    else:
        selected.append(service_key)

    await state.update_data(selected_additional_services=selected)
    await HandlersHelper.show_additional_services(message, state, source)
    await callback.answer()


@router.callback_query(F.data.startswith("extras:done:"))
async def extras_done(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    source = data.split(":", 2)[2]
    if source == "rent_space_request":
        state_data = await state.get_data()
        target = state_data.get("target")
        selection_path = [str(value) for value in state_data.get("selection_path", []) if isinstance(value, str)]
        requester_label = state_data.get("requester_label") if isinstance(state_data.get("requester_label"), str) else None
        requester_id = state_data.get("requester_id") if isinstance(state_data.get("requester_id"), int) else None
        selected_additional_services = [
            str(value) for value in state_data.get("selected_additional_services", []) if isinstance(value, str)
        ]

        if not isinstance(target, str) or not target:
            await callback.answer("Не получилось продолжить оформление", show_alert=True)
            return

        await HandlersHelper.start_request_flow(
            message=message,
            state=state,
            target=target,
            selection_path=selection_path,
            requester_label=requester_label,
            requester_id=requester_id,
            selected_additional_services=selected_additional_services,
            skip_additional_services_step=True,
        )
        await callback.answer("Ваш выбор сохранен")
        return

    if source not in EXTRAS_SOURCE_CONFIG:
        await callback.answer()
        return

    await HandlersHelper.show_corporate_activities(message, state)
    await callback.answer("Ваш выбор сохранен")


@router.callback_query(F.data == "menu:corporate")
async def menu_corporate(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    existing_data = await state.get_data()
    selected_additional_services = [
        str(value) for value in existing_data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    await state.update_data(
        corporate_group_key=None,
        corporate_group_label=None,
        corporate_activities=[],
        selection_path=["Корпоратив"],
        selected_additional_services=selected_additional_services,
    )
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Корпоратив</b>\n\n{CORPORATE_INFO}\n\nВыберите примерный размер вашей группы:",
        reply_markup=corporate_group_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "corp:menu")
async def corporate_menu_file(callback: CallbackQuery) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await message.answer(CORPORATE_CATERING_INFO)

    if CORPORATE_MENU_FILE_PATH.is_file():
        await message.answer_document(
            FSInputFile(str(CORPORATE_MENU_FILE_PATH)),
            caption="Банкетное меню в PDF-файле.",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("corp:size:"))
async def corporate_group_selected(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    group_key = data.split(":", 2)[2]
    group_label = CORPORATE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer("Не удалось определить размер группы", show_alert=True)
        return

    await state.update_data(
        corporate_group_key=group_key,
        corporate_group_label=group_label,
        corporate_activities=[],
        selection_path=["Корпоратив", group_label],
    )
    await HandlersHelper.show_corporate_activities(message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("corp:activity:"))
async def corporate_activity_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    activity_key = data.split(":", 2)[2]
    if activity_key not in CORPORATE_ACTIVITY_LABELS:
        await callback.answer("Не удалось определить активность", show_alert=True)
        return

    raw_selected = (await state.get_data()).get("corporate_activities", [])
    selected = [str(value) for value in raw_selected if isinstance(value, str)]

    if activity_key in selected:
        selected = [value for value in selected if value != activity_key]
    else:
        selected.append(activity_key)

    await state.update_data(corporate_activities=selected)
    await HandlersHelper.show_corporate_activities(message, state)
    await callback.answer()


@router.callback_query(F.data == "corp:done")
async def corporate_done(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    data = await state.get_data()
    group_label = data.get("corporate_group_label") if isinstance(data.get("corporate_group_label"), str) else None
    activity_keys = [str(value) for value in data.get("corporate_activities", []) if isinstance(value, str)]
    selected_services = [str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)]

    if group_label is None:
        await callback.answer("Сначала выберите размер группы", show_alert=True)
        return

    activity_labels = [CORPORATE_ACTIVITY_LABELS[key] for key in activity_keys if key in CORPORATE_ACTIVITY_LABELS]
    service_labels = [ADDITIONAL_SERVICE_LABELS[key] for key in selected_services if key in ADDITIONAL_SERVICE_LABELS]
    selection_path = ["Корпоратив", group_label]
    selection_path.extend(activity_labels or ["Активности не выбраны"])
    await state.update_data(selection_path=selection_path)

    await HandlersHelper.safe_edit_text(
        message,
        "<b>Корпоратив</b>\n\n"
        f"Размер вашей группы: {group_label}\n"
        f"Что вам интересно: {', '.join(activity_labels) if activity_labels else 'пока не выбрано'}\n"
        f"Дополнительные услуги: {', '.join(service_labels) if service_labels else 'не выбраны'}\n\n"
        "Если все верно, отправьте заявку, и мы свяжемся с вами с готовым предложением.",
        reply_markup=request_button("corporate"),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:event")
async def menu_event(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    if message is None:
        await callback.answer()
        return

    await state.update_data(selection_path=["Мероприятие"])
    await HandlersHelper.safe_edit_text(message, EVENT_INFO, reply_markup=request_button("event"))
    await callback.answer()


@router.callback_query(F.data.startswith("karting:info:"))
async def show_karting_info(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    info_key = data.split(":", 2)[2]
    faq_item = KARTING_FAQ.get(info_key)
    if faq_item is None:
        await callback.answer("Не удалось открыть раздел", show_alert=True)
        return

    title, answer = faq_item
    await state.update_data(selection_path=["Развлечения", "Картинг", title])
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Картинг</b>\n\n<b>{title}</b>\n{answer}",
        reply_markup=karting_info_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("item:"))
async def show_item(callback: CallbackQuery, state: FSMContext) -> None:
    
    message = HandlersHelper.callback_message(callback)
    data = callback.data
    if message is None or data is None:
        await callback.answer()
        return

    item_key = data.split(":", 1)[1]
    item = ITEMS_BY_KEY[item_key]
    state_data = await state.get_data()
    rent_space_group_label = (
        state_data.get("rent_space_group_label")
        if isinstance(state_data.get("rent_space_group_label"), str)
        else None
    )

    if item.key == "karting":
        await state.update_data(selection_path=[item.category_label, item.title])
        await HandlersHelper.safe_edit_text(
            message,
            f"<b>{item.title}</b>\n\n{item.description}\n\nВыберите, что именно хотите узнать:",
            reply_markup=karting_info_keyboard(),
        )
        await callback.answer()
        return

    selection_path = [item.category_label, item.title]
    if item.category_label == "Аренда / Где посидеть" and rent_space_group_label:
        selection_path = [item.category_label, rent_space_group_label, item.title]

    await state.update_data(selection_path=selection_path, selected_additional_services=[])
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>{item.title}</b>\n\n{item.description}",
        reply_markup=request_button(item.key),
    )
    await callback.answer()
