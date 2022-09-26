import asyncio
import re
import typing

from aiohttp import hdrs
from lxml import etree

import aiohttp
import aiohttp_socks
from bs4 import BeautifulSoup
from requests.exceptions import ProxyError

import config
from lib.work_path import get_path


class NotWorkingAccount(Exception):
    pass


class NoItems(Exception):
    pass


class UseProxy(Exception):
    pass


class NotEnoughProxy(Exception):
    pass


class Proxy:
    def __init__(self, ip=None, port=None,
                 login=None, password=None
                 ):
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password

    @staticmethod
    def get_all(data: str) -> typing.List['Proxy']:
        proxies = data.strip().split('\n')
        proxies_object = []
        for proxy in proxies:
            parsed_proxy = proxy.split(":")
            proxies_object.append(
                Proxy(
                    ip=parsed_proxy[0],
                    port=parsed_proxy[1],
                    login=parsed_proxy[2],
                    password=parsed_proxy[3]
                )
            )
        if not proxies_object:
            raise NotEnoughProxy
        return proxies_object


def clear_data_in_file(path, data):

    with open(path, 'r') as f_read:
        _data = f_read.read()

    _data = _data.replace(data, "").strip()

    with open(path, 'w') as f_write:
        f_write.write(_data)



class ParserSteam:
    def __init__(self, profile: str,
                 headers: dict,
                 proxies_path_to_file: str
                 ):
        self.profile_link = profile
        self.proxies_path_to_file = proxies_path_to_file

        self.use_proxy = None
        self.session = aiohttp.ClientSession(connector=self.create_connector())
        self.headers = headers

    @staticmethod
    def base_create_connector(proxy: Proxy):
        proxy_url = "socks5://{login}:{password}@{ip}:{port}".format(
            login=proxy.login, password=proxy.password,
            ip=proxy.ip, port=proxy.port
        )
        connector = aiohttp_socks.ProxyConnector().from_url(proxy_url)
        return connector

    async def request_session(
            self,
            method,
            url,
            **params
    ) -> '_RequestContextManager':

        error_status = False
        while True:
            try:
                response = await self.session.request(method, url=url, **params)
                return response
            except ProxyError:
                error_status = True

            except Exception as e:
                error = e
                error_status = True

            if error_status:
                ip = f"{self.use_proxy.ip}:{self.use_proxy.port}:{self.use_proxy.login}:{self.use_proxy.password}"
                clear_data_in_file(self.proxies_path_to_file, ip)

                path_to_file = get_path("{}{}{}", 'proxies', 'failed_proxies.txt')

                with open(path_to_file, 'a+') as f:
                    f.write(
                        f"{ip}\n"
                    )
                await self.replacement_session()







    def create_connector(self) -> aiohttp_socks.ProxyConnector:
        with open(self.proxies_path_to_file, 'r') as f:
            data = f.read()

        proxies = Proxy.get_all(data)
        proxy = proxies[0]
        connector = self.base_create_connector(proxy)

        self.use_proxy = proxy

        return connector

    async def replacement_session(self):

        with open(self.proxies_path_to_file, 'r') as f:
            data = f.read().strip()
        proxies = Proxy.get_all(data)
        for proxy in proxies:
            if proxy.ip == self.use_proxy.ip:
                continue

            ip = f"{self.use_proxy.ip}:{self.use_proxy.port}:{self.use_proxy.login}:{self.use_proxy.password}"
            data = data.replace(ip, "")
            with open(self.proxies_path_to_file, 'w') as f_proxies:
                f_proxies.write(data.strip())

            path_to_file = get_path("{}{}{}", 'proxies', 'used_proxies.txt')
            with open(path_to_file, 'a+') as f_used:
                f_used.write(f"{ip}\n")

            self.use_proxy = proxy
            print(f"идет замена прокси {proxy.ip}:{proxy.port}")

            connector = self.base_create_connector(proxy)
            await self.session.close()
            self.session = aiohttp.ClientSession(connector=connector)
            break

    @staticmethod
    def total_sum(data: dict):

        item_prices = [item_price for _, item_price in data.items()]

        return round(sum(item_prices), 2)

    @staticmethod
    def get_price(text):
        symbols = ['$']
        formatted_text = text
        if text is None:
            return round(0,2)
        for symbol in symbols:
            formatted_text = formatted_text.replace(symbol, "")

        return round(float(formatted_text.strip()), 2)

    async def get_profile_id(self):

        search_profile_id = re.search("\d+", self.profile_link)
        if search_profile_id:
            return search_profile_id.group(0)

        response = await self.request_session(hdrs.METH_GET, self.profile_link, headers=self.headers)
        content = await response.text()
        pattern = r"UserYou.SetSteamId\(.+?\)"
        searched_steam_object = re.search(pattern, content).group(0)
        searched_steam_id = re.search(r"\d+", searched_steam_object).group(0)

        return searched_steam_id



    async def get_items(self, profile_id: str,
                        app_id: int,
                        count=5000) -> list[dict]:
        link = "https://steamcommunity.com/inventory/{profile_id}/{app_id}/2?l=english&count={count}".format(
            profile_id=profile_id,
            app_id=app_id,
            count=count
        )

        response = await self.request_session(hdrs.METH_GET, link, headers=self.headers)
        data = await response.json()

        if data is None:
            raise NotWorkingAccount

        total_inventory_count = data.get("total_inventory_count")
        if total_inventory_count <= 0:
            raise NoItems

        return data.get("descriptions")

    async def get_price_item(self,
                             app_id: int,
                             item_name_hash: str):
        for i in range(0, 3):
            link = config.LINK_MARKET.format(
                app_id=app_id, market_hash_name=item_name_hash
            )
            response = await self.request_session(hdrs.METH_GET, link, headers=self.headers)
            data = await response.json()

            if data is None:
                await asyncio.sleep(0.6)
                await self.replacement_session()
                continue

            if not data.get("success"):
                return "$0"

            return data.get("lowest_price")
