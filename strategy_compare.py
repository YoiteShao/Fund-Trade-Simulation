# https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code=000001&sdate=2018-12-18&edate=2021-10-25&per=20&page=1


import urllib.request
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from bs4 import BeautifulSoup
from datetime import datetime


class fund_script():
    def __init__(self, code, start, end, cash):
        self.head = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/81.0.4044.138 Safari/537.36',
            }
        ]
        self.fund_dock = pd.DataFrame(columns=["date", "unit_gain", "add_gain", "rate"])
        self.code = code
        self.start = start
        self.end = end
        self.cash = cash
        self.get_dock()
        self.start_unit_gain = self.fund_dock.iloc[-1]['unit_gain']
        print("start_unit_gain", self.start_unit_gain)
        self.end_unit_gain = self.fund_dock.iloc[0]['unit_gain']
        print("end_unit_gain", self.end_unit_gain)
        self.end_add_gain = self.fund_dock.iloc[0]['add_gain']

    def script(self, url):
        """
        Crawling basic script
        :param url:target url
        :return:str, all the context
        """
        index = 0
        request = urllib.request.Request(url, headers=self.head[index])
        html = urllib.request.urlopen(request)
        soup = BeautifulSoup(html, features='html.parser')
        word = str(soup)
        return word

    def get_all_pages(self, code, start, end):
        """
        get all pages from the estmoney port
        :param code: fund code
        :param start: start date
        :param end: end date
        :return: int, all pages amount
        """
        url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code=" + code + "&sdate=" + start \
              + "&edate=" + end + "&per=40&page=1"
        word = self.script(url)
        all_page = word[word.index("pages:") + 6:word.index(",curpage")]
        return int(all_page)

    def basic_page(self, code, start, end, k):
        """
        get each page
        """
        url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code=" + code + "&sdate=" + start \
              + "&edate=" + end + "&per=40&page=" + str(k)
        word = self.script(url)
        return word

    def get_dock(self):
        """
        get all fund data
        """
        all_page = self.get_all_pages(self.code, self.start, self.end)
        for i in range(1, all_page + 1):
            once_res = self.basic_page(self.code, self.start, self.end, i)
            once_array = once_res[once_res.index("<tbody>") + 7:once_res.index("</tbody>")].split("</tr>")
            self.list_process(once_array)
        return self.fund_dock

    def list_process(self, array):
        """
        process data from html language to python array
        :return: save data to self.fund_dock
        """
        for item in array:
            temp_item = item.split("</td>")
            if temp_item[0]:
                date = temp_item[0][8:]
                unit_gain = float(temp_item[1][21:])
                add_gain = float(temp_item[2][21:])
                try:
                    rate = float(temp_item[3][25:][:-1]) / 100
                except:
                    rate = 0
                self.fund_dock.loc[date] = [date, unit_gain, add_gain, rate]

    def date_check(self, date, days):
        """
        chose which day to invest
        :param date: such as 2020-08-07
        :param days: array , days range
        :return: bool
        """
        week = datetime.strptime(date, "%Y-%m-%d").weekday()
        for day in days:
            if week + 1 == day:
                return True
        return False

    def get_months(self):
        """
        get months between start date and end date
        """
        years = int(self.end[:4]) - int(self.start[:4])
        month = int(self.end[5:7]) - int(self.start[5:7])
        return years * 12 + month

    def rate_strategy(self, invest_rate, stop_rate, record=False, draw=False):
        """
        Rate strategy:
        Set init Psychological value when you buy at first, continue buy it when the value fall down more than the rate
        Change your Psychological value when the value rise more than the rate
        """
        months = self.get_months()
        cash = self.cash
        #   Invest the principal in batches on a monthly basis
        single_money = cash // months
        #   fist time to buy
        curr_price = self.start_unit_gain
        buy_count = math.floor(single_money / curr_price)
        fund_counts = [buy_count]
        cash -= curr_price * buy_count
        # Init buy&sell record
        buy_record_y, buy_record_x, sell_record_y, sell_record_x = [], [], [], []
        #   each time to buy
        for i in self.fund_dock.index[::-1]:
            # today price
            today_price = self.fund_dock.loc[i]['unit_gain']

            # today all value
            value = sum(fund_counts) * today_price
            # all single money
            all_money = single_money * sum(1 for x in fund_counts if x > 0)
            if record:
                print(self.fund_dock.loc[i]['date'], " ||original price:", curr_price, " ||today price:", today_price,
                      "||yesterday trade", fund_counts[-1],
                      " ||profit: ", (value - all_money) / all_money)
            # check stop and add to cash
            sell_count = self.stop_strategy(cash, fund_counts, today_price, stop_rate)
            fund_counts.append(-sell_count)
            if sell_count > 0:
                sell_record_y.append(today_price)
                sell_record_x.append(self.fund_dock.loc[i]['date'])
            cash += sell_count * today_price

            # If fall
            if today_price < curr_price:
                #   If fall more than invest rate, buy and reduce money
                if (curr_price - today_price) / today_price >= invest_rate:
                    if cash >= single_money:
                        buy_count = math.floor(single_money / today_price)
                        fund_counts.append(buy_count)
                    elif single_money > cash > 0:
                        buy_count = math.floor(cash / today_price)
                        fund_counts.append(buy_count)

                    cash -= buy_count * today_price
                    curr_price = today_price
                    buy_record_y.append(today_price)
                    buy_record_x.append(self.fund_dock.loc[i]['date'])
                    if record:
                        print("   buy:", today_price, " count:", buy_count)

            else:
                #   If rise too high , change current price
                if (today_price - curr_price) / curr_price >= invest_rate * 2.5:
                    curr_price = today_price

        print("****rate_strategy****")
        print("buy times: ", sum(1 for x in fund_counts if x > 0))
        print("sell times: ", sum(1 for x in fund_counts if x < 0))
        print("Final value: ", cash + sum(fund_counts) * self.end_unit_gain)
        if draw:
            self.draw(buy_record_y, buy_record_x, sell_record_y, sell_record_x, "****rate_strategy****")

    def week_strategy(self, days_array, stop_rate, record=False, draw=False):
        """
        invest once a week at Monday\Tuesday...
        :param days_array: week
        """
        months = self.get_months()
        cash = self.cash
        #   Invest the principal in batches on a monthly basis
        single_money = cash // (months * 4)
        fund_counts = [0]
        # Init buy&sell record
        buy_record_y, buy_record_x, sell_record_y, sell_record_x = [], [], [], []
        #   Buy once a week at specific day
        for i in self.fund_dock.index[::-1]:
            # today price
            today_price = self.fund_dock.loc[i]['unit_gain']
            # today all value
            value = sum(fund_counts) * today_price
            # all single money
            all_money = single_money * sum(1 for x in fund_counts if x > 0) + 1e-10
            if record:
                print(self.fund_dock.loc[i]['date'], " ||today price:", today_price, " ||yesterday trade",
                      fund_counts[-1],
                      " ||profit: ", (value - all_money) / all_money)
            # check stop
            sell_count = self.stop_strategy(cash, fund_counts, today_price, stop_rate)
            fund_counts.append(-sell_count)
            if sell_count > 0:
                sell_record_y.append(today_price)
                sell_record_x.append(self.fund_dock.loc[i]['date'])
            cash += sell_count * today_price
            #   If today is the day, buy and reduce money
            if self.date_check(self.fund_dock.loc[i]['date'], days_array):
                buy_count = math.floor(single_money / self.fund_dock.loc[i]['unit_gain'])
                fund_counts.append(buy_count)
                cash -= buy_count * today_price
                if record:
                    print("   buy:", today_price, " count:", buy_count)
                buy_record_y.append(today_price)
                buy_record_x.append(self.fund_dock.loc[i]['date'])

        print("****week_strategy****")
        print("buy times: ", sum(1 for x in fund_counts if x > 0))
        print("sell times: ", sum(1 for x in fund_counts if x < 0))
        print("Final value: ", cash + sum(fund_counts) * self.end_unit_gain)

        if draw:
            self.draw(buy_record_y, buy_record_x, sell_record_y, sell_record_x, "****week_strategy****")

    def stop_strategy(self, all_money, fund_counts, today_price, stop_rate):
        """
        Profit stopping strategy
        When the all invest value amoutn larger than your init value , it can be sold
        :return: sell count
        """
        invest_value = sum(fund_counts) * today_price
        # If the stop ratio is exceeded
        if ((invest_value - all_money) / all_money) >= stop_rate:
            # print("Now reach stop point: ", (invest_value - (self.cash - cash)) / (self.cash - cash))
            sell_count = invest_value // today_price
            #   If stop point has not been reached last time
            if fund_counts[-1] >= 0:
                print(" sell: ", today_price, " count:", math.floor(sell_count * stop_rate))
                return math.floor(sell_count * stop_rate)
            #   If stop point has been reached last time
            else:
                print(" sell: ", today_price, " count:",
                      math.floor(sell_count * (((invest_value - all_money) / all_money) - stop_rate)))
                return math.floor(sell_count * (((invest_value - all_money) / all_money) - stop_rate))
        else:
            return 0

    def draw(self, buy_record_y=[], buy_record_x=[], sell_record_y=[], sell_record_x=[], title=""):
        font1 = {'family': 'Times New Roman', 'weight': 'normal', 'size': 10}
        plt.ylabel("Average NAV", font1)  # 设置纵轴单位
        y = self.fund_dock['unit_gain'][::-1]
        x = self.fund_dock['date'][::-1]
        plt.title(title)
        plt.plot(x, y, color='blue',alpha=0.5)
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(31))
        plt.xticks(rotation=60)
        plt.scatter(sell_record_x, sell_record_y, marker='o', color='red', edgecolors='red', s=15, clip_on=False,
                    label='Sell')
        plt.scatter(buy_record_x, buy_record_y, marker='o', color='forestgreen', edgecolors='forestgreen', s=15,
                    clip_on=False, label='Buy')
        plt.legend(loc='lower right')
        plt.show()


way = fund_script("007301", "2019-07-01", "2021-10-27", 10000)
context = way.get_dock()
# pd.set_option('display.max_rows',None)
print(context)
way.rate_strategy(0.04, 0.2, False, True)
# way.week_strategy([1, 3, 5], 0.2, False, True)
# way.draw()
