import sys
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import urllib.request
import configparser

config = configparser.ConfigParser()
path = sys.argv[1]
config.read(path)


def script(url):
    """
    Crawling basic script
    :param url:target url
    :return:str, all the context
    """
    request = urllib.request.Request(url)
    html = urllib.request.urlopen(request)
    soup = BeautifulSoup(html, features='html.parser')
    word = str(soup)
    return word


def list_process(array):
    """
    process data from html language to dict
    :return: save unit gain data to fund_history
    """
    fund_history = {}
    for item in array:
        temp_item = item.split("</td>")
        if temp_item[0]:
            date = temp_item[0][8:]
            unit_gain = float(temp_item[1][21:])
            fund_history[date] = unit_gain
    return fund_history


def getHistoryGain(code, date):
    """
    to get selected date unit gain
    """
    url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code=" + code + \
          "&sdate=2021-01-01&edate=2030-01-01&per=40&page=1"
    once_res = script(url)
    once_array = once_res[once_res.index("<tbody>") + 7:once_res.index("</tbody>")].split("</tr>")
    fund_history = list_process(once_array)
    return fund_history[date]


def getTodayGain(code):
    """
    to get today gain
    """
    url = "http://fundgz.1234567.com.cn/js/" + code + ".js?"
    res = script(url)
    try:
        price = res[res.index("gsz") + 6:res.index("gszzl") - 3]
        time = res[res.index("gztime") + 9:-4]
        name = res[res.index("name") + 7:res.index("jzrq") - 3]
    except Exception:
        return None, None, None
    return time, name, price


for old_code in config["DATA"]:
    spec_date = config["DATA"][old_code]
    if spec_date:
        old_price = getHistoryGain(old_code, spec_date)
        price_range = (old_price / 1.015, old_price * 1.015)
        today_time = getTodayGain(old_code)[0]
        code_name = getTodayGain(old_code)[1]
        today_price = getTodayGain(old_code)[2]
        if today_price:
            changed = True if float(today_price) >= old_price * 1.015 else False
            buy = True if float(today_price) <= old_price / 1.015 else False
        else:
            changed = False
            buy = False
        print(
            "--CODE--|-------Now------|-Valuation-|-Low Price-|-High Price-|-HistoryDATE-|-BUY-|-Changed-|")
        print(code_name)
        print("{}  |{}|   {}  | ↓ {} |  ↑ {} | {}  |{}|  {}  | \n\n".format(old_code, today_time, today_price,
                                                                            round(price_range[0], 5),
                                                                            round(price_range[1], 5),
                                                                            spec_date, buy, changed))
        if buy or changed:
            print("Operate", old_code, today_time[:10])
            config.set("DATA", old_code, today_time[:10])

with open(path, "w") as fw:
    config.write(fw)
