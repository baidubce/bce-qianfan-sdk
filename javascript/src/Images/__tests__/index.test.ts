import {Image2Text, Text2Image, setEnvVariable} from '../../index';

// 设置环境变量
setEnvVariable('QIANFAN_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_CONSOLE_API_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_ACCESS_KEY', '123');
setEnvVariable('QIANFAN_SECRET_KEY', '456');

describe('Image2Text', () => {
    let client;

    beforeEach(() => {
        client = new Image2Text({Endpoint: 'http://example.com'});
        jest.clearAllMocks();
    });

    it('should return a response for a given image', async () => {
        const mockImage2TextResponse = {
            data: '分析结果',
        };
        client.image2Text = jest.fn().mockResolvedValue(mockImage2TextResponse);

        const resp = await client.image2Text({
            prompt: '分析一下图片画了什么',
            image: '图片的base64编码',
        });
        expect(client.image2Text).toHaveBeenCalledWith({
            prompt: '分析一下图片画了什么',
            image: '图片的base64编码',
        });
        expect(resp).toEqual(mockImage2TextResponse);
    });
});


describe('Text2Image', () => {
    let client;

    beforeEach(() => {
        // 实例化 Text2Image 客户端
        client = new Text2Image();
        jest.clearAllMocks();
    });

    it('should generate an image based on text input', async () => {
        // 模拟 text2Image 方法的响应
        const mockText2ImageResponse = {
            data: [{
                b64_image: 'base64EncodedImage',
            }],
        };
        client.text2Image = jest.fn().mockResolvedValue(mockText2ImageResponse);

        const resp = await client.text2Image({
            prompt: '生成爱莎公主的图片',
            size: '768x768',
            n: 1,
            steps: 20,
            sampler_index: 'Euler a',
        }, 'Stable-Diffusion-XL');

        // 验证 text2Image 方法是否被正确调用
        expect(client.text2Image).toHaveBeenCalledWith({
            prompt: '生成爱莎公主的图片',
            size: '768x768',
            n: 1,
            steps: 20,
            sampler_index: 'Euler a',
        }, 'Stable-Diffusion-XL');

        // 验证返回的数据
        expect(resp).toEqual(mockText2ImageResponse);

        // 以下是对生成的图片进行展示的部分
        // 在单元测试中，我们通常不启动服务器来展示生成的图片
        // 但如果需要验证图片的 Base64 编码，可以添加相应的断言
        const base64Image = resp.data[0].b64_image;
        expect(base64Image).toBe('base64EncodedImage');
    });

    // 你可以添加更多测试用例来覆盖不同的情况
});