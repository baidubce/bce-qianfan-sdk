package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.QianfanV2;
import com.baidubce.qianfan.model.embedding.v2.EmbeddingRequestV2;
import com.baidubce.qianfan.model.embedding.v2.EmbeddingResponseV2;

import java.util.List;

public class EmbeddingV2Builder extends BaseBuilderV2<EmbeddingV2Builder> {
    private List<String> input;

    private String user;

    public EmbeddingV2Builder() {
        super();
    }

    public EmbeddingV2Builder(QianfanV2 qianfan) {
        super(qianfan);
    }

    public EmbeddingV2Builder input(List<String> input) {
        this.input = input;
        return this;
    }

    public EmbeddingV2Builder user(String user) {
        this.user = user;
        return this;
    }

    public EmbeddingRequestV2 build() {
        return new EmbeddingRequestV2()
                .setInput(input)
                .setModel(super.getModel())
                .setUser(user)
                .setExtraParameters(super.getExtraParameters());
    }

    public EmbeddingResponseV2 execute() {
        return super.getQianfanV2().embedding(build());
    }
}
