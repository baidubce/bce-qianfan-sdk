// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import {APIErrorCode} from './enum';
import {DefaultConfig} from './interface';

export const BASE_PATH = '/rpc/2.0/ai_custom/v1/wenxinworkshop';
export const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
};
export const DEFAULT_CONFIG: DefaultConfig = {
    QIANFAN_AK: '',
    QIANFAN_SK: '',
    QIANFAN_ACCESS_KEY: '',
    QIANFAN_SECRET_KEY: '',
    QIANFAN_BASE_URL: 'https://aip.baidubce.com',
    QIANFAN_CONSOLE_API_BASE_URL: 'https://qianfan.baidubce.com',
    QIANFAN_LLM_API_RETRY_TIMEOUT: '600000',
    QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR: '0',
    QIANFAN_LLM_RETRY_MAX_WAIT_INTERVAL: '120000',
    QIANFAN_LLM_API_RETRY_COUNT: '1',
    QIANFAN_QPS_LIMIT: '',
    QIANFAN_RPM_LIMIT: '',
    QIANFAN_TPM_LIMIT: '',
    version: '1',
    ENABLE_OAUTH: false,
};

export const RETRY_CODE = [
    APIErrorCode.TPMLimitReached,
    APIErrorCode.ConsoleInternalError,
    APIErrorCode.ServerHighLoad,
    APIErrorCode.QPSLimitReached,
];

export const SERVER_LIST_API = '/wenxinworkshop/service/list';

export const DYNAMIC_INVALID = ['reranker'];
