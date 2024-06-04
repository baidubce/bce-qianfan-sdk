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

import {Image2Text, setEnvVariable} from '../index';

// 修改env文件
// setEnvVariable('QIANFAN_AK','***');
// setEnvVariable('QIANFAN_SK','***');

// 直接读取env
// const client = new Image2Text({Endpoint: '***'});
// 使用预置服务
const client = new Image2Text();

// 手动传AK/SK 测试
// const client = new Eembedding({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传ACCESS_KEY/ SECRET_KEY测试
// const client = new Eembedding({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });

// AK/SK 测试
async function main() {
    const resp = await client.image2Text({
        prompt: '分析一下图片画了什么',
        image: '图片的base64编码',
    });
    console.log(resp);
}

main();