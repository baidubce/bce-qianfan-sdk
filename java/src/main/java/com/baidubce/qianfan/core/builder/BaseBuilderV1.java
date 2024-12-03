package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.exception.ValidationException;

public class BaseBuilderV1<T extends BaseBuilderV1<T>> extends BaseBuilder<T> {
    private Qianfan qianfan;

    protected BaseBuilderV1() {
        super();
    }

    protected BaseBuilderV1(Qianfan qianfan) {
        this.qianfan = qianfan;
    }

    protected Qianfan getQianfan() {
        if (qianfan == null) {
            throw new ValidationException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }

        return qianfan;
    }
}
