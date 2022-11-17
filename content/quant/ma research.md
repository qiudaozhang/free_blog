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

 

- 入场离场： 主要使用是否在ma之上则定方向

- 固有缺陷
  - 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss
  - 可能是恰好当前一个ma之上，  实际上具体的大部分都是ma之下，可能恰好做反了
  - 一个K的反转里面out，几乎时刻都在open close，惨死



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



- 完善点
  - 要求连续几个都处于之上或之下，减少了偶然性

- 固有缺陷
  - 不知实际的高低，比如ma之上超高的位置open long，很容易引起巨大是loss
  - 可能是恰好当前一个ma之上，  实际上具体的大部分都是ma之下，可能恰好做反了
  - 一个K的反转里面out，几乎时刻都在open close，惨死


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





- 完善点：
  - 多空都根据简单的20K计算了一个防守价格
- 固有缺陷：
  - bias验证可能失手直接破掉



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

- 改进：
  - 如果超大损失，直接close，能避免再大的loss，虽然之前已经处理了loss_price，但是如果算出来的这个值距离很远，很可能就已经爆仓了，所以这一步有必要处理

- 缺陷：
  - 但如果插完之后里面回到原有水平就白亏，所以这是个两难的问题，







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























