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
import DynamicModelEndpoint from '../index';
import HttpClient from '../../HttpClient';
import Fetch from '../../Fetch/index';

jest.mock('../../HttpClient', () => {
    return jest.fn().mockImplementation(() => {
        return {
            getSignature: jest.fn().mockResolvedValue({
                httpMethod: 'POST',
                path: 'https://qianfan-console-api-base-url.com',
                body: JSON.stringify({apiTypefilter: ['type']}),
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                },
            }),
        };
    });
});

jest.mock('../../Fetch/fetch', () => {
    return jest.fn().mockImplementation(() => {
        return {
            makeRequest: jest
                .fn()
                .mockResolvedValueOnce({
                    result: {
                        common: [
                            {apiType: 'chat', name: 'model1', url: 'https://example.com/Model1'},
                            {apiType: 'chat', name: 'model2', url: 'https://example.com/Model2'},
                        ],
                    },
                })
                .mockRejectedValueOnce(new Error('Network error')),
        };
    });
});

function setupDynamicModelEndpoint(clientResponse) {
    const client = new HttpClient({}) as jest.Mocked<HttpClient>;
    const fetchInstance = new Fetch() as jest.Mocked<Fetch>;

    client.getSignature.mockResolvedValue(clientResponse); // 假设这是获取签名的响应
    fetchInstance.makeRequest.mockResolvedValue({}); // 假设这是 fetch 请求的响应

    return new DynamicModelEndpoint(client, 'https://qianfan-console-api-base-url.com', 'https://qianfan-base-url.com');
}

// Test Suites
describe('DynamicModelEndpoint', () => {
    beforeEach(() => {
        // 重置所有Mocks
        jest.clearAllMocks();
    });
    // 测试动态映射未过期时获取端点
    it('should return endpoint from dynamic mapping when not expired', async () => {
        const endpoint = setupDynamicModelEndpoint({});
        endpoint.setDynamicMapExpireAt(Date.now() / 1000 + 1000); // 设置为未过期
        const dynamicTypeModelEndpointMap = endpoint.getDynamicTypeModelEndpointMap();
        dynamicTypeModelEndpointMap.set('chat', new Map([['model1', 'https://example.com/Model0']]));
        await expect(endpoint.getEndpoint('chat', 'Model1')).resolves.toEqual(
            '/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/Model0'
        );
    });
    // 测试动态映射已过期并成功更新后获取端点
    it('should update and return endpoint from dynamic mapping when expired', async () => {
        const endpoint = setupDynamicModelEndpoint({});
        endpoint.setDynamicMapExpireAt(Date.now() / 1000 - 1); // 设置为已过期
        const dynamicTypeModelEndpointMap = endpoint.getDynamicTypeModelEndpointMap();
        await expect(endpoint.getEndpoint('chat', 'model1')).resolves.toEqual(
            '/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/Model1'
        );
        expect(dynamicTypeModelEndpointMap.get('chat').get('model2')).toEqual('https://example.com/Model2');
    });
    //   测试更新动态映射失败时的，读取默认配置
    it('should handle failure during dynamic mapping update', async () => {
        const client = new HttpClient({}) as jest.Mocked<HttpClient>;
        const fetchInstance = new Fetch() as jest.Mocked<Fetch>;
        client.getSignature.mockResolvedValue({}); // 假设这是获取签名的响应
        fetchInstance.makeRequest.mockRejectedValue(new Error('Failed to fetch')); // 模拟 fetch 请求失败
        const endpoint = new DynamicModelEndpoint(
            client,
            'https://qianfan-console-api-base-url.com',
            'https://qianfan-base-url.com'
        );
        const dynamicTypeModelEndpointMap = endpoint.getDynamicTypeModelEndpointMap();
        dynamicTypeModelEndpointMap.set('chat', new Map([['model1', 'https://example.com/Model0']]));
        endpoint.setDynamicMapExpireAt(Date.now() / 1000 - 1); // 设置为已过期
        expect(dynamicTypeModelEndpointMap.get('chat').get('model1')).toEqual('https://example.com/Model0');
    });
    //   测试当动态和静态映射中均未找到模型时的行为
    it('should return an empty string when the model is not found in both mappings', async () => {
        const endpoint = setupDynamicModelEndpoint({});
        endpoint.setDynamicMapExpireAt(Date.now() / 1000 + 1000); // 设置为未过期
        await expect(endpoint.getEndpoint('chat', 'NonExistentModel')).resolves.toEqual('');
    });
});
