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

import java.util.List;

public class ListServiceResponse {
    /**
     * 预置服务
     */
    private List<ServiceItem> common;

    /**
     * 自定义服务
     */
    private List<ServiceItem> custom;

    public List<ServiceItem> getCommon() {
        return common;
    }

    public ListServiceResponse setCommon(List<ServiceItem> common) {
        this.common = common;
        return this;
    }

    public List<ServiceItem> getCustom() {
        return custom;
    }

    public ListServiceResponse setCustom(List<ServiceItem> custom) {
        this.custom = custom;
        return this;
    }
}
