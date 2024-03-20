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

public class ImageData {
    /**
     * 固定值 "image"
     */
    private String object;

    /**
     * 图片base64编码内容
     */
    private String b64Image;

    /**
     * 序号
     */
    private Integer index;

    public String getObject() {
        return object;
    }

    public ImageData setObject(String object) {
        this.object = object;
        return this;
    }

    public String getB64Image() {
        return b64Image;
    }

    public ImageData setB64Image(String b64Image) {
        this.b64Image = b64Image;
        return this;
    }

    public Integer getIndex() {
        return index;
    }

    public ImageData setIndex(Integer index) {
        this.index = index;
        return this;
    }
}
