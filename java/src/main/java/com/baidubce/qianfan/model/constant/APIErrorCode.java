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

package com.baidubce.qianfan.model.constant;

public class APIErrorCode {
    public static final int NO_ERROR = 0;
    public static final int UNKNOWN_ERROR = 1;
    public static final int SERVICE_UNAVAILABLE = 2;
    public static final int UNSUPPORTED_METHOD = 3;
    public static final int REQUEST_LIMIT_REACHED = 4;
    public static final int NO_PERMISSION_TO_ACCESS_DATA = 6;
    public static final int GET_SERVICE_TOKEN_FAILED = 13;
    public static final int APP_NOT_EXIST = 15;
    public static final int DAILY_LIMIT_REACHED = 17;
    public static final int QPS_LIMIT_REACHED = 18;
    public static final int TOTAL_REQUEST_LIMIT_REACHED = 19;
    public static final int INVALID_REQUEST = 100;
    public static final int API_TOKEN_INVALID = 110;
    public static final int API_TOKEN_EXPIRED = 111;
    public static final int INTERNAL_ERROR = 336000;
    public static final int INVALID_ARGUMENT = 336001;
    public static final int INVALID_JSON = 336002;
    public static final int INVALID_PARAM = 336003;
    public static final int PERMISSION_ERROR = 336004;
    public static final int API_NAME_NOT_EXIST = 336005;
    public static final int SERVER_HIGH_LOAD = 336100;
    public static final int INVALID_HTTP_METHOD = 336101;
    public static final int INVALID_ARGUMENT_SYSTEM = 336104;
    public static final int INVALID_ARGUMENT_USER_SETTING = 336105;
    public static final int RPM_LIMIT_REACHED = 336501;
    public static final int TPM_LIMIT_REACHED = 336502;
    public static final int CONSOLE_INTERNAL_ERROR = 500000;

    private APIErrorCode() {
    }
}
