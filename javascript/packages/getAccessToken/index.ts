import axios, {isAxiosError} from 'axios';
import {AccessTokenRes} from './type';

/**
 * 认证函数，使用 API_KEY 和 SECRET_KEY 进行 HTTP Basic Auth 认证
 *
 * @param API_KEY API 密钥
 * @param SECRET_KEY 密钥
 * @returns 返回 Promise<AccessTokenRes> 认证结果对象，包含 access_token 和 expires_in
 * @throws 如果认证失败，抛出错误信息
 */
export async function getAccessToken(API_KEY: string, SECRET_KEY: string): Promise<AccessTokenRes> {
    // 使用 HTTP Basic Auth 进行认证
    const axiosInstance = axios.create({
        auth: {
            username: API_KEY,
            password: SECRET_KEY,
        },
    });

    // 请求的 URL
    const url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials';
    // 请求的头部信息
    const headers = {
        'Content-Type': 'application/json',
        accept: 'application/json',
    };

    try {
        // 发起 POST 请求，获取返回结果
        const res = await axiosInstance.post(url, {}, {headers, withCredentials: false});

        // 如果返回状态码不是 200，抛出错误
        if (res.status !== 200) {
            throw new Error(`Request failed with status ${res.status}`);
        }

        // 返回结果中提取 access_token 和 expires_in，并返回
        return {
            access_token: res.data.access_token,
            expires_in: res.data.expires_in,
        };
    }
    catch (err: unknown) {
        if (isAxiosError(err)) { // 判断 err 是否为 AxiosError 类型
            // 如果返回结果中包含 error_description，抛出对应的错误信息；否则直接抛出原始错误信息
            if (err.response?.data?.error_description) {
                throw new Error(err.response.data.error_description);
            }
            else {
                throw err;
            }
        }
        else {
            throw err; // 如果 err 不是 AxiosError 类型，直接抛出原始错误信息
        }
    }
}