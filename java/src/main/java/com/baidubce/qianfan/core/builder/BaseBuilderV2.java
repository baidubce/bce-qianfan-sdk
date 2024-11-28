package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.QianfanBase;
import com.baidubce.qianfan.QianfanV2;
import com.baidubce.qianfan.model.exception.ValidationException;

public class BaseBuilderV2<T extends BaseBuilderV2<T>> extends BaseBuilder<T> {
    protected BaseBuilderV2() {
        super();
    }

    protected BaseBuilderV2(QianfanBase qianfan) {
        super(qianfan);
    }

    protected QianfanV2 getQianfanV2() {
        if (qianfan == null) {
            throw new ValidationException("QianfanBase client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }

        if (!(qianfan instanceof QianfanV2)) {
            throw new ValidationException("QianfanBase is not the instance of Qianfan");
        }
        return (QianfanV2) qianfan;
    }
}
