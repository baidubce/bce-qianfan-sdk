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

import {Plugins, setEnvVariable} from '../index';

// 修改env文件
// setEnvVariable('QIANFAN_AK','***');
// setEnvVariable('QIANFAN_SK','***');

// 直接读取env
const client = new Plugins({Endpoint: '***'});

// 手动传AK/SK 测试
// const client = new Eembedding({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传ACCESS_KEY/ SECRET_KEY测试
// const client = new Eembedding({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });
/*
 * plugins支持插件
 * 知识库 uuid-zhishiku
 * 天气 uuid-weatherforecast
 * 智慧图问 uuid-chatocr
*/
// 天气插件 测试
async function weatherMain() {
    const resp = await client.plugin({
        query: '深圳今天天气如何',
        plugins: [
            'uuid-weatherforecast',
        ],
        verbose: false,
    });
    console.log('返回结果');
    console.log(resp);
}

// weatherMain();

// 天气插件 流式测试
async function weatherStreamMain() {
    const stream = await client.plugin({
        query: '深圳今天天气如何',
        plugins: [
            'uuid-weatherforecast',
        ],
        stream: true,
        verbose: false,
    });
    console.log('返回结果');
    for await (const chunk of stream as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
}

weatherStreamMain();

