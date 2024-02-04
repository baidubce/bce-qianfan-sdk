import ChatCompletion from "../../src/ChatCompletion";

const API_KEY =  "";
const SECRET_KEY = "";
const IAMAK = ""
const IAMSK = ""
const client = new  ChatCompletion(API_KEY, SECRET_KEY, 'AK');
// IAM 测试
// const client = new ChatCompletion(IAMAK, IAMSK);

// IAM 测试
// AK/SK 测试
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