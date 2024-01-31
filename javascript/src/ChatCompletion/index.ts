import axios from 'axios';
// import HttpClient from '../HttpClient';
import {modelInfoMap, getIAMConfig} from './utils';
import {api_base, DEFAULT_HEADERS, base_path} from '../constant';
import {getAccessToken} from '../utils';
import {ChatModel, ChatResp} from '../interface';

export class ChatCompletion {
    private API_KEY: string;
    private SECRET_KEY: string;
    private IAMAK?: string;
    private IAMSK?: string;
    private headers = DEFAULT_HEADERS;
    access_token: string = '';
    expires_in: number = 0;
    /**
     * 千帆大模型
     * @param API_KEY 应用的API Key，在千帆控制台-应用列表查看
     * @param SECRET_KEY 应用的Secret Key，在千帆控制台-应用列表查看
     * @param IAMAK IAM Key
     * @param IAMSK IAM Secret Key
     */
    constructor(API_KEY: string, SECRET_KEY: string, IAMAK?: string, IAMSK?: string) {
        this.API_KEY = API_KEY;
        this.SECRET_KEY = SECRET_KEY;
        this.IAMAK = IAMAK;
        this.IAMSK = IAMSK;
    }

    /**
     * 发起基础对话请求
     * @param model 模型名称
     * @param body 请求参数
     * @param endpoint 申请发布时填写的API地址
     * @returns Promise<ChatResp>
     */
    public async baseChat<T extends ChatModel>(
        body: any,
        model: T = 'ERNIE-Bot' as T,
        endpoint: string = ''
    ): Promise<ChatResp<T>> {
        // 埋点 hardcode
        body.extra_parameters = {
            ...body?.extra_parameters,
            'request_source': 'qianfan_appbuilder_v1.0',
        };
        if (endpoint.length === 0) {
            endpoint = modelInfoMap[model].endpoint;
        }
        // // IAM 鉴权
        // if (this.IAMAK && this.IAMSK) {
        //     const config = getIAMConfig(this.IAMAK, this.IAMSK);
        //     const client :any = new HttpClient(config);
        //     const path = `${base_path}${endpoint}`;
        //     const response = await client.sendRequest('POST', path, body, this.headers, {});
        //     return response.body;
        // }

        // AK/SK 鉴权
        const  access= await getAccessToken(this.API_KEY, this.SECRET_KEY, this.headers);
        if (access.expires_in < Date.now() / 1000) {
         const url = `${api_base}${endpoint}?access_token=${access.access_token}`;
         const resp = await axios.post(url, body, {headers: this.headers});
         if (resp.data?.error_code && resp.data?.error_msg) {
             throw new Error(resp.data.error_msg);
         }
         return resp.data as ChatResp<T>;
        }
    }
}