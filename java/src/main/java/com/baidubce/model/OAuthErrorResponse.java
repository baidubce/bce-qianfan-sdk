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

package com.baidubce.model;

import com.baidubce.util.Json;

import java.io.Serializable;

public class OAuthErrorResponse implements Serializable {
    private String error;

    private String errorDescription;

    public String getError() {
        return error;
    }

    public OAuthErrorResponse setError(String error) {
        this.error = error;
        return this;
    }

    public String getErrorDescription() {
        return errorDescription;
    }

    public OAuthErrorResponse setErrorDescription(String errorDescription) {
        this.errorDescription = errorDescription;
        return this;
    }

    @Override
    public String toString() {
        return Json.serialize(this);
    }
}
