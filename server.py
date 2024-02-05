import platform
import asyncio
import logging
import websockets
import names
import aiohttp
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import date, timedelta
from main import form

today = date.today()
MAIN_LIST = list()

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    def form(self, data, MAIN_LIST, additional_currencies=('PLN', 'CAD')):
        dict_of_the_day = dict()
        currency_dict = dict()
        date = data['date']
        currensies = ('EUR', 'USD', *additional_currencies)
        exchangeRate = data['exchangeRate']
        for line in exchangeRate:
            currency = line['currency']

            if currency in currensies:
                if 'saleRate' in line:
                    saleRate = line['saleRate']
                else:
                    saleRate = line['saleRateNB']
                if 'purchaseRate' in line:
                    purchaseRate = line['purchaseRate']
                else:
                    purchaseRate = line['purchaseRateNB']
                currency_dict[currency] = {
                    'sale': saleRate, 'purchase': purchaseRate}
                dict_of_the_day[date] = currency_dict
        MAIN_LIST.append(dict_of_the_day)

    async def exchange(self, ws: WebSocketServerProtocol):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.privatbank.ua/p24api/exchange_rates?date={today.strftime("%d.%m.%Y")}') as response:
                data = await response.json()
        self.form(data, MAIN_LIST, '_')
        for course_of_the_day in MAIN_LIST:
            for the_day, current_rate in course_of_the_day.items():
                message = f'{the_day}, {current_rate}'
        await self.send_to_clients(f"{ws.name}: {message}")

    async def currency_rang(self, session, day):
        url = f"https://api.privatbank.ua/p24api/exchange_rates?date={day}"
        async with session.get(url) as response:
            print("Status:", response.status)
            data = await response.json()
            return data

    async def exchange_2(self, additional_currencies, days, ws):
        DAYS = [(today - timedelta(days=x)).strftime("%d.%m.%Y")
                for x in range(days)]
        async with aiohttp.ClientSession() as session:
            r = [self.currency_rang(session, day) for day in DAYS]
            result = await asyncio.gather(*r)
            for data in result:
                self.form(data, MAIN_LIST, additional_currencies)
            return MAIN_LIST

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == 'exchange':
                await self.exchange(ws)
            elif message.startswith('exchange'):
                days = int(message.split()[1])
                additional_currencies = message.split()[2:]
                result = await self.exchange_2(additional_currencies, days, ws)
                r = list()
                for rage_of_day in result:
                    r.append(self.send_to_clients(f"{ws.name}: {rage_of_day}"))
                await asyncio.gather(*r)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
