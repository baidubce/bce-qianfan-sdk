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

import java.util.List;

public class ServiceItem {
    /**
     * 服务id
     */
    @JsonProp("serviceId")
    private Integer serviceId;

    /**
     * 服务uuid
     */
    @JsonProp("serviceUuid")
    private String serviceUuid;

    /**
     * 服务名称
     */
    private String name;

    /**
     * 服务endpoint
     */
    private String url;

    /**
     * 服务类型，说明：
     * · chat
     * · completions
     * · embeddings
     * · text2image
     * · image2text
     */
    @JsonProp("apiType")
    private String apiType;

    /**
     * 付费状态，说明：
     * · NOTOPEN
     * · OPENED
     * · STOP
     * · FREE
     */
    @JsonProp("chargeStatus")
    private String chargeStatus;

    /**
     * 服务版本列表
     */
    @JsonProp("versionList")
    private List<ServiceVersion> versionList;

    public Integer getServiceId() {
        return serviceId;
    }

    public ServiceItem setServiceId(Integer serviceId) {
        this.serviceId = serviceId;
        return this;
    }

    public String getServiceUuid() {
        return serviceUuid;
    }

    public ServiceItem setServiceUuid(String serviceUuid) {
        this.serviceUuid = serviceUuid;
        return this;
    }

    public String getName() {
        return name;
    }

    public ServiceItem setName(String name) {
        this.name = name;
        return this;
    }

    public String getUrl() {
        return url;
    }

    public ServiceItem setUrl(String url) {
        this.url = url;
        return this;
    }

    public String getApiType() {
        return apiType;
    }

    public ServiceItem setApiType(String apiType) {
        this.apiType = apiType;
        return this;
    }

    public String getChargeStatus() {
        return chargeStatus;
    }

    public ServiceItem setChargeStatus(String chargeStatus) {
        this.chargeStatus = chargeStatus;
        return this;
    }

    public List<ServiceVersion> getVersionList() {
        return versionList;
    }

    public ServiceItem setVersionList(List<ServiceVersion> versionList) {
        this.versionList = versionList;
        return this;
    }
}
