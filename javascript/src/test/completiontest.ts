import Completions from "../../src/Completions";

// const API_KEY =  "";
// const SECRET_KEY = "";
const IAMAK = ""
const IAMSK = ""
// const client = new Completions(API_KEY, SECRET_KEY, 'AK');
// IAM 测试
const client = new Completions(IAMAK, IAMSK);

// IAM 测试
async function main() {
    const resp = await client.completions({
        prompt: 'Introduce the city Beijing',
        stream: true,
    }, "SQLCoder-7B");
    console.log('返回结果')
    console.log(resp);
}

// AK/SK 测试
// async function main() {
//     const resp = await client.completions({
//         prompt: 'Introduce the city Beijing',
//     }, "SQLCoder-7B");
//     console.log('返回结果')
//     console.log(resp);
// }

main();