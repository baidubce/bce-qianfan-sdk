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

import {Plugin, setEnvVariable} from '../src/index';

// 修改env文件
// setEnvVariable('QIANFAN_AK','***');
// setEnvVariable('QIANFAN_SK','***');

// 直接读取env
const client = new Plugin();

// 手动传AK/SK 测试
// const client = new Plugin({ QIANFAN_AK: '***', QIANFAN_SK: '***'});
// 手动传ACCESS_KEY/ SECRET_KEY测试
// const client = new Plugin({ QIANFAN_ACCESS_KEY: '***', QIANFAN_SECRET_KEY: '***' });
/*
 * plugins支持插件
 * 知识库 uuid-zhishiku
 * 天气 uuid-weatherforecast
 * 智慧图问 uuid-chatocr
*/
// 天气插件 测试
async function weatherMain() {
    const resp = await client.plugins({
        query: '深圳今天天气如何',
        plugins: [
            'uuid-weatherforecast',
        ],
    });
    console.log('返回结果');
    console.log(resp);
}

// weatherMain();

// 天气插件 流式测试
async function weatherStreamMain() {
    const stream = await client.plugins({
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

// 智慧图问插件 测试
async function main() {
    const stream = await client.plugins({
        query: '请解析这张图片, 告诉我怎么画这张图的简笔画',
        plugins: [
            'uuid-chatocr',
        ],
        stream: true,
        fileurl: 'https://xxx.bcebos.com/xxx/xxx.jpeg',
    });
    for await (const chunk of stream as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
    // console.log('返回结果');
    // console.log(resp);
}

// weatherStreamMain();

// weatherMain();

// eChart插件测试
// async function yiYanMain() {
//     const resp = await client.plugins({
//         messages: [
//             {
//                 "role": "user",
//                 "content": "帮我画一个饼状图：8月的用户反馈中，BUG有100条，需求有100条，使用咨询100条，总共300条反馈"
//             }
//         ],
//         plugins: ["eChart"],
//     });
//     console.log('返回结果');
//     console.log(resp);
// }
// yiYanMain();

// echarts流式测试
// async function streamYiYanMain() {
//     const resp = await client.plugins({
//         messages: [
//             {
//                 "role": "user",
//                 "content": `请按照下面要求给我生成雷达图：学校教育质量: 维度：师资力量、设施、
//                 课程内容、学生满意度。对象：A,B,C三所学校。学校A的师资力量得分为10分，
//                 设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。*
//                 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，
//                 学生满意度的得分为7分。* 学校C的师资力量得分为7分，设施得分为7分，
//                 课程内容的得分为9分，学生满意度的得分为8分。`
//             }
//         ],
//         plugins: ["eChart"],
//         stream: true,
//     });
//     for await (const chunk of resp as AsyncIterableIterator<any>) {
//         console.log(chunk);
//     }
// }
// streamYiYanMain();

// ImageAI插件测试
// async function yiYanMain() {
//     const resp = await client.plugins({
//         messages: [
//             {
//                 "role": "user",
//                 "content": "<img>cow.jpeg</img><url>https://xxx/xxx/xxx.jpeg</url> 这张图片当中都有啥"
//             }
//         ],
//         plugins: ["ImageAI"],
//     });
//     console.log('返回结果');
//     console.log(resp);
// }

async function streamYiYanMain() {
    const resp = await client.plugins({
        messages: [
            {
                'role': 'user',
                'content': '<file>浅谈牛奶的营养与消费趋势.docx</file><url>https://xxx/xxx/xxx.docx</url>',
            },
        ],
        plugins: ['ImageAI'],
        stream: false,
    });
    for await (const chunk of resp as AsyncIterableIterator<any>) {
        console.log(chunk);
    }
}

// ChatFile测试
async function yiYanMain() {
    const resp = await client.plugins({
        messages: [
            {'role': 'user', 'content': '<file>浅谈牛奶的营养与消费趋势.docx</file><url>https://xxx/xxx/xxx.docx</url>'},
            // eslint-disable-next-line max-len
            {'role': 'assistant', 'content': '以下是该文档的关键内容：\n牛奶作为一种营养丰富、易消化吸收的天然食品，受到广泛欢迎。其价值主要表现在营养成分和医学价值两个方面。在营养成分方面，牛奶含有多种必需的营养成分，如脂肪、蛋白质、乳糖、矿物质和水分等，比例适中，易于消化吸收。在医学价值方面，牛奶具有促进生长发育、维持健康水平的作用，对于儿童长高也有积极影响。此外，牛奶还具有极高的市场前景，消费者关注度持续上升，消费心理和市场需求也在不断变化。为了更好地发挥牛奶的营养价值，我们应该注意健康饮用牛奶的方式，适量饮用，并根据自身情况选择合适的牛奶产品。综上所述，牛奶作为一种理想的天然食品，不仅具有丰富的营养成分，还具有极高的医学价值和市场前景。我们应该充分认识牛奶的价值，科学饮用，让牛奶为我们的健康发挥更大的作用。'},
            {'role': 'user', 'content': '牛奶的营养成本有哪些'},
        ],
        plugins: ['ChatFile'],
        stream: false,
    });
    console.log('返回结果');
    console.log(resp);
}
yiYanMain();
// streamYiYanMain();