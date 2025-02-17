package com.baidubce.qianfan.model.embedding.v2;

import com.baidubce.qianfan.model.BaseResponse;

import java.util.List;

public class EmbeddingResponseV2 extends BaseResponse<EmbeddingResponseV2> {
    private String model;

    private List<EmbeddingDataV2> data;

    private EmbeddingUsageV2 usage;

    public String getModel() {
        return model;
    }

    public EmbeddingResponseV2 setModel(String model) {
        this.model = model;
        return this;
    }

    public List<EmbeddingDataV2> getData() {
        return data;
    }

    public EmbeddingResponseV2 setData(List<EmbeddingDataV2> data) {
        this.data = data;
        return this;
    }

    public EmbeddingUsageV2 getUsage() {
        return usage;
    }

    public EmbeddingResponseV2 setUsage(EmbeddingUsageV2 usage) {
        this.usage = usage;
        return this;
    }
}
