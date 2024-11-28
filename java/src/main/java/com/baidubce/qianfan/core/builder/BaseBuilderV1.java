package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.QianfanBase;
import com.baidubce.qianfan.model.exception.ValidationException;

public class BaseBuilderV1<T extends BaseBuilderV1<T>> extends BaseBuilder<T> {
    protected BaseBuilderV1() {
        super();
    }

    protected BaseBuilderV1(QianfanBase qianfan) {
        super(qianfan);
    }

    protected Qianfan getQianfan() {
        if (qianfan == null) {
            throw new ValidationException("QianfanBase client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }

        if (!(qianfan instanceof Qianfan)) {
            throw new ValidationException("QianfanBase is not the instance of Qianfan");
        }
        return (Qianfan) qianfan;
    }
}
