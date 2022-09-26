import asyncio
import os
import re
import config
from lib.filter import filter_items
from lib.parsing_steam import ParserSteam, NotWorkingAccount, NoItems, NotEnoughProxy
from lib.work_directories import move_directory, move_directory_not_found_and_private
from lib.work_path import get_path


def read_directories(path) -> list[str]:
    paths = []
    for directory_name in os.listdir(path):
        paths.append(
            path + fr"{os.sep}{directory_name}"
        )

    return paths


def get_filename(path, _slash=os.sep):
    return path.split(_slash)[-1].strip()


def get_profile_link(text: str, link='https://steamcommunity.com/profiles/'):
    pattern = r"{}\d+".format(link)
    re_search = re.search(pattern, text)

    if re_search is not None:
        return re_search.group(0)

    parsed = text.split("\n")
    profile = parsed[1].replace("Link:", '').strip()

    return profile


def print_data(steam_parsing, data_items, directory_steam_account):
    pass
    # print(f"Общая сумма инвентаря: {steam_parsing.total_sum(data_items)} у директории {directory_steam_account}")


async def main():
    directories_steam_account = read_directories(get_path("{}{}", 'steam'))
    print("Начинаем работу...")
    max_directories = len(directories_steam_account)

    print(directories_steam_account)
    status_stop = False

    for n, directory_steam_account in enumerate(directories_steam_account, 1):

        if "__pacifier__" in directory_steam_account:
            continue

        directories_in_steam_account = read_directories(directory_steam_account)


        for directory_in_steam_account in directories_in_steam_account:
            if status_stop:
                break
            steam_parsing = ParserSteam(None, config.HEADERS, get_path("{}{}{}{}", "proxies", 'proxies.txt'))

            try:
                if 'check' in get_filename(directory_in_steam_account):
                    status_private = False
                    with open(directory_in_steam_account, 'r') as f:
                        data = f.read()
                    profile_link = get_profile_link(data)
                    print(f"Парсинг профиля - {profile_link} (директория - {directory_steam_account})")
                    steam_parsing.profile_link = profile_link
                    profile_id = await steam_parsing.get_profile_id()
                    data_items = {
                        name_key: {} for name_key in config.APP_IDS.keys()
                    }

                    for name, app_id in config.APP_IDS.items():
                        # print(f"Парсим товары {name}")

                        try:
                            items_by_game: list[dict] = await steam_parsing.get_items(profile_id, app_id=app_id)
                        except NotWorkingAccount:
                            print(f"нельзя посмотреть айтемы: {profile_link}")
                            status_private = True
                            move_directory_not_found_and_private(directory_steam_account, 'private')
                            break
                        except NoItems:
                            print(f"нет айтемов {profile_link} в {name}")
                            continue

                        print(f"Спарсено товаров {len(items_by_game)} в {name}")
                        items_by_game = filter_items(app_id, items_by_game)
                        if not items_by_game:
                            continue


                        for item in items_by_game:
                            try:
                                market_hash_name = item.get('market_hash_name')
                                status_tradable = item.get('tradable')
                                if not status_tradable:
                                    continue

                                item_price = await steam_parsing.get_price_item(app_id, item.get("market_hash_name"))
                                print(f"{market_hash_name} - {steam_parsing.get_price(item_price)}$")
                                await asyncio.sleep(1.6)

                            except NotEnoughProxy as e:

                                print(
                                    "К сожалению, у вас закончились прокси. Попробуйте чуть позже. все использованные прокси лежат в ./proxies/uses_proxies.txt"
                                )
                                # print_data(steam_parsing, data_items, directory_steam_account)
                                return

                            data_items[name].update(
                                {
                                    item.get("market_hash_name"): steam_parsing.get_price(item_price)
                                }
                            )  # {'csgo': [{name: price},], 'dota': [{name: price},]}

                    if status_private:
                        break
                    collection_items = []
                    for name_app, _items in data_items.items():
                        collection_items.extend(_items)

                    if not collection_items:
                        print(f"Нет айтемов у аккаунта {directory_steam_account}")
                        move_directory_not_found_and_private(directory_steam_account, 'no_inventory')
                        continue

                    if data_items:
                        print(f"Переносим папку {directory_steam_account}")
                        move_directory(path_steam_directory=directory_steam_account,
                                       path_steam_directory_file_check=directory_in_steam_account,
                                       profile_id=profile_id,
                                       data_items=data_items)
            finally:
                await steam_parsing.session.close()



if __name__ == "__main__":
    asyncio.run(main())
