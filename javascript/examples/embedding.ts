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

import {Embedding, setEnvVariable} from '../index';

// 修改env文件
// setEnvVariable('QIANFAN_AK','***');
// setEnvVariable('QIANFAN_SK','***');

// 直接读取env
const client = new Embedding();

// 手动传AK/SK 测试
// const client = new Embedding({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传ACCESS_KEY/ SECRET_KEY测试
// const client = new Embedding({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });

// AK/SK 测试
async function main() {
    const resp = await client.embedding({
        input: ['Introduce the city Beijing'],
    }, 'Embedding-V1');
    console.log('返回结果');
    console.log(resp.data);
}

main();