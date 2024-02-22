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

import axios, {AxiosInstance} from 'axios';
import HttpClient from '../HttpClient';
import {api_base, DEFAULT_HEADERS, base_path} from '../constant';
import {getAccessToken, getRequestBody, getModelEndpoint, getIAMConfig} from '../utils';
import {Stream} from '../streaming';
import {ChatBody, ChatResp} from '../interface';
import * as packageJson from '../../package.json';
import {modelInfoMap, ChatModel} from './utils';

export class ChatCompletion {
    private controller: AbortController;
    private API_KEY: string;
    private SECRET_KEY: string;
    private Type = 'IAM';
    private headers = DEFAULT_HEADERS;
    private axiosInstance: AxiosInstance;
    access_token = '';
    expires_in = 0;

    /**
     * 千帆大模型
     * @param QIANFAN_AK API Key，IAM、AK/SK 鉴权时必填
     * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
     * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
     */

    constructor(API_KEY: string, SECRET_KEY: string, Type = 'IAM') {
        this.API_KEY = API_KEY;
        this.SECRET_KEY = SECRET_KEY;
        this.Type = Type;
        this.axiosInstance = axios.create();
        this.controller = new AbortController();
    }

    /**
     * 发送请求
     *
     * @param model ChatModel类型参数
     * @param body ChatBody类型参数
     * @param stream 是否开启流式处理，默认为false
     * @returns Promise<ChatResp | AsyncIterable<ChatResp>>
     */
    private async sendRequest(model: ChatModel, body: ChatBody, stream = false): Promise<ChatResp | AsyncIterable<ChatResp>> {
        const endpoint = getModelEndpoint(model, modelInfoMap);
        const requestBody = getRequestBody(body, packageJson.version);

        // IAM鉴权
        if (this.Type === 'IAM') {
            const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
            const client = new HttpClient(config);
            const path = `${base_path}${endpoint}`;
            const response = await client.sendRequest('POST', path, requestBody, this.headers, stream);
            return response;
        }

        // AK/SK鉴权
        if (this.Type === 'AK') {
            const access = await getAccessToken(this.API_KEY, this.SECRET_KEY, this.headers);
            const url = `${api_base}${endpoint}?access_token=${access.access_token}`;
            const options = {
                method: 'POST',
                url: url,
                headers: this.headers,
                data: requestBody
            };

            // 流式处理
            if (stream) {
                try {
                    const sseStream: AsyncIterable<ChatResp> = Stream.fromSSEResponse(await fetch(url, {
                        method: 'POST',
                        headers: this.headers,
                        body: requestBody
                    }), this.controller) as any;
                    return sseStream;
                }
                catch (error) {
                    throw new Error(error);
                }
            }
            else {
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data as ChatResp;
                }
                catch (error) {
                    throw new Error(error);
                }
            }
        }
    }
    /**
     * chat
     * @param body 聊天请求体
     * @param model 聊天模型，默认为 'ERNIE-Bot-turbo'
     * @param stream 是否开启流模式，默认为 false
     * @returns Promise<ChatResp | AsyncIterable<ChatResp>>
     */
    public async chat(body: ChatBody, model: ChatModel = 'ERNIE-Bot-turbo'): Promise<ChatResp | AsyncIterable<ChatResp>> {
        const stream = body.stream ?? false;
        return this.sendRequest(model, body, stream);
    }
}

export default ChatCompletion;