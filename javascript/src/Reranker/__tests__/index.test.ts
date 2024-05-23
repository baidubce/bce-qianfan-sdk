/* eslint-disable max-len */
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

import {Reranker, setEnvVariable} from '../../index';

// 设置环境变量
setEnvVariable('QIANFAN_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_CONSOLE_API_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_ACCESS_KEY', '123');
setEnvVariable('QIANFAN_SECRET_KEY', '456');

describe('Reranker functionality', () => {
    let client;

    beforeEach(() => {
        client = new Reranker();
        jest.clearAllMocks();
    });

    it('should reorder documents by query', async () => {
        const resp = await client.reranker({
            query: '上海天气',
            documents: ['上海气候', '北京美食'],
        });
        console.log(resp);
        expect(resp).toBeDefined();
    });
});
