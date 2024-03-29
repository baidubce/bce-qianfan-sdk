/*
 * Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.baidubce.qianfan.model.console;

import com.baidubce.qianfan.util.JsonProp;

public class ServiceVersion {
    /**
     * 发布该服务版本的模型id，只有自定义服务会返回该字段
     */
    @JsonProp("aiModelId")
    private String aiModelId;

    /**
     * 发布该服务版本的模型版本id，只有自定义服务会返回该字段
     */
    @JsonProp("aiModelVersionId")
    private String aiModelVersionId;

    /**
     * 服务基础模型类型
     */
    @JsonProp("trainType")
    private String trainType;

    /**
     * 服务状态，说明
     * （1）该字段值对应状态说明：
     * · Done：已发布
     * · New：待发布
     * · Deploying：发布中
     * · Failed：发布失败
     * · Stopped：暂停服务
     * （2）如果是预置服务，该字段为固定值Done
     */
    @JsonProp("serviceStatus")
    private String serviceStatus;

    public String getAiModelId() {
        return aiModelId;
    }

    public ServiceVersion setAiModelId(String aiModelId) {
        this.aiModelId = aiModelId;
        return this;
    }

    public String getAiModelVersionId() {
        return aiModelVersionId;
    }

    public ServiceVersion setAiModelVersionId(String aiModelVersionId) {
        this.aiModelVersionId = aiModelVersionId;
        return this;
    }

    public String getTrainType() {
        return trainType;
    }

    public ServiceVersion setTrainType(String trainType) {
        this.trainType = trainType;
        return this;
    }

    public String getServiceStatus() {
        return serviceStatus;
    }

    public ServiceVersion setServiceStatus(String serviceStatus) {
        this.serviceStatus = serviceStatus;
        return this;
    }
}
