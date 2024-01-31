import axios, {AxiosRequestConfig} from 'axios';

import {AccessTokenResp} from './interface';
/**
 * 使用 AK，SK 生成鉴权签名（Access Token）
 * @return string 鉴权签名信息（Access Token）
 */

export async function getAccessToken(
    API_KEY: string,
    SECRET_KEY: string,
    headers: AxiosRequestConfig['headers']
): Promise<AccessTokenResp> {
    const url = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${API_KEY}&client_secret=${SECRET_KEY}`;
    const resp = await axios.post(url, {}, {headers, withCredentials: false});
    if (resp.data?.error && resp.data?.error_description) {
        throw new Error(resp.data.error_description);
    }
    const expires_in = resp.data.expires_in + Date.now() / 1000;
    return {
        access_token: resp.data.access_token,
        expires_in,
    };
}