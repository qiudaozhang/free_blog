

> 纯技术研究，非真实交易



2022-11-18



## v1

test for eth 4h



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


class B3(BaseTest):

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
        p2 = df[-40:-20]
        p1 = df[-20:]
        p2min = p2['l'].min()
        p1min = p1['l'].min()
        p2max = p2['h'].max()
        p1max = p1['h'].max()
        c = k['c']
        o = k['o']

        sec = df.iloc[-2]
        three = df.iloc[-3]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        limit = 2.7 / 100
        max_use = 2370
        min_bias_rate = abs(nake.min_dif(sec['ma'], sec['h'], sec['l'])) / sec['ma']

        macd_gp = macd.gold_pos(df_pre)
        macd_dp = macd.dead_pos(df_pre)
        if 0 < gp < max_use:
            if min_bias_rate < limit and macd_gp > 0 and sec['macd'] > 0:
                # sub = df_pre[-(gp-1):]
                # if len(sub) > 3:
                #     if len(sub.query('bias2_rate < 0')) > 0:
                #         return
                # if min_bias_rate < limit and sec['yy'] and sec['l'] > three['l'] \
                #         and sec['h'] > three['h']:
                # if p1min > p2min:
                #     return
                self.buy_long(k['o'])
                return
        if 0 < dp < max_use:
            # sub = df_pre[-(dp - 1):]
            # if len(sub) > 3:
            #     if len(sub.query('bias2_rate > 0')) > 0:
            #         return
            if min_bias_rate < limit and macd_dp > 0 and sec['macd'] < 0:
                # if min_bias_rate < limit and not sec['yy'] and sec['h'] < three['h'] \
                #             and sec['l'] < three['l']:
                # if p1max < p2max:
                #     return
                self.buy_short(k['o'])
                return

    def handle_win(self):
        k = self.now_k
        o = k['o']
        df = self.df[:-1]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        p3 = df[-5:-1]

        max_win = 200 / 100

        if self.open_win() > 30 / 100:
            if self.stop_price is None:
                if self.is_long():
                    self.stop_price = o - o * 5 / 100
                if self.is_short():
                    self.stop_price = o + o * 5 / 100

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
            self.close_profit(max_win, 'max_win')
            return
        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'ma decross')
                return

        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'ma decross')
                return

    def handle_loss(self):
        k = self.now_k
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        # loss = -4 / 10
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')
            return

        if self.open_win() < -1.5/10:
            if self.is_long():
                if dp > 0:
                    self.close(k['o'], 'ma decross')
                    return
            if self.is_short():
                if gp > 0:
                    self.close(k['o'], 'ma decross')
                    return

    def handle_mid(self):
        # 卡中间的不处理
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')


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

print(len(df_total))
df = df_total
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

bt = B3(df[100:], all, margin, 3, 5 / 10000)
bt.run()
print(
    f"balance: {bt.balance:.2f} times {bt.entry_times} fee {bt.total_commission:.2f} "
    f"total balance {all}  margin {margin} win times  {bt.win_times} loss times {bt.loss_times}  ")
t3 = tu.now_ms()
print((t3 - t2) / 1000)
output = pd.DataFrame(bt.orders)
output.to_csv('record.csv')

```



eth 4h test

> balance: 12165.09 times 73 fee 217.50 total balance 3000  margin 1000 win times  34 loss times 38  



btc 4h test

> balance: 4678.92 times 68 fee 202.50 total balance 3000  margin 1000 win times  30 loss times 37  



bnb 4h test

> balance: 6242.63 times 64 fee 190.50 total balance 3000  margin 1000 win times  33 loss times 30 



ada 4h test

> balance: 10744.30 times 81 fee 243.00 total balance 3000  margin 1000 win times  37 loss times 44  



dot 4h test

> balance: 7409.15 times 65 fee 193.50 total balance 3000  margin 1000 win times  31 loss times 33  



ltc 4h test

> balance: 999.99 times 74 fee 222.00 total balance 3000  margin 1000 win times  33 loss times 41  





主要处理获利后停损，不能倒亏，还有必须有一定loss才执行decross close





## v2



如果选择移除基础loss才decross close，看看如何

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


class B3(BaseTest):

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
        p2 = df[-40:-20]
        p1 = df[-20:]
        p2min = p2['l'].min()
        p1min = p1['l'].min()
        p2max = p2['h'].max()
        p1max = p1['h'].max()
        c = k['c']
        o = k['o']

        sec = df.iloc[-2]
        three = df.iloc[-3]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        limit = 2.7 / 100
        max_use = 2370
        min_bias_rate = abs(nake.min_dif(sec['ma'], sec['h'], sec['l'])) / sec['ma']

        macd_gp = macd.gold_pos(df_pre)
        macd_dp = macd.dead_pos(df_pre)
        if 0 < gp < max_use:
            if min_bias_rate < limit and macd_gp > 0 and sec['macd'] > 0:
                # sub = df_pre[-(gp-1):]
                # if len(sub) > 3:
                #     if len(sub.query('bias2_rate < 0')) > 0:
                #         return
                # if min_bias_rate < limit and sec['yy'] and sec['l'] > three['l'] \
                #         and sec['h'] > three['h']:
                # if p1min > p2min:
                #     return
                self.buy_long(k['o'])
                return
        if 0 < dp < max_use:
            # sub = df_pre[-(dp - 1):]
            # if len(sub) > 3:
            #     if len(sub.query('bias2_rate > 0')) > 0:
            #         return
            if min_bias_rate < limit and macd_dp > 0 and sec['macd'] < 0:
                # if min_bias_rate < limit and not sec['yy'] and sec['h'] < three['h'] \
                #             and sec['l'] < three['l']:
                # if p1max < p2max:
                #     return
                self.buy_short(k['o'])
                return

    def handle_win(self):
        k = self.now_k
        o = k['o']
        df = self.df[:-1]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        p3 = df[-5:-1]

        max_win = 200 / 100

        if self.open_win() > 30 / 100:
            if self.stop_price is None:
                if self.is_long():
                    self.stop_price = o - o * 5 / 100
                if self.is_short():
                    self.stop_price = o + o * 5 / 100

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
            self.close_profit(max_win, 'max_win')
            return
        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'ma decross')
                return

        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'ma decross')
                return

    def handle_loss(self):
        k = self.now_k
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        # loss = -4 / 10
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')
            return

        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'ma decross')
                return
        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'ma decross')
                return

    def handle_mid(self):
        # 卡中间的不处理
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')


from util import timeutil as tu

# path_dir = 'E:\\coding\\coin_data\\1d'
path_dir = 'E:\\coding\\coin_data\\ltc\\4h'
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

print(len(df_total))
df = df_total
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

bt = B3(df[100:], all, margin, 3, 5 / 10000)
bt.run()
print(
    f"balance: {bt.balance:.2f} times {bt.entry_times} fee {bt.total_commission:.2f} "
    f"total balance {all}  margin {margin} win times  {bt.win_times} loss times {bt.loss_times}  ")
t3 = tu.now_ms()
print((t3 - t2) / 1000)
output = pd.DataFrame(bt.orders)
output.to_csv('record.csv')
```



btc 4h

> balance: 5940.40 times 111 fee 331.50 total balance 3000  margin 1000 win times  27 loss times 83  



eth 4h

> balance: 10752.36 times 107 fee 319.50 total balance 3000  margin 1000 win times  36 loss times 70  



bnb 4h

> balance: 8081.23 times 87 fee 259.50 total balance 3000  margin 1000 win times  34 loss times 52  



ada 4h

> balance: 12813.68 times 108 fee 324.00 total balance 3000  margin 1000 win times  38 loss times 70  



dot 4h

>balance: 8026.73 times 92 fee 274.50 total balance 3000  margin 1000 win times  31 loss times 60  

ltc 4h 

> balance: 4706.84 times 117 fee 349.50 total balance 3000  margin 1000 win times  39 loss times 77  



eth的测试记录csv文件 

[记录](https://qiudaozhang.lanzouy.com/inIWJ0g7rv0h)



翻译逻辑

```
ema两个周期
34 
73

杠杆：3x
最大止损：40%
最大止盈：200%
手续费： 5/10000， 开仓平仓都扣除


入场规则：（假设多，空反过来）
如果交叉，且前k的ma最小靠近率小于1.7/100
则当前K开盘就以开盘价格做多

离场规则
   优先执行是否满足最大止损，如果满足以最大止损平仓离场
   
   处于损失的情况下：
   		如果触发最大止损执行
   		如果ma反向交叉执行
   
	获利的情况下：
		如果利润超过了12%，进行停损保护，以开盘价格回撤3%作为最后防守，打破平仓
		如果满足最大止盈，执行
		如果ma反向交叉执行
	

```





## v3

作为一个备份版本



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

class B3(BaseTest):
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
        p2 = df[-40:-20]
        p1 = df[-20:]
        sec = df.iloc[-2]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        limit = 2.7 / 100
        max_use = 2370
        min_bias_rate = abs(nake.min_dif(sec['ma'], sec['h'], sec['l'])) / sec['ma']

        macd_gp = macd.gold_pos(df_pre)
        macd_dp = macd.dead_pos(df_pre)
        if 0 < gp < max_use:
            if min_bias_rate < limit and macd_gp > 0 and sec['macd'] > 0:
                self.buy_long(k['o'])
                return
        if 0 < dp < max_use:
            if min_bias_rate < limit and macd_dp > 0 and sec['macd'] < 0:
                self.buy_short(k['o'])
                return

    def handle_win(self):
        k = self.now_k
        o = k['o']
        df = self.df[:-1]
        df_pre = df[:-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        p3 = df[-5:-1]

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
            self.close_profit(max_win, 'max_win')
            return
        if self.is_long():
            if dp > 0:
                self.close(k['o'], 'ma decross')
                return

        if self.is_short():
            if gp > 0:
                self.close(k['o'], 'ma decross')
                return

    def handle_loss(self):
        k = self.now_k
        o = k['o']
        df_pre = df[:-1]
        sec = df.iloc[-1]
        gp = ema.gold_pos_v2(df_pre, 'ma', 'ma2')
        dp = ema.dead_pos_v2(df_pre, 'ma', 'ma2')
        # loss = -4 / 10
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')
            return

        if self.is_long():

            if self.buy_k < kk:
                if sec['bias2_rate'] < loss73:
                    self.close(o, '73击破损失')
                    return
            if dp > 0:
                self.close(k['o'], 'ma decross')
                return
        if self.is_short():
            if self.buy_k < kk:
                if sec['bias2_rate'] > -loss73:
                    self.close(o, '73击破损失')
                    return
            if gp > 0:
                self.close(k['o'], 'ma decross')
                return

    def handle_mid(self):
        # 卡中间的不处理
        if self.max_loss() < max_loss_v:
            self.close_profit(max_loss_v, 'max loss')


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
# df = df[4500:]
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

bt = B3(df[100:], all, margin, 3, 5 / 10000)
bt.run()
print(
    f"balance: {bt.balance:.2f} times {bt.entry_times} fee {bt.total_commission:.2f} "
    f"total balance {all}  margin {margin} win times  {bt.win_times} loss times {bt.loss_times}  ")
t3 = tu.now_ms()
print((t3 - t2) / 1000)
output = pd.DataFrame(bt.orders)
output.to_csv('record.csv')

```

