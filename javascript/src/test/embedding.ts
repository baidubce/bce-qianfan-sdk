import * as dotenv from "dotenv";
import Embedding from "../../src/Embedding";

dotenv.config();
const API_KEY = process.env.API_KEY || '';
const SECRET_KEY = process.env.SECRET_KEY || '';
const IAM_ACESS_KEY = process.env.IAM_ACESS_KEY || '';
const IAM_SECRET_KEY = process.env.IAM_SECRET_KEY || '';
const client = new Embedding(API_KEY, SECRET_KEY, 'AK');
// IAM 测试
// const client = new Embedding(IAM_ACESS_KEY, IAM_SECRET_KEY);

// AK/SK 测试
async function main() {
    const resp = await client.embedding({
        input: [ 'Introduce the city Beijing'],
    }, "Embedding-V1");
    console.log('返回结果')
    console.log(resp.data as any);
}

main();