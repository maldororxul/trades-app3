import discord
import time
import asyncio
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from webdriver_manager.chrome import ChromeDriverManager    # pip install webdriver-manager
from bs4 import BeautifulSoup as bs
import requests
import re


TOKEN = 'NzYyOTc3NDM2OTQxMTU2MzUz.X3xAHA.nRyakxJWm4qJ_aST65bn5TvANB8'
CHANNEL_ID = 711192122753024004


class MyClient(discord.Client):

    working = True

    async def on_ready(self):
        print('Logged on as', self.user)
        await self.send_msg()

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content.lower() in ['start', 'старт']:
            self.working = True
            await message.channel.send('Начинаю работу')

        if message.content.lower() in ['stop', 'стоп']:
            self.working = False
            await message.channel.send('Прекращаю работу')

    @staticmethod
    async def parse():

        res = list()

        r = requests.get('https://www.roseltorg.ru/procedures/search_ajax?query_field=%D0%BF%D0%BE%D1%81%D1%82%D0%B0%D0%B2%D0%BA&customer=&status%5B%5D=0&address=&start_price=&end_price=&currency=all&start_date_published=&end_date_published=&guarantee_start_price=&guarantee_end_price=&start_date_requests=&end_date_requests=&form_id=searchp_form&page=')
        if r.status_code != 200:
            return None
        soup = bs(r.text, 'html.parser')
        urls = soup.find_all('a', class_=re.compile('search-results__link'))
        if len(urls) == 0:
            return None

        for u in urls:
            url = f"https://www.roseltorg.ru{u.get('href')}"
            r = requests.get(url)
            if r.status_code != 200:
                continue
            soup = bs(r.text, 'html.parser')
            h1 = soup.find('h1').text.replace('Процедура:', '').strip()
            summ = soup.find('div', class_='lot-item__sum').text.strip()
            params = soup.find_all('p', class_='data-table__info')
            summ_params = soup.find_all('span', class_='lot-item__summ')
            line = {
                'Title': f"{h1} (Лот 1) - НМЦ - {summ}",
                'Наименование процедуры': params[0].text,
                'Организатор': params[1].text,
                'Обеспечение заявки': summ_params[0].text,
                'Обеспечение контракта': summ_params[1].text,
                'Публикация извещения': params[4].text,
                'Примем заявок': params[5].text,
                'ЭП': url,
            }
            # for n, p in enumerate(params):
            #     print(n, p)
            res.append(line)
            await asyncio.sleep(1)

        return res

    async def send_msg(self):
        while True:
            if self.working:
                channel = self.get_channel(id=CHANNEL_ID)
                if channel:

                    # получаем последние 200 сообщений (список урлов процедур)
                    urls = list()
                    async for msg in channel.history(limit=200):
                        if msg.author == self.user:
                            if len(msg.embeds) > 0:
                                embed = msg.embeds[0].to_dict()
                                if 'fields' not in embed.keys():
                                    continue
                                for f in embed['fields']:
                                    if f['name'] == 'ЭП':
                                        urls.append(f['value'])

                    res = await self.parse()
                    if len(res) > 0:
                        for r in res:
                            if r['ЭП'] in urls:
                                continue
                            embed = discord.Embed(title=r['Title'], color=0x00ff00)
                            # embed.from_dict(r)
                            for k in r.keys():
                                if k == 'Title':
                                    continue
                                embed.add_field(name=k, value=r[k], inline=False)
                            await channel.send(embed=embed)
                            break
                    else:
                        await channel.send('ошибка')
            await asyncio.sleep(60)


client = MyClient()
client.run(TOKEN)
