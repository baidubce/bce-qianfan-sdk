package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.plugin.PluginResponse;

/**
 * 本示例实现了Plugin调用流程
 */
public class PluginExample {
    public static void main(String[] args) {
        chatOcr();
    }

    private static void chatOcr() {
        Qianfan qianfan = new Qianfan();
        PluginResponse response = qianfan.plugin()
                // 请前往千帆大模型平台控制台->插件编排->配置插件应用服务
                // 配置完成后进行上线，并进入详情页获取服务endpoint
                // 示例: https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/endpoint/
                .endpoint("endpoint")
                // 智慧图问场景通过fileurl传入图片
                .fileurl("https://www.baidu.com/img/flexible/logo/pc/result@2.png")
                .query("这个图片是什么")
                .execute();
        System.out.println(response.getResult());
    }
}
