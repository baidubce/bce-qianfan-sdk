package com.baidubce.qianfan;

import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.core.auth.Auth;
import com.baidubce.qianfan.core.builder.ChatV2Builder;
import com.baidubce.qianfan.model.chat.v2.request.V2Request;
import com.baidubce.qianfan.model.chat.v2.response.V2Response;
import com.baidubce.qianfan.model.chat.v2.response.V2StreamResponse;

public class QianfanV2 extends QianfanBase {

    public QianfanV2() {
        this.client = new QianfanClient();
    }

    public QianfanV2(String accessKey, String secretKey) {
        this.client = new QianfanClient(Auth.TYPE_V2, accessKey, secretKey);
    }

    public QianfanV2(QianfanClient client) {
        this.client = client;
    }

    public ChatV2Builder chatCompletion() {
        return new ChatV2Builder(this);
    }

    public V2Response chatCompletion(V2Request request) {
        return request(request, V2Response.class);
    }

    public StreamIterator<V2StreamResponse> chatCompletionStream(V2Request request) {
        request.setStream(true);
        return requestStream(request, V2StreamResponse.class);
    }
}
