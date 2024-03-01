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

package com.baidubce.core.auth;

import com.baidubce.model.exception.ValidationException;
import com.baidubce.util.StringUtils;

public class Auth {
    public static final String TYPE_IAM = "IAM";
    public static final String TYPE_OAUTH = "OAuth";
    public static final String ENV_ACCESS_KEY = "QIANFAN_ACCESS_KEY";
    public static final String ENV_SECRET_KEY = "QIANFAN_SECRET_KEY";
    public static final String ENV_QIANFAN_AK = "QIANFAN_AK";
    public static final String ENV_QIANFAN_SK = "QIANFAN_SK";

    private Auth() {
    }

    public static IAuth create() {
        String accessKey = System.getenv(ENV_ACCESS_KEY);
        String secretKey = System.getenv(ENV_SECRET_KEY);
        if (StringUtils.isNotEmpty(accessKey) && StringUtils.isNotEmpty(secretKey)) {
            return create(TYPE_IAM, accessKey, secretKey);
        }
        String qianfanAK = System.getenv(ENV_QIANFAN_AK);
        String qianfanSK = System.getenv(ENV_QIANFAN_SK);
        if (StringUtils.isNotEmpty(qianfanAK) && StringUtils.isNotEmpty(qianfanSK)) {
            return create(TYPE_OAUTH, qianfanAK, qianfanSK);
        }
        throw new ValidationException("No access key or secret key found in environment variables");
    }

    public static IAuth create(String accessKey, String secretKey) {
        return create(TYPE_IAM, accessKey, secretKey);
    }

    public static IAuth create(String type, String accessKey, String secretKey) {
        if (TYPE_IAM.equals(type)) {
            return new IAMAuth(accessKey, secretKey);
        } else if (TYPE_OAUTH.equals(type)) {
            return new QianfanOAuth(accessKey, secretKey);
        } else {
            throw new ValidationException("Unsupported auth type: " + type);
        }
    }
}
