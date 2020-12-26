# coding utf-8
import csv
import datetime
import re
import dataclasses
import os
import subprocess

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#import japanize_matplotlib
import pandas as pd
FILENAME = "./SaveFile_000001_000427.csv"

MS_GOTHIC = 'MS Gothic'

class Deal():
    ''' 取引 '''
    def __init__(self, row:list):
        date_str = row.pop(0)
        sp = date_str.split("/")
        rsp = [ re.sub('[^0-9]','',x) for x in sp]
        self.date = datetime.date(*[int(x) for x in rsp])

        self.brandname = row.pop(0)
        self.brandcode = row.pop(0)
        self.market = row.pop(0)
        self.type = row.pop(0)
        self.limit = row.pop(0)
        self.account = row.pop(0)
        self.tax_type = row.pop(0)
        self.quantity = int(row.pop(0))
        self.value = float(row.pop(0))
        self.fee  = row.pop(0)
        self.tax = row.pop(0)
        self.dealdate = row.pop(0)
    
    @property
    def is_buy_stock(self):
        try:
            if self.type == '株式現物買':
                return True
            return False
        except Exception as e:
            print(self.__dict__)
            print(e)
            return False
    
    @property
    def is_sell_stock(self):
        try:
            if self.type == '株式現物売':
                return True
            return False
        except Exception as e:
            print(self.__dict__)
            print(e)
            return False

class Deal_for_rakuten(Deal):
    pass

class Deals():
    def __init__(self, filename,cls=Deal):
        self.filename=filename
        self.deals=[]
        with open(filename, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                try:
                    try:
                        d = cls(row[:])
                    except Exception as e:
                        print(f"{e}\n{row}")
                        continue
                    self.deals.append(d)
                    continue
                except Exception:
                    continue
    
    def assign(self):
        self.asset_history = Assets_History()
        asset = Assets(0,0,0)
        self.HoldPool = HoldPool()

        start = datetime.date(2020,1,1)
        next_sunday = start + datetime.timedelta(days=(6-start.weekday()))
        for deal in self.deals:
            while True:
                if deal.date > next_sunday:
                    x = Assets_snapshot(assets=asset, ss_date=next_sunday)
                    self.asset_history.append(x)
                    next_sunday = next_sunday + datetime.timedelta(weeks=1)
                else:
                    break
            result = self.HoldPool.add(deal)
            print(asset, result)
            asset = asset + result
        self.asset_history.append(entry=Assets_snapshot(assets=asset, ss_date=datetime.date(2020,12,31)))
        
        self.asset_history.base_zero()
        self.asset_history.out()



    def output(self):        
        print("---<history>---")
        print(History.csvheader())
        for his in self.HoldPool.history:
            print(his.csv)
        print("---<hold pool>---")
        for hold in self.HoldPool.hold:
            print(hold.__dict__)

        dir = os.path.dirname(self.filename)
        path = (f'{dir}//out//')
        try:
            os.mkdir(path)
        except Exception:
            print(f"{path} is exist")
            pass
        with open(f"{path}/history.csv", newline='',mode='w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(History.csvheader())
            for his in self.HoldPool.history:
                writer.writerow(his.csv)

        fig = plt.figure(figsize=(16,9))
        ax = fig.add_subplot(1,1,1)

        for his in self.HoldPool.history:
            x,y,name = his.graph_data()
            ax.plot(x,y,'-o',label=name)

        for deal in self.HoldPool.hold:
            x = [(deal.date-datetime.date(2020,1,1)).days,364]
            y = [deal.quantity * deal.value, deal.quantity * deal.value]
            ax.plot(x,y,'-o',label=deal.brandname)
        
        x = self.asset_history.date_ticks
        cashs = self.asset_history.cash_ticks
        stocks = self.asset_history.stock_ticks
        ax.bar(x,stocks,width=4.0,alpha=0.3,label='株')
        ax.bar(x,cashs,width=4.0,alpha=0.3,bottom=stocks,label='現金')

        ax.set_xlim([0,366])
        ax.grid(True)
        plt.legend(ncol=4,bbox_to_anchor=(0.5, 1), loc='lower center',prop={"family":MS_GOTHIC})
        plt.savefig(f"{path}timeline.png",bbox_inches='tight')        
        #plt.show()        
        print(path)
        #ubprocess.Popen(['explorer',path])
        #os.startfile(path)
        return (path)

    def __isBuydeal(self,d:Deal):
        if d.type == "投信金額買付":
            return True
        elif d.type == "株式現物買":
            return True
        else:
            return False

class History():
    def __init__(self,
                brandname,
                brandcode, 
                quantity, 
                buy_date, 
                buy_value, 
                sell_date, 
                sell_value):
        self.brandname = brandname
        self.brandcode = brandcode
        self.quantity = quantity
        self.buy_date = buy_date
        self.buy_value = buy_value
        self.sell_date = sell_date
        self.sell_value = sell_value
        self.term = (self.sell_date - self.buy_date)
        self.advantage = self.quantity * (self.sell_value - self.buy_value)
        self.advantage_rate = (self.sell_value - self.buy_value) / self.buy_value
        self.advantage_per_day = self.advantage / (1+self.term.days )
        self.advantage_rate_per_day = self.advantage_rate / (1+self.term.days )

    @staticmethod
    def csvheader():
        return ["銘柄名","銘柄コード","数量","買日付","買値","売日","売値","保有期間","損益","損益率","日割り損益","日割り損益率"]

    @property
    def csv(self):
        return [self.brandname,
                self.brandcode,
                self.quantity,
                self.buy_date,
                self.buy_value,
                self.sell_date,
                self.sell_value,
                self.term.days,
                self.advantage,
                self.advantage_rate,
                self.advantage_per_day,
                self.advantage_rate_per_day]
    
    def graph_data(self):
        x = [(self.buy_date - datetime.date(2020,1,1)).days, (self.sell_date-datetime.date(2020,1,1)).days]
        y = [self.buy_value*self.quantity,self.sell_value*self.quantity]
        return (x,y,self.brandname)

@dataclasses.dataclass
class Assets():
    cash : int = 0
    stocks: int = 0
    investment : int = 0
    other:int = 0
    
    def __add__(self, other):
        return Assets(self.cash + other.cash,
                        self.stocks + other.stocks,
                        self.investment + other.investment)

    @property
    def sum(self):
        return self.cash + self.stocks + self.investment + self.other

@dataclasses.dataclass
class Assets_snapshot():
    assets : Assets
    ss_date :datetime.date

class Assets_History():
    def __init__(self):
        self.history = []

    def append(self, entry:Assets_snapshot):
        self.history.append(entry)
    
    def base_zero(self):
        min_cash = min([h.assets.cash for h in self.history])
        new = []
        for h in self.history:
            x = h.assets + Assets(cash=-min_cash)
            new.append(Assets_snapshot(x, h.ss_date))
        self.history = new

    def out(self):
        for h in self.history:
            print(h)
    
    @property
    def date_ticks(self):
        return [(h.ss_date-datetime.date(2020,1,1)).days for h in self.history]

    @property
    def cash_ticks(self):
        return [h.assets.cash for h in self.history]

    @property
    def stock_ticks(self):
        return [h.assets.stocks for h in self.history]

    @property
    def assets_ticks(self):
        return [h.assets.sum for h in self.history]


class HoldPool():
    # 保持しているデータを管理する。
    def __init__(self):
        self.hold = []
        self.history = []
        self.assets = Assets()
    def add(self, d:Deal) -> Assets:
        # 保持に加える
        if d.is_buy_stock:
            # self.hold.append(d)
            return self.__add_buy_stock(d)
        elif d.is_sell_stock:
            return self.__add_sell_stock(d)
        else:
            #v = d.quantity*d.value
            return Assets()

    def __add_buy_stock(self,d:Deal):
        '''FIXME:ダサすぎる''' 
        result = Assets()
        for t,h in enumerate(self.hold):
            if h.brandcode != d.brandcode or not h.is_sell_stock:
                continue
            if h.quantity >= d.quantity:
                his = History(d.brandname,
                            d.brandcode,
                            d.quantity,
                            h.date,
                            h.value,
                            d.date,
                            d.value)
                self.history.append(his)
                
                self.hold[t].quantity -= d.quantity
                result = result + Assets(stocks=+d.quantity*h.value, cash=-d.quantity*d.value)
                d.quantity = 0
                break
            else:
                his = History(d.brandname,
                            d.brandcode,
                            h.quantity,
                            h.date,
                            h.value,
                            d.date,
                            d.value)
                self.history.append(his)

                d.quantity -= h.quantity
                result = result + Assets(stocks=+h.quantity*h.value, cash=-h.quantity*d.value)
                self.hold[t].quantity = 0

        self.hold.append(d)
        result = result + Assets(stocks=+d.quantity*d.value, cash=-d.quantity*d.value)
        new_hold = []
        for h in self.hold:
            if h.quantity > 0:
                new_hold.append(h)
        self.hold = new_hold
        return result

    def __add_sell_stock(self,d:Deal):
        '''FIXME:ダサすぎる''' 
        result = Assets()
        for t,h in enumerate(self.hold):
            if h.brandcode != d.brandcode or not h.is_buy_stock:
                continue
            if h.quantity >= d.quantity:
                his = History(d.brandname,
                            d.brandcode,
                            d.quantity,
                            h.date,
                            h.value,
                            d.date,
                            d.value)
                self.history.append(his)
                
                self.hold[t].quantity -= d.quantity
                result = result + Assets(stocks=-d.quantity*h.value, cash=+d.quantity*d.value)
                d.quantity = 0
                break
            else:
                his = History(d.brandname,
                            d.brandcode,
                            h.quantity,
                            h.date,
                            h.value,
                            d.date,
                            d.value)
                self.history.append(his)

                d.quantity -= h.quantity
                result = result + Assets(stocks=-h.quantity*h.value, cash=+h.quantity*d.value)
                self.hold[t].quantity = 0

        self.hold.append(d)
        result = result + Assets(stocks=-d.quantity*d.value, cash=+d.quantity*d.value)
        new_hold = []
        for h in self.hold:
            if h.quantity > 0:
                new_hold.append(h)
        self.hold = new_hold
        return result

if  __name__ == "__main__":
    print(Assets(0,0,0)+Assets(1,1,-1))
    try:
        ds = Deals(FILENAME)
    except Exception as e:
        print(f"Deals{e}")
    ds.assign()
    try:
        pass
    except Exception as e:
        print(f"assign{e}")
    try:
        ds.output()
    except Exception as e:
        print(f"output:{e}")

    #for d in ds.deals:
    #    print(d.__dict__)
    # print(d.__dict__)
    #input("何かキーを押すと終了します")