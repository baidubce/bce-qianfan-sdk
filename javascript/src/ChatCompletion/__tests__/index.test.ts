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

import {ChatBody, RespBase} from '../../interface';
import {ChatCompletion, setEnvVariable} from '../../index';

setEnvVariable('QIANFAN_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_CONSOLE_API_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_ACCESS_KEY', '123');
setEnvVariable('QIANFAN_SECRET_KEY', '456');

describe('ChatCompletion', () => {
    const client = new ChatCompletion();

    beforeEach(() => {
        jest.resetAllMocks();
    });

    it('should return a response when called with valid arguments and no stream', async () => {
        const body: ChatBody = {
            stream: false,
            messages: [
                {
                    role: 'user',
                    content: 'What is the weather like in Shenzhen today',
                },
            ],
        };
        const res = (await client.chat(body, 'ernie-bot')) as RespBase;
        const result = res?.result;
        expect(result).toBeDefined();
    });

    it('should return a response when called with valid arguments and stream', async () => {
        const body: ChatBody = {
            query: 'Hello',
            extra_parameters: {},
            stream: true,
            messages: [
                {
                    role: 'user',
                    content: 'What is the weather like in Shenzhen today',
                },
            ],
        };
        const res = await client.chat(body, 'ERNIE-Bot-turbo');
        expect(res).toBeDefined();
    });

    it('should throw an error when an invalid model is provided', async () => {
        const body: ChatBody = {
            query: 'Hello',
            extra_parameters: {},
            messages: [
                {
                    role: 'user',
                    content: 'What is the weather like in Shenzhen today',
                },
            ],
        };
        try {
            // @ts-ignore
            await client.chat(body, 'InvalidModel');
        }
        catch (error) {
            expect(error).toBeInstanceOf(Error);
        }
    });
});
