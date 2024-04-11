import {Mutex} from 'async-mutex';
import Fetch from '../Fetch/fetch';
import HttpClient from '../HttpClient';
import {SERVER_LIST_API, DEFAULT_HEADERS} from '../constant';
import {getTypeMap, typeModelEndpointMap} from './utils';
import {getPath} from '../utils';

type ModelEndpointMap = Map<string, Map<string, string>>;

class DynamicModelEndpoint {
    private DYNAMIC_MAP_REFRESH_INTERVAL = 3600;
    private dynamicTypeModelEndpointMap: ModelEndpointMap = new Map();
    private dynamicMapExpireAt: number = 0;
    private qianfanConsoleApiBaseUrl: string;
    private qianfanBaseUrl: string;
    /**
     * 客户端
     */
    private client: HttpClient;
    /**
     * 构造函数
     */
    protected fetchInstance: Fetch;

    constructor(client: HttpClient, qianfanConsoleApiBaseUrl: string, qianfanBaseUrl: string) {
        this.client = client;
        this.qianfanConsoleApiBaseUrl = qianfanConsoleApiBaseUrl;
        this.qianfanBaseUrl = qianfanBaseUrl;
        this.fetchInstance = new Fetch();
    }

    /**
     * 获取终端节点
     *
     * @param type 类型
     * @param model 模型（可选）
     * @param endpoint 终端节点（可选）
     * @returns 终端节点
     */
    public async getEndpoint(type: string, model?: string): Promise<string> {
        const mutex = new Mutex();
        const release = await mutex.acquire(); // 等待获取互斥锁
        try {
            if (this.isDynamicMapExpired()) {
                await this.updateDynamicModelEndpoint(type); // 等待动态更新完成
                this.dynamicMapExpireAt = Date.now() / 1000 + this.DYNAMIC_MAP_REFRESH_INTERVAL;
            }
        }
        catch (error) {
            console.log('Failed to update dynamic model endpoint map', error);
        }
        finally {
            release(); // 释放互斥锁
            // 在更新逻辑完成后继续
            const dynamicTypeMap = getTypeMap(this.dynamicTypeModelEndpointMap, type);
            if (dynamicTypeMap) {
                const url = dynamicTypeMap.get(model?.toLowerCase() ?? '') ?? '';

                return url; // 如果找到了动态类型映射中的URL，返回它
            }

            // 如果动态映射中没有找到，尝试从静态映射中获取
            const typeMap = getTypeMap(typeModelEndpointMap, type);
            const endPoint = typeMap.get(model?.toLowerCase() ?? '') ?? '';
            const url = getPath({
                Authentication: 'IAM',
                api_base: this.qianfanBaseUrl,
                endpoint: endPoint,
                type,
            });
            return url; // 返回从静态映射中获取的URL
        }
    }
    /**
     * 判断动态映射是否已过期
     *
     * @return 如果动态映射已过期，返回true；否则返回false
     */
    private isDynamicMapExpired() {
        // 获取当前时间戳（以秒为单位）
        const now = Date.now() / 1000;
        // 比较当前时间戳和动态映射过期时间戳
        return now > this.dynamicMapExpireAt;
    }
    /**
     * 更新动态模型端点
     *
     * @param qianfanConsoleApiBaseUrl Qianfan控制台API基础URL
     * @param apiTypefilter API类型过滤器数组
     * @param headers HTTP请求头
     * @returns 返回异步操作结果
     */
    async updateDynamicModelEndpoint(type: string) {
        const url = `${this.qianfanConsoleApiBaseUrl}${SERVER_LIST_API}`;
        const fetchOption = await this.client.getSignature({
            httpMethod: 'POST',
            path: url,
            
            body: JSON.stringify({
                apiTypefilter: [type],
            }),
            headers: {
                ...DEFAULT_HEADERS,
            },
        });

        try {
            const res = await this.fetchInstance.makeRequest(url, fetchOption);
            const commonServerList = res?.result?.common ?? [];
            const newMap = new Map<string, string>();
            this.dynamicTypeModelEndpointMap.set(type, newMap);
            if (commonServerList.length) {
                commonServerList.forEach(item => {
                    let modelMap = this.dynamicTypeModelEndpointMap.get(item.apiType);
                    if (!modelMap) {
                        modelMap = new Map<string, string>();
                        this.dynamicTypeModelEndpointMap.set(item.apiType, modelMap);
                    }
                    modelMap.set(item.name.toLowerCase(), item.url);
                });
            }
        }
        catch (error) {
            throw new Error('更新动态模型端点失败');
        }
    }

    getDynamicMapExpireAt() {
        return this.dynamicMapExpireAt;
    }
    setDynamicMapExpireAt(dynamicMapExpireAt: number) {
        this.dynamicMapExpireAt = dynamicMapExpireAt;
    }
    getDynamicTypeModelEndpointMap() {
        return this.dynamicTypeModelEndpointMap;
    }
}

export default DynamicModelEndpoint;
