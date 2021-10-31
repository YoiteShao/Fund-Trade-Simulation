import urllib.request
import pandas as pd
import math
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from datetime import datetime


def stop_strategy(all_single_money, fund_counts, today_price, stop_rate):
    """
    Profit stopping strategy
    When the all invest value amount more than your init value , it can be sold
    :return: sell count
    """
    #   Value of funds currently held
    invest_value = sum(fund_counts) * today_price

    # If the stop ratio is exceeded, buy a few counts
    if ((invest_value - all_single_money) / all_single_money) >= stop_rate:
        sell_count = invest_value // today_price
        #   If stop point has not been reached last time, sell sell_count * stop_rate
        if fund_counts[-1] >= 0:
            return math.floor(sell_count * stop_rate)
            # return math.floor(sell_count * stop_rate * 2)
        #   If stop point has been reached last time, sell sell_count * (now_profit_rate-stop_rate)
        else:
            return math.floor(sell_count * (((invest_value - all_single_money) / all_single_money) - stop_rate))
    #   else do nothing
    else:
        return 0


def date_check(date, days):
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


class fund_script:
    def __init__(self, code, start, end, cash):
        """
        :param code:    Fund code
        :param start:   Start Date Time
        :param end:     End Date Time
        :param cash:    Cash reserves
        """
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
                except ValueError:
                    rate = 0
                self.fund_dock.loc[date] = [date, unit_gain, add_gain, rate]

    def get_months(self):
        """
        get months between start date and end date
        """
        years = int(self.end[:4]) - int(self.start[:4])
        month = int(self.end[5:7]) - int(self.start[5:7])
        return years * 12 + month

    def rate_strategy(self, invest_rate, stop_rate, record=False, draw=False):
        """
        Investment through ratio, if the decline exceeds invest_rate to purchase and update the preset price.
        :param invest_rate: Investment point
        :param stop_rate:   Interference stop point
        :param record:      Print daily transaction information
        :param draw:        Draw an investment chart
        """
        months = self.get_months()
        cash = self.cash
        #   Single investment amount in batches on a monthly basis
        single_money = cash // months

        #   fist day to buy
        curr_price = self.start_unit_gain
        buy_count = math.floor(single_money / curr_price)
        #   invest counts record
        fund_counts = [buy_count]
        cash -= curr_price * buy_count

        # Init buy&sell draw record
        buy_record_y, buy_record_x, sell_record_y, sell_record_x = [], [], [], []

        #   each time to buy
        for i in self.fund_dock.index[::-1]:
            # today price
            today_price = self.fund_dock.loc[i]['unit_gain']

            # today all value
            value = sum(fund_counts) * today_price

            # Total investment amount
            all_single_money = single_money * sum(1 for x in fund_counts if x > 0)

            # check stop and add to cash
            sell_count = stop_strategy(all_single_money, fund_counts, today_price, stop_rate)
            fund_counts.append(-sell_count)
            cash += sell_count * today_price

            if record:
                print(self.fund_dock.loc[i]['date'], " ||Preset price:", curr_price, " ||Today price:", today_price,
                      "||Yesterday trade", fund_counts[-1],
                      " ||Profit: ", (value - all_single_money) / all_single_money, " ||Remaining cash:", cash)
                if sell_count > 0:
                    print("========> Sell ", sell_count)

            #   draw part
            if sell_count > 0:
                sell_record_y.append(today_price)
                sell_record_x.append(self.fund_dock.loc[i]['date'])

            # If Decline
            if today_price < curr_price:
                #   If Decline more than invest_rate, buy and reduce cash
                if (curr_price - today_price) / today_price >= invest_rate:
                    if cash >= single_money:
                        buy_count = math.floor(single_money / today_price)
                        fund_counts.append(buy_count)
                    elif single_money > cash > 0:
                        buy_count = math.floor(cash / today_price)
                        fund_counts.append(buy_count)

                    #   Updated cash and preset price
                    cash -= buy_count * today_price
                    curr_price = today_price

                    #   draw part
                    buy_record_y.append(today_price)
                    buy_record_x.append(self.fund_dock.loc[i]['date'])

                    if record:
                        print("========> Buy", buy_count)

            else:
                #   If rise too high , change preset price
                if (today_price - curr_price) / curr_price >= invest_rate * 2.5:
                    curr_price = today_price
            #   Multiplied by the IMF interest rate
            cash = cash * (1 + 5.5 * 1e-5)

        print("****rate_strategy****invest rate:{} stop rate:{}".format(invest_rate, stop_rate))
        print("buy times: ", sum(1 for x in fund_counts if x > 0))
        print("sell times: ", sum(1 for x in fund_counts if x < 0))
        print("Final value: ", cash + sum(fund_counts) * self.end_unit_gain)
        print("Remaining cash:", cash)

        if draw:
            self.draw(buy_record_y, buy_record_x, sell_record_y, sell_record_x, "****rate_strategy****")

        return cash + sum(fund_counts) * self.end_unit_gain, cash

    def week_strategy(self, days_array, stop_rate, record=False, draw=False):
        """
        Invest once a week at specific day
        :param days_array: Chose which day to invest
        :param stop_rate:   Interference stop point
        :param record:      Print daily transaction information
        :param draw:        Draw an investment chart
        """
        months = self.get_months()
        cash = self.cash

        #   Single investment amount
        single_money = cash // (months * 4 * len(days_array))

        #   invest counts record
        fund_counts = [0]

        # draw part
        buy_record_y, buy_record_x, sell_record_y, sell_record_x = [], [], [], []

        #   Buy once a week at specific day
        for i in self.fund_dock.index[::-1]:
            # today price
            today_price = self.fund_dock.loc[i]['unit_gain']

            # today all value
            value = sum(fund_counts) * today_price

            # Total investment amount
            all_single_money = single_money * sum(1 for x in fund_counts if x > 0) + 1e-10

            # check stop and add to cash
            sell_count = stop_strategy(all_single_money, fund_counts, today_price, stop_rate)
            fund_counts.append(-sell_count)
            cash += sell_count * today_price

            if record:
                print(self.fund_dock.loc[i]['date'], " ||Today price:", today_price, " ||Yesterday trade",
                      fund_counts[-1], " ||Profit: ", (value - all_single_money) / all_single_money,
                      " ||Remaining cash:", cash)
                if sell_count > 0:
                    print("========> Sell ", sell_count)

            #   draw part
            if sell_count > 0:
                sell_record_y.append(today_price)
                sell_record_x.append(self.fund_dock.loc[i]['date'])

            #   If today is the day, buy and reduce money
            if date_check(self.fund_dock.loc[i]['date'], days_array):
                buy_count = 0
                if cash >= single_money:
                    buy_count = math.floor(single_money / self.fund_dock.loc[i]['unit_gain'])
                    fund_counts.append(buy_count)
                elif single_money > cash > 0:
                    buy_count = math.floor(cash / self.fund_dock.loc[i]['unit_gain'])
                    fund_counts.append(buy_count)
                #   Updated cash and preset price
                cash -= buy_count * today_price

                if record:
                    print("========> Buy", buy_count)

                #   draw part
                buy_record_y.append(today_price)
                buy_record_x.append(self.fund_dock.loc[i]['date'])
            #   Multiplied by the IMF interest rate
            cash = cash * (1 + 5.5 * 1e-5)

        print("****week_strategy****days:{} stop rate: {}".format(days_array, stop_rate))
        print("buy times: ", sum(1 for x in fund_counts if x > 0))
        print("sell times: ", sum(1 for x in fund_counts if x < 0))
        print("Final value: ", cash + sum(fund_counts) * self.end_unit_gain)
        print("Remaining cash:", cash)

        if draw:
            self.draw(buy_record_y, buy_record_x, sell_record_y, sell_record_x, "****week_strategy****")

        return cash + sum(fund_counts) * self.end_unit_gain, cash

    def draw(self, buy_record_y=[], buy_record_x=[], sell_record_y=[], sell_record_x=[], title=""):
        font1 = {'family': 'Times New Roman', 'weight': 'normal', 'size': 10}
        plt.ylabel("Average NAV", font1)
        y = self.fund_dock['unit_gain'][::-1]
        x = self.fund_dock['date'][::-1]
        plt.title(title)
        plt.plot(x, y, color='blue', alpha=0.5)
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(31))
        plt.xticks(rotation=60)
        plt.scatter(sell_record_x, sell_record_y, marker='o', color='red', edgecolors='red', s=15, clip_on=False,
                    label='Sell')
        plt.scatter(buy_record_x, buy_record_y, marker='o', color='forestgreen', edgecolors='forestgreen', s=15,
                    clip_on=False, label='Buy')
        plt.legend(loc='lower right')
        plt.show()

    def FindRateRangeInRateStrategy(self, invest_start, invest_end, invest_step, stop_start, stop_end, stop_step):
        """
        Find Rate Range In Rate Strategy include invest start and stop rate
        """

        def crack(number):
            start = int(number ** 0.5)
            factor = number / start
            while not int(factor) == factor:
                start += 1
                factor = number / start
            return [start, int(factor)]

        integer = int(round((stop_end - stop_start) / stop_step, 1) + 1)
        subplots = crack(integer)
        i = 0
        global_final_value_dock = [[] for _ in range(integer)]

        global_final_cash_dock = [[] for _ in range(integer)]
        global_x = [[] for _ in range(integer + 1)]
        global_final_all_dock = [[] for _ in range(integer)]
        stop_rate = stop_start
        plt.figure(dpi=150)
        while stop_rate <= stop_end + stop_step:
            invest_rate = invest_start
            while invest_rate <= invest_end + invest_step:
                global_x[i].append(invest_rate)
                global_final_value_dock[i].append(self.rate_strategy(invest_rate, stop_rate, False, False)[0])
                global_final_cash_dock[i].append(self.rate_strategy(invest_rate, stop_rate, False, False)[1])
                invest_rate += invest_step

            global_final_all_dock[i] = [f1 + f2 for f1, f2 in
                                        zip(global_final_value_dock[i], global_final_cash_dock[i])]
            # print("subplots:", subplots[0], subplots[1], i + 1)
            plt.subplot(subplots[0], subplots[1], i + 1)
            plt.plot(global_x[i], global_final_value_dock[i], label='Final Value')
            plt.plot(global_x[i], global_final_cash_dock[i], label='Remain Cash')
            plt.plot(global_x[i], global_final_all_dock[i], label='Total property')
            plt.legend(loc='best', fontsize=17 - integer)
            plt.xticks(fontsize=17 - integer)
            plt.yticks(fontsize=17 - integer)
            plt.ylabel("Money", fontsize=17 - integer)
            plt.xlabel("Invest Rate", fontsize=17 - integer)
            plt.title("Best Rate Range In Rate Strategy with " + str(round(stop_rate, 2)) + " Stop Rate",
                      fontsize=17 - integer)
            plt.grid()
            i += 1
            stop_rate += stop_step
        plt.tight_layout()

        plt.show()

    def FindDayRangeInWeekStrategy(self, days_list, stop_start, stop_end, stop_step):
        """
        Find Day Range In Week Strategy
        days_list: All combinations of all fixed investment days
        """

        def crack(number):
            start = int(number ** 0.5)
            factor = number / start
            while not int(factor) == factor:
                start += 1
                factor = number / start
            return [start, int(factor)]

        integer = int(round((stop_end - stop_start) / stop_step, 1) + 1)
        subplots = crack(integer)
        i = 0
        global_final_value_dock = [[] for _ in range(integer)]
        global_final_cash_dock = [[] for _ in range(integer)]
        global_x = [[] for _ in range(integer + 1)]
        global_final_all_dock = [[] for _ in range(integer)]
        stop_rate = stop_start
        plt.figure(dpi=150)
        while stop_rate <= stop_end + stop_step:
            for item in days_list:
                global_x[i].append(str(item))
                global_final_value_dock[i].append(self.week_strategy(item, stop_rate, False, False)[0])
                global_final_cash_dock[i].append(self.week_strategy(item, stop_rate, False, False)[1])
            global_final_all_dock[i] = [f1 + f2 for f1, f2 in
                                        zip(global_final_value_dock[i], global_final_cash_dock[i])]
            plt.subplot(subplots[0], subplots[1], i + 1)

            plt.plot(global_x[i], global_final_value_dock[i], label='Final Value')
            plt.plot(global_x[i], global_final_cash_dock[i], label='Remain Cash')
            plt.plot(global_x[i], global_final_all_dock[i], label='Total property')

            plt.legend(loc='best', fontsize=17 - integer)
            plt.xticks(fontsize=17 - integer)
            plt.yticks(fontsize=17 - integer)
            plt.ylabel("Money", fontsize=17 - integer)
            plt.xlabel("Days", fontsize=17 - integer)
            plt.title("Best Rate Range In Week Strategy with " + str(round(stop_rate, 2)) + " Stop Rate",
                      fontsize=17 - integer)
            plt.grid()
            i += 1
            stop_rate += stop_step
        plt.tight_layout()

        plt.show()


if __name__ == '__main__':
    way = fund_script("270042", "2019-07-01", "2021-10-27", 10000)
    context = way.get_dock()
    # pd.set_option('display.max_rows',None)
    print(context)
    # way.rate_strategy(0.02, 0.3, False, True)
    # way.week_strategy([1, 3, 5], 0.2, False, True)

    way.FindDayRangeInWeekStrategy([[1], [2], [3], [4], [5]], 0.18, 0.4, 0.02)
    way.FindRateRangeInRateStrategy(0.02, 0.1, 0.01, 0.18, 0.4, 0.02)
