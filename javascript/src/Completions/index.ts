import axios, {AxiosInstance} from 'axios';
import HttpClient from '../HttpClient';
import {CompletionModel, modelInfoMap} from './utils';
import {DEFAULT_HEADERS} from '../constant';
import {getAccessToken, getRequestBody, getIAMConfig, getPath} from '../utils';
import {RespBase, CompletionBody} from '../interface';
import * as packageJson from '../../package.json';

export class Completions {
    private API_KEY: string;
    private SECRET_KEY: string;
    private Type?: string = 'IAM';
    private Endpoint?: string = '';
    private headers = DEFAULT_HEADERS;
    private axiosInstance: AxiosInstance;
    access_token: string = '';
    expires_in: number = 0;

    /**
     * 千帆大模型
     * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
     * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
     * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
     * @param Endpoint 请求地址，默认使用千帆大模型服务
     */

    constructor(API_KEY: string, SECRET_KEY: string, Type: string = 'IAM', Endpoint: string = '') {
        this.API_KEY = API_KEY;
        this.SECRET_KEY = SECRET_KEY;
        this.Type = Type
        this.Endpoint = Endpoint;
        this.axiosInstance = axios.create();
    }

    private async sendRequest(model: CompletionModel, body: CompletionBody, stream: boolean = false, endpoint?:string): Promise<RespBase> {
        const path = getPath(model, modelInfoMap, endpoint, 'completions');
        const requestBody = getRequestBody(body, packageJson.version);
        // IAM鉴权
        if (this.Type === 'IAM') {
            const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
            const client = new HttpClient(config);
            const response = await client.sendRequest('POST', path, requestBody, this.headers);
            return response as RespBase;
        }
        // AK/SK鉴权    
        if (this.Type === 'AK') {
            const access = await getAccessToken(this.API_KEY, this.SECRET_KEY, this.headers);
            // 重试问题初始化进入不了 TODO!!
            // if (access.expires_in < Date.now() / 1000) { 
                const url = `${path}?access_token=${access.access_token}`;
                const options = {
                    method: 'POST',
                    url: url,
                    headers: this.headers,
                    data: requestBody
                }
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data as RespBase;
                } catch (error) {
                    throw new Error(error);
                }
            // }
        }

        // TODO 流式结果处理

        throw new Error(`Unsupported authentication type: ${this.Type}`);
    }

    public async completions(body: CompletionBody, model: CompletionModel = 'ERNIE-Bot-turbo'): Promise<RespBase> {
       const stream = body.stream ?? false;
       return this.sendRequest(model, body, stream, this.Endpoint);
    }
}

export default Completions