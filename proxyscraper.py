import sys
import aiohttp
import asyncio
import random
import os
import socket
import time
import re
from typing import List, Union
from colorama import Fore, Style, init
init()

class ProxyChecker:
    def __init__(self):
        self.client_timeout: int = 5
        self.endpoint: str = "http://ip-api.com/json/?fields=8217"
        self.country_list_usa: List[str] = ["United States"]
        self.country_list_eu: List[str] = [
    "Albania", "Andorra", "Austria", "Belarus", "Belgium",
    "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
    "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
    "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
    "North Macedonia", "Norway", "Poland", "Portugal", "Romania",
    "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", 
    "Spain", "Sweden", "Switzerland", "Ukraine"
]
        self.proxy_scraping_list_path: str = "proxysources.txt"
        self.scraped_proxies: List[str] = []
        self.proxy_regex: str = r"\d+\.\d+\.\d+\.\d+:\d+"
        self.semaphore: asyncio.Semaphore = None

    def save_proxy(self, proxy: str) -> None:
        with open("workingproxies.txt", "a+") as proxy_file:
            proxy_file.write(proxy + "\n")

    def clear_proxy(self) -> None:
        with open("workingproxies.txt", "w+") as proxy_file:
            pass

    async def proxy_scraper(self) -> None:
        proxy_sources: List[str] = []
        with open(self.proxy_scraping_list_path, "r") as source_file:
            proxy_sources.extend(source_file.read().splitlines())

        proxy_sources = sorted(set(proxy_sources))

        async def fetch_proxy(source_link: str) -> None:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
            ) as session:
                try:
                    async with session.get(
                        source_link,
                        headers={
                            "User-Agent": self.generate_user_agent()
                        },
                        timeout=self.client_timeout,
                    ) as response:
                        proxies = re.findall(self.proxy_regex, await response.text())
                        self.scraped_proxies.extend(proxies)
                except Exception as error:
                    self.handle_error(source_link, error)

        await asyncio.gather(*[fetch_proxy(source_link) for source_link in proxy_sources])

    def generate_user_agent(self) -> str:
        return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/{random.randint(503, 567)}.36 (KHTML, like Gecko) Chrome/{random.randint(104, 117)}.0.0.0 Safari/{random.randint(550,575)}.36"

    def handle_error(self, source_link: str, error: Exception) -> None:
        print(Fore.LIGHTRED_EX + f"[!]{Style.RESET_ALL} Failed to process '{Fore.LIGHTYELLOW_EX}{source_link}{Style.RESET_ALL}', Error: {Fore.LIGHTRED_EX}{error}{Style.RESET_ALL}")

    async def proxy_checker(self, region: Union[str, List[str]], proxy: str) -> None:
        country_check = region != "All"
        ip_address = proxy.split(":")[0]
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
        ) as session:
            try:
                starting_time = time.monotonic()
                async with session.get(
                    self.endpoint,
                    proxy=f"http://{proxy}",
                    timeout=self.client_timeout,
                ) as response:
                    data = await response.json()
                    ending_time = time.monotonic()
                    if not country_check or data["country"] in region:
                        self.print_working_proxy(proxy, data, starting_time, ending_time)
                        self.save_proxy(proxy)

            except Exception:
                pass

    def print_working_proxy(self, proxy: str, data: dict, starting_time: float, ending_time: float) -> None:
        print(
            Fore.LIGHTGREEN_EX + f"[+]{Style.RESET_ALL} Working Proxy:{Fore.LIGHTYELLOW_EX} {proxy}{Style.RESET_ALL} | Location: {Fore.LIGHTYELLOW_EX}{data['country']}{Style.RESET_ALL} | Speed: {Fore.LIGHTYELLOW_EX}{abs(starting_time - ending_time):.2f}s{Style.RESET_ALL}"
        )

    async def run(self, region: Union[str, List[str]], threads: int) -> None:
        await self.proxy_scraper()
        self.scraped_proxies = sorted(set(self.scraped_proxies))
        print(Fore.LIGHTYELLOW_EX + f"[!]{Style.RESET_ALL} Grabbed {Fore.LIGHTYELLOW_EX}{len(self.scraped_proxies)}{Style.RESET_ALL} proxies.")
        self.clear_proxy()

        region = self.get_normalized_region(region)
        self.semaphore = asyncio.Semaphore(threads)

        async def check_proxy(proxy: str) -> None:
            async with self.semaphore:
                await self.proxy_checker(region, proxy)

        await asyncio.gather(*[check_proxy(proxy) for proxy in self.scraped_proxies])

    def get_normalized_region(self, region: Union[str, List[str]]) -> Union[str, List[str]]:
        if region == "US":
            return self.country_list_usa
        elif region == "EU":
            return self.country_list_eu
        elif region == "ALL":
            return "All"
        else:
            self.exit_with_error(Fore.LIGHTRED_EX + f"[!]{Style.RESET_ALL} Invalid region choice exiting...")

    def exit_with_error(self, message: str) -> None:
        print(Fore.LIGHTYELLOW_EX + f"[!]{Style.RESET_ALL} {message}")
        sys.exit(0)

async def main(region: Union[str, List[str]], threads: int) -> None:
    proxy_checker = ProxyChecker()
    await proxy_checker.run(region, threads)

if __name__ == "__main__":
    if "nt" in os.name:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    threads = int(input(Fore.LIGHTYELLOW_EX + f"[?]{Style.RESET_ALL} Enter the number of threads: "))
    region = input(Fore.LIGHTYELLOW_EX + f"[?]{Style.RESET_ALL} Enter region (US/EU/ALL): ").upper()
    print(Fore.LIGHTRED_EX + f"[!]{Style.RESET_ALL} Starting...")
    asyncio.run(main(region, threads))
