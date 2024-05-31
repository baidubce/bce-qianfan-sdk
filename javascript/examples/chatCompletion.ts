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

import {ChatCompletion, setEnvVariable} from '../src/index';

// 修改env文件
// setEnvVariable('QIANFAN_AK','***');
// setEnvVariable('QIANFAN_SK','***');

// 直接读取env
const client = new ChatCompletion();

// 手动传AK/SK 测试
// const client = new ChatCompletion({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传ACCESS_KEY/ SECRET_KEY测试
// const client = new ChatCompletion({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });

// 流式 测试
async function main() {
    const stream =  await client.chat({
        messages: [
            {
                role: 'user',
                content: '等额本金和等额本息有什么区别？',
            },
        ],
        stream: true,
    }, 'ERNIE-Bot-turbo');
    console.log('流式返回结果');
    for await (const chunk of stream as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
}

// 基础 测试
// async function main() {
//     const resp = await client.chat({
//         messages: [
//             {
//                 role: "user",
//                 content: "今天深圳天气",
//             },
//         ],
//     }, "ERNIE-Bot-turbo");
//     console.log('返回结果')
//     console.log(resp);
// }

main();
