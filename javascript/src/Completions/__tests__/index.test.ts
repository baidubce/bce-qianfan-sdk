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
import {CompletionBody, RespBase} from '../../interface';
import {Completions, setEnvVariable} from '../../index';

setEnvVariable('QIANFAN_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_CONSOLE_API_BASE_URL', 'http://127.0.0.1:8866');
setEnvVariable('QIANFAN_ACCESS_KEY', '123');
setEnvVariable('QIANFAN_SECRET_KEY', '456');

describe('Completions', () => {
    const client = new Completions();

    beforeEach(() => {
        jest.resetAllMocks();
    });

    it('should return a response when called with valid arguments and no stream', async () => {
        const body: CompletionBody = {
            messages: [],
            prompt: 'Introduce the city of Shenzhen',
            stream: false,
            temperature: 1,
            top_k: 1,
            top_p: 1,
            penalty_score: 1,
            stop: [],
            user_id: '',
            extra_parameters: {},
        };
        const res = (await client.completions(body, 'SQLCoder-7B')) as RespBase;
        const result = res?.result;
        expect(result).toBeDefined();
    }, 60 * 1000);

    it('should return a response when called with valid arguments and stream', async () => {
        const body: CompletionBody = {
            messages: [],
            prompt: 'Introduce the city of Shenzhen',
            stream: true,
            temperature: 1,
            top_k: 1,
            top_p: 1,
            penalty_score: 1,
            stop: [],
            user_id: '',
            extra_parameters: {},
        };
        const res = (await client.completions(body, 'SQLCoder-7B')) as RespBase;
        expect(res).toBeDefined();
    }, 60 * 1000);

    it('should throw an error when an invalid model is provided', async () => {
        const body: CompletionBody = {
            messages: [],
            prompt: 'Introduce the city of Shenzhen',
            stream: true,
            temperature: 1,
            top_k: 1,
            top_p: 1,
            penalty_score: 1,
            stop: [],
            user_id: '',
            extra_parameters: {},
        };
        try {
            // @ts-ignore
            await client.completions(body, 'InvalidModel');
        }
        catch (error) {
            expect(error).toBeInstanceOf(Error);
        }
    }, 60 * 1000);

    it('should throw an error when an invalid temperature is provided', async () => {
        const body: CompletionBody = {
            messages: [],
            prompt: 'Introduce the city of Shenzhen',
            stream: true,
            temperature: 0,
            top_k: 1,
            top_p: 1,
            penalty_score: 1,
            stop: [],
            user_id: '',
            extra_parameters: {},
        };
        try {
            await client.completions(body, 'SQLCoder-7B');
        }
        catch (error) {
            expect(error).toBeInstanceOf(Error);
        }
    }, 60 * 1000);
});