import * as dotenv from "dotenv";
import Completions from "../../src/Completions";

dotenv.config();
const QIANFAN_AK = process.env.QIANFAN_AK || '';
const QIANFAN_SK = process.env.QIANFAN_SK || '';
const QIANFAN_ACCESS_KEY = process.env.QIANFAN_ACCESS_KEY || '';
const QIANFAN_SECRET_KEY = process.env.QIANFAN_SECRET_KEY || '';
// AK/SK 测试
// const client = new Completions(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
const client = new Completions(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);

async function main() {
    const resp = await client.completions({
        prompt: 'Introduce the city Beijing',
    }, "SQLCoder-7B");
    console.log('返回结果')
    console.log(resp);
}

// // 流式 测试
// async function main() {
//     const stream =  await client.completions({
//         prompt: 'Introduce the city Beijing',
//         stream: true,
//       }, "SQLCoder-7B");
//       console.log('流式返回结果')
//       for await (const chunk of stream as AsyncIterableIterator<any>) {
//           console.log(chunk);
//         }
// }

main();