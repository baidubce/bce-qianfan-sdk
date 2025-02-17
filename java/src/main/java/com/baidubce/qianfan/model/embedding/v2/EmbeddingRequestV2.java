package com.baidubce.qianfan.model.embedding.v2;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class EmbeddingRequestV2 extends BaseRequest<EmbeddingRequestV2> {
    private List<String> input;

    private String user;

    @Override
    public String getType() {
        return ModelType.EMBEDDINGS;
    }

    public List<String> getInput() {
        return input;
    }

    public EmbeddingRequestV2 setInput(List<String> input) {
        this.input = input;
        return this;
    }

    public String getUser() {
        return user;
    }

    public EmbeddingRequestV2 setUser(String user) {
        this.user = user;
        return this;
    }
}
