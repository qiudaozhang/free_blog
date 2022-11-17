[TOC]



预计要完成的内容

1. 单均线交易
2. 双均线交易
3. 均线+bias交易
4. 均线+裸K组合交易
5. ...







## 初步尝试

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



| 优点           | 缺陷                                                         |
| -------------- | ------------------------------------------------------------ |
| 解决了方向问题 | 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss |
|                | 可能是恰好当前一个ma之上，  实际上具体的大部分都是ma之下，可能恰好做反了 |
|                | 一个K的反转里面out，几乎时刻都在open close，惨死             |



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



| 优点                                       | 缺陷                                                         |
| ------------------------------------------ | ------------------------------------------------------------ |
| 要求连续几个都处于之上或之下，减少了偶然性 | 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss |
|                                            | 可能是恰好当前一个ma之上，  实际上具体的大部分都是ma之下，可能恰好做反了 |
|                                            | 一个K的反转里面out，几乎时刻都在open close，惨死             |












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



- 完善点：

  - win loss out都需要满足至少1%的振幅，这样可以避免无穷的open close

- 固有缺陷：

  - 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss

  - 如果出现单K反转超过1%，并且后续又继续延续trend，可能会白亏






| 优点                                                         | 缺陷                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| win loss out都需要满足至少1%的振幅，这样可以避免无穷的open close | 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss |
|                                                              | 如果出现单K反转超过1%，并且后续又继续延续trend，可能会白亏   |







### v4

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
            if 0 < k['bias_rate'] < 2 / 1000:
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -2 / 1000:
                self.open_short()
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            # update here
            if apm_rate > 10/100:
                self.close()
                return

            if abs(k['bias_rate']) > 5/100:
                self.close()
                return 

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

- 完善点：
  - 引入bias进行偏移的限定，避免在bias值超大的时候还参与
- 固有缺陷：
  - 如果出现单K反转超过1%，并且后续又继续延续trend，可能会白亏



根据测试结果，bias_rate 如果不想限制太死，参考值为不宜小于3/1000

| 优点                                                 | 缺陷                                                       |
| ---------------------------------------------------- | ---------------------------------------------------------- |
| 引入bias进行偏移的限定，避免在bias值超大的时候还参与 | 如果出现单K反转超过1%，并且后续又继续延续trend，可能会白亏 |







### v5

接下来我们实装test观察

2022-11-17 10:13

ETHUSDT 开多,成交价格 1217.11



```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 10 / 100:
                self.close()
                return

            if abs(k['bias_rate']) > 5 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        # logger.info(f"loss {self.get_unrealize_profit()}")
        super().handle_loss_out()
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']

        lp_key = self.create_key('loss_price')
        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

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





| 优点                                  | 缺陷                     |
| ------------------------------------- | ------------------------ |
| 多空都根据简单的20K计算了一个防守价格 | bias验证可能失守直接破掉 |



此时计算的loss price 为1187

然后我们分析发现当前bias_rate超过1的都不多，所以再调整下



【v5-y1】

```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        super().handle_loss_out()
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']

        lp_key = self.create_key('loss_price')
        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

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



思考，对于连续6k击破原有的ma的是否要选择放弃呢，或者7k，根据这个思路我们改一下



【v5-y2】

```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        # logger.info(f"loss {self.get_unrealize_profit()}")
        super().handle_loss_out()
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

        if self.has_order:
            if apm_rate > 1 / 100:
                self.reverse_break_close()
                return
            if self.is_now_long():
                if self.df[-7:]['bias_rate'].lt(0).all():
                    self.close()
                    return
            if self.is_now_short():
                if self.df[-7:]['bias_rate'].gt(0).all():
                    self.close()
                    return

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



还有问题吗？

插针的超级急速运动没有解决

| 改进                                                         | 缺陷                                                       |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| 如果超大损失，直接close，能避免再大的loss，虽然之前已经处理了<br />loss_price，但是如果算出来的这个值距离很远，很可能就已经爆仓<br />了，所以这一步有必要处理 | 但如果插完之后里面回到原有水平就白亏，所以这是个两难的问题 |







【v5-y3】

```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        logger.info(f"loss {self.get_unrealize_profit():.4f}")
        super().handle_loss_out()
        # 如果过大损失，直接离场
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

        if self.has_order:
            if apm_rate > 1 / 100:
                self.reverse_break_close()
                return
            if self.is_now_long():
                if self.df[-7:]['bias_rate'].lt(0).all():
                    self.close()
                    return
            if self.is_now_short():
                if self.df[-7:]['bias_rate'].gt(0).all():
                    self.close()
                    return

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



还有问题吗，其实也有，如果是很小的震动，即使以连续反向突破7k作为平仓依据也不太好，最好还是加上1%的振幅





【v5-y4】



```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        logger.info(f"loss {self.get_unrealize_profit():.4f}")
        super().handle_loss_out()
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

        if self.has_order:
            if apm_rate > 1 / 100:
                self.reverse_break_close()
                if self.has_order:
                    if self.is_now_long():
                        if self.df[-7:]['bias_rate'].lt(0).all():
                            self.close()
                            return
                    if self.is_now_short():
                        if self.df[-7:]['bias_rate'].gt(0).all():
                            self.close()
                            return

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



到此，我们可以梳理下问题



| 问题           | 是否解决 | 解决办法                                                   |
| -------------- | -------- | ---------------------------------------------------------- |
| 方向           | 是       | 连续的ma的单边性                                           |
| 入场价格       | 是       | bias接近率                                                 |
| 止损           | 是       | 计算止损、最大止损、反向连续突破性止损                     |
| 止盈           | 是       | 最大止盈、bias偏移过大止盈、较长利润之后的连续反向突破止盈 |
| 频率问题       | 否       | 根选择的周期关系很大，15m 1h 4h...                         |
| 震荡性反复亏损 | 否       | 如果单边性不强，这个问题现有逻辑无法解决                   |
| 恶意插针       | 否       | 这个问题无法预测，无好的解决办法                           |







## 频率问题处理



经过研究发现即使是15m的运动幅度50k也很容易接近4%，所以我们的运行逻辑，如果1%这种波动就直接close，会造成极大的交易频率问题，当然放大了允许的亏损，更好的方式，应该是只保留的之前计算是loss_price，和插针保护即可，其它的应该移除。但是亏损可能接近4%，这样允许的杠杆就必须降低，简易不超过8，5x比较合适。



【pro-1】



```python
import talib
from loguru import logger

from db.fkline import find_csv
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
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
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        logger.info(f"loss {self.get_pure_win():.4f}")
        logger.info(apm_rate)
        super().handle_loss_out()
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return

        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

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





允许的亏损变大了，在这一步前更重要的就是入场的方向和价位需要更加谨慎了，否则就要承受较大的亏损，另外承担较大亏损的同时也得博取更大利润才行。





## 双MA的引入



单个的缺点在于无法比较直观的感受的行进中的程度，刚开始还是要结束？



```python
import talib
from loguru import logger

from db.fkline import find_csv
from findex import ema
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)
        df['ma2'] = talib.SMA(df['c'], 43)
        df['bias'] = df['c'] - df['ma']
        df['bias_rate'] = df['bias'] / df['ma']
        df['bias2'] = df['c'] - df['ma']
        df['bias2_rate'] = df['bias2'] / df['ma2']
        self.df = df
        k = self.df.iloc[-1]
        self.k = k
        self.gp = ema.gold_pos_v2(df, 'ma', 'ma2')
        self.dp = ema.dead_pos_v2(df, 'ma', 'ma2')
        logger.info(f"gp {self.gp} dp {self.dp}")

    def handle_in(self):
        k = self.k
        df = self.df
        sdf = df[-5:]
        bias_closer = 2 / 1000
        if sdf['bias_rate'].gt(0).all():
            logger.info(k['bias_rate'])
            if 0 < k['bias_rate'] < bias_closer:
                # logger.info('may long')
                self.open_long()
                return
        if sdf['bias_rate'].lt(0).all():
            if 0 > k['bias_rate'] > -bias_closer:
                self.open_short()
                # logger.info('may short')
                return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        logger.info(f"loss {self.get_pure_win():.4f}")
        logger.info(apm_rate)
        super().handle_loss_out()
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return

        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

        # if self.has_order:
        #     if apm_rate > 2 / 100:
        #         self.reverse_break_close()
        #         if self.has_order:
        #             if self.is_now_long():
        #                 if self.df[-7:]['bias_rate'].lt(0).all():
        #                     self.close()
        #                     return
        #             if self.is_now_short():
        #                 if self.df[-7:]['bias_rate'].gt(0).all():
        #                     self.close()
        #                     return

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



引入了两个ma，且计算了交叉到现在经历的K数量，gp代表金叉，dp代表死叉，为正数才代表该方向成立，数字越大代表交叉得越久。

借助它我们可以用来衡量参与的时机，比如我们限定只在早期才参与，否则不参与



```python
import talib
from loguru import logger

from db.fkline import find_csv
from findex import ema
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)
        df['ma2'] = talib.SMA(df['c'], 43)
        df['bias'] = df['c'] - df['ma']
        df['bias_rate'] = df['bias'] / df['ma']
        df['bias2'] = df['c'] - df['ma']
        df['bias2_rate'] = df['bias2'] / df['ma2']
        self.df = df
        k = self.df.iloc[-1]
        self.k = k
        self.gp = ema.gold_pos_v2(df, 'ma', 'ma2')
        self.dp = ema.dead_pos_v2(df, 'ma', 'ma2')
        logger.info(f"gp {self.gp} dp {self.dp}")

    def handle_in(self):
        k = self.k
        df = self.df
        sdf = df[-5:]
        bias_closer = 2 / 1000
        max_use = 30
        if 0 < self.gp < max_use:
            if sdf['bias_rate'].gt(0).all():
                logger.info(k['bias_rate'])
                if 0 < k['bias_rate'] < bias_closer:
                    self.open_long()
                    return
        if 0 < self.dp < max_use:
            if sdf['bias_rate'].lt(0).all():
                if 0 > k['bias_rate'] > -bias_closer:
                    self.open_short()
                    return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        logger.info(f"loss {self.get_pure_win():.4f}")
        logger.info(apm_rate)
        super().handle_loss_out()
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return

        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

        # if self.has_order:
        #     if apm_rate > 2 / 100:
        #         self.reverse_break_close()
        #         if self.has_order:
        #             if self.is_now_long():
        #                 if self.df[-7:]['bias_rate'].lt(0).all():
        #                     self.close()
        #                     return
        #             if self.is_now_short():
        #                 if self.df[-7:]['bias_rate'].gt(0).all():
        #                     self.close()
        #                     return

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









| 问题           | 是否解决 | 解决办法                                                   |
| -------------- | -------- | ---------------------------------------------------------- |
| 方向           | 是       | 连续的ma的单边性                                           |
| 入场价格       | 是       | bias接近率                                                 |
| 止损           | 是       | 计算止损、最大止损、反向连续突破性止损                     |
| 止盈           | 是       | 最大止盈、bias偏移过大止盈、较长利润之后的连续反向突破止盈 |
| 频率问题       | -        | 双MA的交叉早期限定一定程度解决了这个问题                   |
| 震荡性反复亏损 | -        | 放大了止损，一定程序解决了这个问题                         |
| 恶意插针       | 否       | 这个问题无法预测，无好的解决办法                           |
| 验证无效       | 否       | 交叉后以bias值限定了入场价格，但是也可能直接破掉           |



## 验证无效解决



我们希望验证是有效的，这个怎么作为标准呢，我们假设open long为研究对象

1. 最近的k有靠近ma
2. 不能下破ma2
3. 最近的语义描述为10K
4. 最新的5k和前5k比high high



```python
import talib
from loguru import logger

from db.fkline import find_csv
from findex import ema
from strategy.BaseStrategy import BaseStrategy


class SingleMa(BaseStrategy):

    def __init__(self, _id, uid, s, margin, sid, mode, ext):
        super().__init__(_id, uid, s, margin, sid, mode, ext)
        # 暂时写死
        i = '15m'
        p = 20
        self.i = i  # 为k周期比如4h
        df = find_csv(s, i)
        df['ma'] = talib.SMA(df['c'], p)
        df['ma2'] = talib.SMA(df['c'], 43)
        df['bias'] = df['c'] - df['ma']
        df['bias_rate'] = df['bias'] / df['ma']
        df['bias2'] = df['c'] - df['ma']
        df['bias2_rate'] = df['bias2'] / df['ma2']
        df['ma_gap'] = df['ma'] - df['ma2']
        df['ma_gap_rate'] = df['ma_gap'] / df['ma']
        self.df = df
        k = self.df.iloc[-1]
        self.k = k
        self.gp = ema.gold_pos_v2(df, 'ma', 'ma2')
        self.dp = ema.dead_pos_v2(df, 'ma', 'ma2')
        logger.info(f"gp {self.gp} dp {self.dp}")

    def handle_in(self):
        k = self.k
        df = self.df
        sdf = df[-5:]
        bias_closer = 2 / 1000
        max_use = 80
        df10 = df[-10:]

        if 0 < self.gp < max_use:
            if len(df10[-10:-5].query('bias_rate < 2/1000')) > 0:
                if df10[-5:]['h'].max() > df10[-10:-5]['h'].max():
                    if len(df10.query('bias2_rate < 0')) <= 1:
                        if sdf['bias_rate'].gt(0).all():
                            logger.info(k['bias_rate'])
                            if 0 < k['bias_rate'] < bias_closer * 2:
                                self.open_long()
                                return
        if 0 < self.dp < max_use:
            if len(df10[-10:-5].query('bias_rate > -2/1000')) > 0:
                if df10[-5:]['l'].min() > df10[-10:-5]['l'].min():
                    if sdf['bias_rate'].lt(0).all():
                        if 0 > k['bias_rate'] > -bias_closer * 2:
                            self.open_short()
                            return

    def handle_win_out(self):
        k = self.k
        super().handle_win_out()
        logger.info(f"win {self.get_unrealize_profit()}")
        if self.has_order:
            super().handle_loss_out()
            apm = abs(self.get_price_move())
            apm_rate = apm / k['c']
            if apm_rate > 3 / 100:
                self.close()
                return
            if abs(k['bias_rate']) > 1 / 100:
                self.close()
                return
            if self.has_order:
                if apm_rate > 1 / 100:
                    self.reverse_break_close()

    def handle_loss_out(self):
        k = self.k
        c = k['c']
        apm = abs(self.get_price_move())
        apm_rate = apm / k['c']
        lp_key = self.create_key('loss_price')
        # logger.info(f"loss {self.get_pure_win():.4f}")
        # logger.info(apm_rate)
        logger.info(k['ma_gap'])
        logger.info(k['ma_gap_rate'])
        super().handle_loss_out()
        if self.get_unrealize_profit_rate() < -60 / 100:
            self.close()
            return

        if not self.have_key(lp_key):
            if self.is_now_long():
                self.save_loss_price(self.df[-20:]['l'].min() - c / 100)
            if self.is_now_short():
                self.save_loss_price(self.df[-20:]['h'].max() + c / 100)

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

最终允许开单的一行bias_rate限制放大两倍是原因是，当验证过后，可能次数的bias_rate会比较大，如果不放大可能无法open。









| 问题           | 是否解决 | 解决办法                                                   |
| -------------- | -------- | ---------------------------------------------------------- |
| 方向           | 是       | 连续的ma的单边性                                           |
| 入场价格       | 是       | bias接近率                                                 |
| 止损           | 是       | 计算止损、最大止损、反向连续突破性止损                     |
| 止盈           | 是       | 最大止盈、bias偏移过大止盈、较长利润之后的连续反向突破止盈 |
| 频率问题       | 60%      | 验证技术可以优化                                           |
| 震荡性反复亏损 | 60%      | 验证技术可以优化                                           |
| 恶意插针       | 否       | 这个问题无法预测，无好的解决办法                           |
| 验证无效       | 是       | 以最新的10进行裸K判定以及双bias的破坏保护                  |

 

我们通过验证的有效性可以规避较大的入场风险，当然需要付出的代价是相对保守的入场价格



