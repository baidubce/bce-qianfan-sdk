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

package com.baidubce.qianfan.core.auth;

import com.baidubce.qianfan.core.QianfanConfig;
import com.baidubce.qianfan.model.ProxyConfig;
import com.baidubce.qianfan.model.exception.ValidationException;
import com.baidubce.qianfan.util.StringUtils;

public class Auth {
    public static final String TYPE_IAM = "IAM";
    public static final String TYPE_OAUTH = "OAuth";
    private ProxyConfig proxyConfig;


    private Auth() {
    }

    public static IAuth create() {
        // Prefer IAM
        String accessKey = QianfanConfig.getQianfanAccessKey();
        String secretKey = QianfanConfig.getQianfanSecretKey();
        if (StringUtils.isNotEmpty(accessKey) && StringUtils.isNotEmpty(secretKey)) {
            return create(TYPE_IAM, accessKey, secretKey);
        }
        String qianfanAK = QianfanConfig.getQianfanAk();
        String qianfanSK = QianfanConfig.getQianfanSk();
        if (StringUtils.isNotEmpty(qianfanAK) && StringUtils.isNotEmpty(qianfanSK)) {
            return create(TYPE_OAUTH, qianfanAK, qianfanSK);
        }
        throw new ValidationException("No access key or secret key found in environment variables");
    }
    public static IAuth create(ProxyConfig proxyConfig) {
        // Prefer IAM
        String accessKey = QianfanConfig.getQianfanAccessKey();
        String secretKey = QianfanConfig.getQianfanSecretKey();
        if (StringUtils.isNotEmpty(accessKey) && StringUtils.isNotEmpty(secretKey)) {
            return create(TYPE_IAM, accessKey, secretKey,proxyConfig);
        }
        String qianfanAK = QianfanConfig.getQianfanAk();
        String qianfanSK = QianfanConfig.getQianfanSk();
        if (StringUtils.isNotEmpty(qianfanAK) && StringUtils.isNotEmpty(qianfanSK)) {
            return create(TYPE_OAUTH, qianfanAK, qianfanSK,proxyConfig);
        }
        throw new ValidationException("No access key or secret key found in environment variables");
    }

    public static IAuth create(String accessKey, String secretKey) {
        return create(TYPE_IAM, accessKey, secretKey);
    }
    public static IAuth create(String accessKey, String secretKey,ProxyConfig proxyConfig) {
        return create(TYPE_IAM, accessKey, secretKey,proxyConfig);
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
    public static IAuth create(String type, String accessKey, String secretKey,ProxyConfig proxyConfig) {
        if (TYPE_IAM.equals(type)) {
            return new IAMAuth(accessKey, secretKey);
        } else if (TYPE_OAUTH.equals(type)) {
            return new QianfanOAuth(accessKey, secretKey, proxyConfig);
        } else {
            throw new ValidationException("Unsupported auth type: " + type);
        }
    }
}
