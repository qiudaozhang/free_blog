文档
 
https://github.com/wechatpay-apiv3/wechatpay-java


 


# native 支付



```java
package com.qiudaozhang.wxpay.config;
import com.wechat.pay.java.core.Config;
import com.wechat.pay.java.core.RSAConfig;
import com.wechat.pay.java.service.payments.nativepay.model.Amount;
import com.wechat.pay.java.service.payments.nativepay.NativePayService;
import com.wechat.pay.java.service.payments.nativepay.model.PrepayRequest;
import com.wechat.pay.java.service.payments.nativepay.model.PrepayResponse;
import org.apache.commons.lang3.RandomStringUtils;
import org.checkerframework.checker.units.qual.A;

public class WxPay1 {

    public static void main(String[] args) {

        String mchId= "xx";
        String appid= "xx";
        Config config =
                new RSAConfig.Builder()
                        .merchantId(mchId)
                        .privateKeyFromPath("F:\\coding_net\\wxpay\\src\\main\\resources\\apiclient_key.pem")
                        .merchantSerialNumber("xxxx")
                        .wechatPayCertificatesFromPath("F:\\coding_net\\wxpay\\src\\main\\resources\\apiclient_cert.pem")
                        .build();

        NativePayService nativePayService = new NativePayService.Builder().config(config).build();
        PrepayRequest request = new PrepayRequest();
        Amount amount = new Amount();
        amount.setTotal(100);
        request.setAmount(amount);
        request.setAppid(appid);
        request.setMchid(mchId);
        request.setDescription("测试交易");
        request.setNotifyUrl("https://xxxxx.zicp.fun/notify");
        request.setOutTradeNo(RandomStringUtils.randomAlphanumeric(32));
        PrepayResponse response = nativePayService.prepay(request);
        System.out.println(response.getCodeUrl());
    }
}
```