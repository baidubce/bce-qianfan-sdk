package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.rerank.RerankResponse;

import java.util.ArrayList;
import java.util.List;

/**
 * 本示例实现了Reranker调用流程，对于给定的Query和文档列表进行重排序，将更相关的文档排在前面
 */
public class RerankExample {
    public static void main(String[] args) {
        List<String> documents = new ArrayList<>();
        documents.add("上海位于中国东部海岸线的中心，长江三角洲最东部。");
        documents.add("上海现在的温度是27度。");
        documents.add("深圳现在的温度是29度。");

        RerankResponse response = new Qianfan().rerank()
                .query("上海现在气温多少？")
                .documents(documents)
                .execute();
        response.getResults().forEach(data -> {
            System.out.println(data.getDocument());
            System.out.println(data.getRelevanceScore());
        });
    }
}
