预计要完成的内容

1. 单均线交易
2. 双均线交易
3. 均线+bias交易
4. 均线+裸K组合交易
5. ...





## single ma 

### v1

```python
import talib

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        e = self.ext
        i = e['i']
        p = int(e['p'])
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)  # p 为MA的周期 比如20
        self.df = df
        k = self.df.iloc[-1]
        self.k = k 

    def handle_in(self):
        k = self.k
        if k['ma'] > 0:
            self.open_long()
        else:
            self.open_short()

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        if self.has_order:
            self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k

        super().handle_loss_out()
        if self.has_order:
            self.reverse_break_close()

    def reverse_break_close(self):
        k = self.k
        if self.is_now_long():
            if k['c'] < 0:
                self.close()
                return
        if self.is_now_short():
            if k['c'] > 0:
                self.close()
                return
```



模型缺陷：

todo





### v2



```python
import talib

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        e = self.ext
        i = e['i']
        p = int(e['p'])
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)  # p 为MA的周期 比如20
        df['bias'] = df['c'] - df['ma']  # bias 描述和ma的差值
        df['bias_rate'] = df['bias'] / df['ma']  # 百分比可以得到一个偏移率
        self.df = df
        k = self.df.iloc[-1]
        self.k = k

    def handle_in(self):
        k = self.k
        df = self.df
        sdf = df[-5:]
        if sdf['bias_rate'].gt(0).all():
            self.open_long()
            return
        if sdf['bias_rate'].lt(0).all():
            self.open_short()
            return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        if self.has_order:
            self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        super().handle_loss_out()
        if self.has_order:
            self.reverse_break_close()

    def reverse_break_close(self):
        k = self.k
        if self.is_now_long():
            if k['c'] < 0:
                self.close()
                return
        if self.is_now_short():
            if k['c'] > 0:
                self.close()
                return
```





提升：

缺陷：




### v3

```python
import talib

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        e = self.ext
        i = e['i']
        p = int(e['p'])
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)  # p 为MA的周期 比如20
        df['bias'] = df['c'] - df['ma']  # bias 描述和ma的差值
        df['bias_rate'] = df['bias'] / df['ma']  # 百分比可以得到一个偏移率
        self.df = df
        k = self.df.iloc[-1]
        self.k = k

    def handle_in(self):
        k = self.k
        df = self.df
        sdf = df[-5:]
        if sdf['bias_rate'].gt(0).all():
            self.open_long()
            return
        if sdf['bias_rate'].lt(0).all():
            self.open_short()
            return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']

            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        super().handle_loss_out()
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']

        if self.has_order:
            if apm_rate > 1 / 100:
                self.reverse_break_close()

    def reverse_break_close(self):
        k = self.k
        if self.is_now_long():
            if k['c'] < 0:
                self.close()
                return
        if self.is_now_short():
            if k['c'] > 0:
                self.close()
                return
```







### v4

