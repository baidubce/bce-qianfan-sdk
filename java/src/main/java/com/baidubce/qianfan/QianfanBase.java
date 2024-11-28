package com.baidubce.qianfan;

import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.console.ConsoleRequest;
import com.baidubce.qianfan.model.console.ConsoleResponse;

import java.lang.reflect.Type;

public abstract class QianfanBase {
    protected QianfanClient client;

    protected QianfanBase() {}

    public <T extends BaseResponse<T>, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        return client.request(request, responseClass);
    }

    public <T extends BaseResponse<T>, U extends BaseRequest<U>> StreamIterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        return client.requestStream(request, responseClass);
    }

    public <T> ConsoleResponse<T> consoleRequest(ConsoleRequest request, Type type) {
        return client.consoleRequest(request, type);
    }

    public void setClient(QianfanClient client) {
        this.client = client;
    }
}
