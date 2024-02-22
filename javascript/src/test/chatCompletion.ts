import * as dotenv from "dotenv";

import ChatCompletion from "../../src/ChatCompletion";

dotenv.config();
const QIANFAN_AK = process.env.QIANFAN_AK || '';
const QIANFAN_SK = process.env.QIANFAN_SK || '';
const QIANFAN_ACCESS_KEY = process.env.QIANFAN_ACCESS_KEY || '';
const QIANFAN_SECRET_KEY = process.env.QIANFAN_SECRET_KEY || '';
// AK/SK 测试
const client = new  ChatCompletion(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
// const client = new ChatCompletion(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);

// 流式 测试
// async function main() {
//     const stream =  await client.chat({
//           messages: [
//               {
//                   role: "user",
//                   content: "等额本金和等额本息有什么区别？"
//               },
//           ],
//           stream: true,
//       }, "ERNIE-Bot-turbo");
//       console.log('流式返回结果')
//       for await (const chunk of stream as AsyncIterableIterator<any>) {
//           console.log(chunk);
//         }
// }

// AK/SK 测试
async function main() {
    const resp = await client.chat({
        messages: [
            {
                role: "user",
                content: "今天深圳天气",
            },
        ],
    }, "ERNIE-Bot-turbo");
    console.log('返回结果')
    console.log(resp);
}

main();