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

package com.baidubce.qianfan.model.image;

import com.baidubce.qianfan.model.BaseResponse;

import java.util.List;

public class Text2ImageResponse extends BaseResponse<Text2ImageResponse> {
    /**
     * 生成图片结果
     */
    private List<ImageData> data;

    /**
     * token统计信息
     */
    private ImageUsage usage;

    public List<ImageData> getData() {
        return data;
    }

    public Text2ImageResponse setData(List<ImageData> data) {
        this.data = data;
        return this;
    }

    public ImageUsage getUsage() {
        return usage;
    }

    public Text2ImageResponse setUsage(ImageUsage usage) {
        this.usage = usage;
        return this;
    }
}
