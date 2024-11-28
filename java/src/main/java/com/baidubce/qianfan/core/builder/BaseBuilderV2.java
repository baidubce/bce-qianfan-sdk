package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.QianfanV2;
import com.baidubce.qianfan.model.exception.ValidationException;

public class BaseBuilderV2<T extends BaseBuilderV2<T>> extends BaseBuilder<T> {
    private QianfanV2 qianfan;

    protected BaseBuilderV2() {
        super();
    }

    protected BaseBuilderV2(QianfanV2 qianfan) {
        this.qianfan = qianfan;
    }

    protected QianfanV2 getQianfanV2() {
        if (qianfan == null) {
            throw new ValidationException("QianfanV2 client is not set. " +
                    "please create builder from QianfanV2 client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }

        return qianfan;
    }
}
