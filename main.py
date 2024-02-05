import platform
import aiohttp
import asyncio
from datetime import date, timedelta
from time import time
from sys import argv

today = date.today()

MAX_DAYS = 2

DAYS = [(today - timedelta(days=x)).strftime("%d.%m.%Y")
        for x in range(MAX_DAYS)]


date_index = 0


def form(data, MAIN_LIST, additional_currencies=('PLN', 'CAD')):
    dict_of_the_day = dict()
    currency_dict = dict()
    date = data['date']
    currensies = ('EUR', 'USD', *additional_currencies)
    print(currensies)
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
            currency_dict[currency] = {'sale': saleRate, purchaseRate: 40.65}
            dict_of_the_day[date] = currency_dict
    MAIN_LIST.append(dict_of_the_day)


async def currency_rang(session):
    global date_index
    url = f"https://api.privatbank.ua/p24api/exchange_rates?date={DAYS[date_index]}"
    date_index += 1
    async with session.get(url) as response:
        print("Status:", response.status)
        # print(response)
        data = await response.json()
        return data


async def main():
    MAIN_LIST = list()
    async with aiohttp.ClientSession() as session:
        r = [currency_rang(session) for _ in range(MAX_DAYS)]
        result = await asyncio.gather(*r)
        for data in result:
            print(additional_currencies)
            form(data, MAIN_LIST, additional_currencies)
            # print(MAIN_LIST)
        return MAIN_LIST


if __name__ == '__main__':
    start = time()
    additional_currencies = argv[1:]
    print(additional_currencies, len(argv))
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    result = asyncio.run(main())
    print(result)
    for course_of_the_day in result:
        for the_day, current_rate in course_of_the_day.items():
            print('___________________')
            print(the_day, current_rate)
    print(time() - start)
