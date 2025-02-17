package com.baidubce.qianfan.model.rerank.v2;

import com.baidubce.qianfan.model.BaseResponse;

import java.util.List;

public class RerankResponseV2 extends BaseResponse<RerankResponseV2> {
    private List<RerankDataV2> results;

    private RerankUsageV2 usage;

    private String model;

    public List<RerankDataV2> getResults() {
        return results;
    }

    public RerankResponseV2 setResults(List<RerankDataV2> results) {
        this.results = results;
        return this;
    }

    public RerankUsageV2 getUsage() {
        return usage;
    }

    public RerankResponseV2 setUsage(RerankUsageV2 usage) {
        this.usage = usage;
        return this;
    }

    public String getModel() {
        return model;
    }

    public RerankResponseV2 setModel(String model) {
        this.model = model;
        return this;
    }
}
