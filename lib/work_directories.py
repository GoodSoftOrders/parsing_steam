"""Работа с директориями"""
import os
import shutil

from lib.work_path import get_path

directories = {
    0: {
        'path': get_path('result', '0_10$'),
        'min': 0,
        'max': 10,
    },
    50: {
        'path': get_path("{}{}{}", 'result', '50_100$'),
        'min': 50,
        'max': 100,
    },

    100: {
        'path': get_path("{}{}{}", 'result', '100$'),
        'min': 100,
    },
    'private': get_path("{}{}{}", 'result', 'private'),
    'no_inventory': get_path("{}{}{}", 'result', 'no_inventory')

}


def get_login_pass_in_file(
        path_steam_directory_file_check: str
):
    with open(path_steam_directory_file_check, 'r') as f:
        readlines = f.readlines()

    return readlines[0]


def create_file(
        path_steam_directory: str,
        path_steam_directory_file_check: str,
        profile_id: str,
        data_items: dict

):
    text = f"{get_login_pass_in_file(path_steam_directory_file_check)}\n\n"
    for name_app, items in data_items.items():

        row_text = f"*{name_app}*"
        amount_inventory = 0
        for item_name, item_price in items.items():  # цена указана в usd

            row_text += f"\n{item_name} - {item_price:.2f} USD"
            amount_inventory += item_price

        text += f'\n{row_text}\n\n'
        text += f'СТОИМОСТЬ ВСЕГО ИНВЕНТАРЯ {amount_inventory} USD\n'
        text += "——————————\n\n"

    path_to_file = get_path("{}{}{}", path_steam_directory, f"{profile_id}.txt")

    with open(path_to_file, 'w', encoding='cp1252') as f:
        f.write(text)

    print('файл с информацией о стоимости инвентаря сохранен... ')


def move_directory(
        path_steam_directory: str,
        path_steam_directory_file_check: str,
        profile_id: str,
        data_items: dict,
):
    create_file(path_steam_directory, path_steam_directory_file_check, profile_id, data_items)

    amount_inventory_all = 0
    for name, items in data_items.items():

        for item_name, item_price in items.items():
            amount_inventory_all += item_price

        directory_name = path_steam_directory.split(os.sep)[-1]

        if 'CSGO' == name:
            if len(items) > 0:
                path_steam_directory_copy = get_path("{}{}{}{}", 'result', 'Medals', directory_name.strip())
                print(f"копируем папку {path_steam_directory} в {path_steam_directory_copy}")
                try:
                    shutil.copytree(path_steam_directory, path_steam_directory_copy)
                except FileExistsError:
                    print(f"Эта папка уже была cкопирована: {path_steam_directory}")

    for amount, directory in directories.items():

        if type(amount) is not int:
            continue

        if directory.get('min') <= amount_inventory_all <= directory.get('max') or directory.get(
                'min') <= amount_inventory_all:
            shutil.move(path_steam_directory, directory.get('path'))
            print(f"Папка {path_steam_directory} была перемещена в {directory.get('path')}")
            break


def move_directory_not_found_and_private(
        path_steam_directory: str,
        error_type: str
):
    path = directories.get(error_type)

    shutil.move(path_steam_directory, path)
    print(f"Папка перемещена {path_steam_directory} в {path}")
