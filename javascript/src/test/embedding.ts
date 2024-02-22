import * as dotenv from "dotenv";
import Embedding from "../../src/Embedding";

dotenv.config();
const QIANFAN_AK = process.env.QIANFAN_AK || '';
const QIANFAN_SK = process.env.QIANFAN_SK || '';
const QIANFAN_ACCESS_KEY = process.env.QIANFAN_ACCESS_KEY || '';
const QIANFAN_SECRET_KEY = process.env.QIANFAN_SECRET_KEY || '';
const client = new Embedding(QIANFAN_AK, QIANFAN_SK, 'AK');
// IAM 测试
// const client = new Embedding(QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY);

// AK/SK 测试
async function main() {
    const resp = await client.embedding({
        input: [ 'Introduce the city Beijing'],
    }, "Embedding-V1");
    console.log('返回结果')
    console.log(resp.data as any);
}

main();