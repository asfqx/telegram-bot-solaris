from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.catalog import (
    ACTIVITIES,
    CLUB_MAP_URL,
    CLUB_SITE_URL,
    CORPORATE_ACTIVITIES,
    CORPORATE_GROUP_SIZES,
    KARTING_FAQ,
    RENT_SPACE_GROUP_SIZES,
    RENT_STAY,
    rent_spaces_for_group,
)
from app.telegram.const import ADDITIONAL_SERVICE_OPTIONS


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Активности", callback_data="menu:activities")
    builder.button(text="Аренда", callback_data="menu:rent")
    builder.button(text="Корпоратив", callback_data="menu:corporate")
    builder.button(text="Мероприятие", callback_data="menu:event")
    builder.button(text="О нашем клубе", callback_data="menu:about")
    builder.adjust(1)
    return builder.as_markup()


def about_club_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сайт", url=CLUB_SITE_URL)],
            [InlineKeyboardButton(text="Связь с поддержкой", callback_data="about:support")],
            [InlineKeyboardButton(text="Как добраться?", callback_data="about:route")],
            [InlineKeyboardButton(text="В главное меню", callback_data="menu:root")],
        ]
    )


def about_club_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="menu:about")],
            [InlineKeyboardButton(text="В главное меню", callback_data="menu:root")],
        ]
    )


def route_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть карту", url=CLUB_MAP_URL)],
            [InlineKeyboardButton(text="Назад", callback_data="menu:about")],
            [InlineKeyboardButton(text="В главное меню", callback_data="menu:root")],
        ]
    )


def additional_services_keyboard(source: str, back_callback: str, selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    selected_set = set(selected)

    for key, label in ADDITIONAL_SERVICE_OPTIONS:
        prefix = "[x] " if key in selected_set else "[ ] "
        builder.button(text=f"{prefix}{label}", callback_data=f"extras:toggle:{source}:{key}")

    builder.button(text="Продолжить", callback_data=f"extras:done:{source}")
    builder.button(text="Назад", callback_data=back_callback)
    builder.button(text="В главное меню", callback_data="menu:root")
    builder.adjust(1)
    return builder.as_markup()


def activities_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in ACTIVITIES:
        builder.button(text=item.title, callback_data=f"item:{item.key}")
    builder.button(text="Назад", callback_data="menu:root")
    builder.adjust(1)
    return builder.as_markup()


def rent_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Где пожить", callback_data="rent:stay")
    builder.button(text="Где посидеть", callback_data="rent:spaces")
    builder.button(text="Назад", callback_data="menu:root")
    builder.adjust(1)
    return builder.as_markup()


def rent_stay_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in RENT_STAY:
        builder.button(text=item.title, callback_data=f"item:{item.key}")
    builder.button(text="Назад", callback_data="menu:rent")
    builder.adjust(1)
    return builder.as_markup()


def rent_spaces_group_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in RENT_SPACE_GROUP_SIZES:
        builder.button(text=label, callback_data=f"rent:spaces:size:{key}")
    builder.button(text="Назад", callback_data="menu:rent")
    builder.adjust(1)
    return builder.as_markup()


def rent_spaces_keyboard(group_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in rent_spaces_for_group(group_key):
        builder.button(text=item.title, callback_data=f"item:{item.key}")
    builder.button(text="К выбору количества гостей", callback_data="rent:spaces")
    builder.button(text="Назад", callback_data="menu:rent")
    builder.adjust(1)
    return builder.as_markup()


def corporate_group_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in CORPORATE_GROUP_SIZES:
        builder.button(text=label, callback_data=f"corp:size:{key}")
    builder.button(text="Банкетное меню", callback_data="corp:menu")
    builder.button(text="В главное меню", callback_data="menu:root")
    builder.adjust(1)
    return builder.as_markup()


def request_people_count_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in CORPORATE_GROUP_SIZES:
        builder.button(text=label, callback_data=f"request:size:{key}")
    builder.adjust(1)
    return builder.as_markup()


def corporate_activities_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    selected_set = set(selected)
    for key, label in CORPORATE_ACTIVITIES:
        prefix = "[x] " if key in selected_set else "[ ] "
        builder.button(text=f"{prefix}{label}", callback_data=f"corp:activity:{key}")
    builder.button(text="Банкетное меню", callback_data="corp:menu")
    builder.button(text="Дополнительные услуги", callback_data="extras:corporate")
    builder.button(text="Продолжить", callback_data="corp:done")
    builder.button(text="К размерам групп", callback_data="menu:corporate")
    builder.adjust(1)
    return builder.as_markup()


def karting_info_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, (title, _) in KARTING_FAQ.items():
        builder.button(text=title, callback_data=f"karting:info:{key}")
    builder.button(text="Записаться", callback_data="request:karting")
    builder.button(text="К активностям", callback_data="menu:activities")
    builder.adjust(1)
    return builder.as_markup()


def request_button(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", callback_data=f"request:{target}")],
            [InlineKeyboardButton(text="В главное меню", callback_data="menu:root")],
        ]
    )


def request_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить заявку", callback_data="request:submit")],
            [InlineKeyboardButton(text="Заполнить заново", callback_data="request:restart")],
            [InlineKeyboardButton(text="В главное меню", callback_data="menu:root")],
        ]
    )


def comment_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="request:skip_comment")],
        ]
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Отправьте номер телефона",
    )

