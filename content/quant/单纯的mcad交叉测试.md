> 纯技术研究，非真实交易



2022-11-18









```python
import os
import sys

import pandas as pd
import talib

from daotest.BaseTest import BaseTest
from findex import nake, ema, macd

pd.set_option('display.max_columns', 5000000)
# 显示所有行
pd.set_option('display.max_rows', 5000000)
# 加长宽度
pd.set_option('display.width', 500000)

LONG = 'LONG'
SHORT = 'SHORT'
# -5/10 now balance 10308.02 total times 66 total fee 196.50    total balance 3000  margin 1000
# -4/10 now balance 10408.02 total times 66 total fee 196.50    total balance 3000  margin 1000   win times  19 loss times 46


max_loss_v = -4 / 10
kk = 20
loss73 = -2/100
max_win = 1.5

class B3_1(BaseTest):
    def __init__(self, data, balance, margin, leverage, commission):
        super().__init__(data, balance, margin, leverage, commission)

    def close_try(self):
        pass

    def next(self):

        super().next()

    def entry(self):
        if len(self.df) < 100:
            return
        k = self.now_k
        df = self.df
        o = k['o']
        sec = df.iloc[-2]
        df_pre = df[:-1]
        max_use = 10
        gp = macd.gold_pos(df_pre)
        dp = macd.dead_pos(df_pre)
        if 0 < gp < max_use:
            self.buy_long(o)
            return
        if 0 < dp < max_use:
            self.buy_short(o)
            return

    def handle_win(self):
        k = self.now_k
        o = k['o']
        df = self.df[:-1]
        df_pre = df[:-1]
        gp = macd.gold_pos(df_pre)
        dp = macd.dead_pos(df_pre)
        sec = df_pre.iloc[-1]

        if self.open_win() > 12 / 100:
            if self.stop_price is None:
                if self.is_long():
                    self.stop_price = o - o * 3 / 100
                if self.is_short():
                    self.stop_price = o + o * 3 / 100

        if self.stop_price is not None:
            if self.is_long():
                if o < self.stop_price:
                    self.close(o, '停损')
                    return
            if self.is_short():
                if o > self.stop_price:
                    self.close(o, '停损')
                    return

        if self.max_win() > max_win:
            self.close_profit(max_win, '最大赢')
            return
        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'macd decross')
                return

        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'macd decross')
                return

    def handle_loss(self):
        k = self.now_k
        o = k['o']
        df_pre = df[:-1]
        sec = df.iloc[-1]
        gp = macd.gold_pos(df_pre)
        dp = macd.dead_pos(df_pre)
        # loss = -4 / 10
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')
            return
        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'macd decross')
                return
        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'macd decross')
                return

    def handle_mid(self):
        # 卡中间的不处理
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, '最大损')


from util import timeutil as tu

# path_dir = 'E:\\coding\\coin_data\\1d'
path_dir = 'E:\\coding\\coin_data\\eth\\4h'
g = os.walk(path_dir)
slash = "\\"
if sys.platform != "win32":
    slash = "/"
df_total = pd.DataFrame()
for path, dir_list, file_list in g:
    if path == path_dir:
        for f in file_list:
            if f.find(".csv") != -1:
                fp = path + slash + f
                df = pd.read_csv(fp, low_memory=False)
                cs = df.columns
                if cs[0] == "open_time":
                    df = pd.read_csv(fp, low_memory=False, header=0, usecols=[0, 1, 2, 3, 4, 5],
                                     names=['t', 'o', 'h', 'l', 'c', 'v'])
                else:
                    df = pd.read_csv(fp, low_memory=False, header=None, usecols=[0, 1, 2, 3, 4, 5],
                                     names=['t', 'o', 'h', 'l', 'c', 'v'])
                df = df.sort_values('t', ascending=True)
                dt = pd.to_numeric(df['t'])
                df['t'] = dt
                t2 = tu.now_ms()
                h8 = 8 * 60 * 60 * 1000
                df['ts'] = df['t'] + h8
                df['date'] = pd.to_datetime(df['ts'], unit='ms')
                df_total = pd.concat([df_total, df])

df = df_total
# df = df[2000:]
# df = df[4500:]
print(df.iloc[0]['date'])
df = df.sort_values('t', ascending=True)
dt = pd.to_numeric(df['t'])
df['t'] = dt
t2 = tu.now_ms()
h8 = 8 * 60 * 60 * 1000
df['t'] = df['t'] + h8
df['date'] = pd.to_datetime(df['t'], unit='ms')
df = nake.nake_convert(df)
df['ma'] = talib.EMA(df['c'], 34)
df['ma2'] = talib.EMA(df['c'], 73)
df['bias'] = df['c'] - df['ma']
df['bias2'] = df['c'] - df['ma2']
df['l_bias2'] = df['l'] - df['ma2']
df['h_bias2'] = df['h'] - df['ma2']
df['bias_rate'] = df['bias'] / df['ma']
df['bias2_rate'] = df['bias2'] / df['ma2']
df = macd.cal_macd(df)
all = 3000
margin = 1000
fix_win = 130 / 100
fix_loss = -80 / 100

bt = B3_1(df[100:], all, margin, 3, 5 / 10000)
bt.run()
print(
    f"balance: {bt.balance:.2f} times {bt.entry_times} fee {bt.total_commission:.2f} "
    f"total balance {all}  margin {margin} win times  {bt.win_times} loss times {bt.loss_times}  ")
t3 = tu.now_ms()
print((t3 - t2) / 1000)
output = pd.DataFrame(bt.orders)
output.to_csv('record.csv')
```



结果惨不忍睹，纯用这个交叉不可取