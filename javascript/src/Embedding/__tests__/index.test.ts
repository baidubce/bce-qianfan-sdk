import {EmbeddingBody, EmbeddingResp} from '../../interface';
import {Embedding, setEnvVariable} from '../../index';

// 设置环境变量
setEnvVariable('QIANFAN_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_CONSOLE_API_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_ACCESS_KEY', '123');
setEnvVariable('QIANFAN_SECRET_KEY', '456');

describe('Embedding', () => {
    const client = new Embedding();

    beforeEach(() => {
        jest.resetAllMocks();
    });

    it('should return a response when called with embedding', async () => {
        const body: EmbeddingBody = {
            input: ['Introduce the city Beijing'],
        };
        const res = (await client.embedding(body)) as EmbeddingResp;
        const result = res?.data;
        expect(result).toBeDefined();
    }, 60 * 1000);
});
