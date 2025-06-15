from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from database import req

def admin_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Розыгрыши",callback_data="admin_raffles")],
        # [InlineKeyboardButton(text="Персонал",callback_data="personal")],
        # [InlineKeyboardButton(text="Рассылка", callback_data="mailing")]
    ])



def admin_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ])


def available_events(events: List[req.Event]):
    kb = []
    
    for event in events:
        kb.append([InlineKeyboardButton(text=event.name, callback_data=f"adminShow_{event.id}")])

    kb.append([InlineKeyboardButton(text="Назад", callback_data="admin_back")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def confirm_winners():
    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text='✅ Да', callback_data=f'confirmWinners'),
        InlineKeyboardButton(text='❌ Нет', callback_data=f'declineWinners'),
        InlineKeyboardButton(text='Назад', callback_data=f'admin_back'),
    ).as_markup()




def admin_start_promotion_button(next_promotion, len_promotion, status):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"1/{len_promotion}", callback_data="q"), 
            InlineKeyboardButton(text="➡️", callback_data=f"Admnavigation_forward_{next_promotion}_{status}")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        
        ]
    ])

def admin_middle_promotion_button(next_promotion, len_promotion, back_promotion, current_promotion_number, status):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"Admnavigation_back_{back_promotion}_{status}"),
            InlineKeyboardButton(text=f"{current_promotion_number}/{len_promotion}", callback_data="q"),
            InlineKeyboardButton(text="➡️", callback_data=f"Admnavigation_forward_{next_promotion}_{status}")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        ]
    ])

def admin_end_promotion_button(len_promotion, back_promotion, status):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"Admnavigation_back_{back_promotion}_{status}"), 
            InlineKeyboardButton(text=f"{len_promotion}/{len_promotion}", callback_data="q")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        ]
    ])






def start_promotion_button_a(next_promotion, len_promotion):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data=f"promotion_edit_{next_promotion-1}")],
        [InlineKeyboardButton(text=f"1/{len_promotion}", callback_data="q"), InlineKeyboardButton(text="➡️", callback_data=f"a_navigation_forward_{next_promotion}")],
     [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        
        ]
     ])

def middle_promotion_button_a(next_promotion, len_promotion, back_promotion, current_promotion_number):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data=f"promotion_edit_{current_promotion_number}")],
        [InlineKeyboardButton(text="⬅️", callback_data=f"a_navigation_back_{back_promotion}"), InlineKeyboardButton(text=f"{current_promotion_number}/{len_promotion}", callback_data="q"), InlineKeyboardButton(text="➡️", callback_data=f"a_navigation_forward_{next_promotion}")],
    [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        
        ]
    ])

def end_promotion_button_a(len_promotion, back_promotion):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data=f"promotion_edit_{back_promotion+1}")],
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"a_navigation_back_{back_promotion}"),
            InlineKeyboardButton(text=f"{len_promotion}/{len_promotion}", callback_data="q")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"admin_back")
        
        ]
    ])

