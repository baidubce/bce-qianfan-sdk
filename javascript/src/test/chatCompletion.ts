import * as dotenv from "dotenv";

import ChatCompletion from "../../src/ChatCompletion";

dotenv.config();
const API_KEY = process.env.API_KEY || '';
const SECRET_KEY = process.env.SECRET_KEY || '';
const IAM_ACESS_KEY = process.env.IAM_ACESS_KEY || '';
const IAM_SECRET_KEY = process.env.IAM_SECRET_KEY || '';
// AK/SK 测试
const client = new  ChatCompletion(API_KEY, SECRET_KEY, 'AK');
// IAM 测试
// const client = new ChatCompletion(IAM_ACESS_KEY, IAM_SECRET_KEY);

// 流式 测试
// async function main() {
//     const resp = await client.chat({
//         messages: [
//             {
//                 role: "user",
//                 content: "你好，请问你是哪个模型？",
//             },
//         ],
//         stream: true,
//     }, "ERNIE-Bot-turbo");
//     console.log('返回结果')
//     console.log(resp);
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