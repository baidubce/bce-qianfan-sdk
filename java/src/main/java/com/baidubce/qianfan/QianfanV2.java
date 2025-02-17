package com.baidubce.qianfan;

import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.core.auth.Auth;
import com.baidubce.qianfan.core.builder.ChatV2Builder;
import com.baidubce.qianfan.core.builder.EmbeddingV2Builder;
import com.baidubce.qianfan.core.builder.RerankV2Builder;
import com.baidubce.qianfan.model.chat.v2.request.RequestV2;
import com.baidubce.qianfan.model.chat.v2.response.ResponseV2;
import com.baidubce.qianfan.model.chat.v2.response.StreamResponseV2;
import com.baidubce.qianfan.model.embedding.v2.EmbeddingRequestV2;
import com.baidubce.qianfan.model.embedding.v2.EmbeddingResponseV2;
import com.baidubce.qianfan.model.rerank.v2.RerankRequestV2;
import com.baidubce.qianfan.model.rerank.v2.RerankResponseV2;

public class QianfanV2 extends QianfanBase {

    public QianfanV2() {
        this.client = new QianfanClient();
    }

    public QianfanV2(String accessKey, String secretKey) {
        this.client = new QianfanClient(Auth.TYPE_V2, accessKey, secretKey);
    }

    QianfanV2(QianfanClient client) {
        this.client = client;
    }

    public ChatV2Builder chatCompletion() {
        return new ChatV2Builder(this);
    }

    public ResponseV2 chatCompletion(RequestV2 request) {
        return request(request, ResponseV2.class);
    }

    public StreamIterator<StreamResponseV2> chatCompletionStream(RequestV2 request) {
        request.setStream(true);
        return requestStream(request, StreamResponseV2.class);
    }

    public EmbeddingV2Builder embedding() {
        return new EmbeddingV2Builder(this);
    }

    public EmbeddingResponseV2 embedding(EmbeddingRequestV2 request) {
        return request(request, EmbeddingResponseV2.class);
    }

    public RerankV2Builder rerank() {
        return new RerankV2Builder(this);
    }

    public RerankResponseV2 rerank(RerankRequestV2 request) {
        return request(request, RerankResponseV2.class);
    }
}
