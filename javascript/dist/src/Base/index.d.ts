import { AxiosInstance } from 'axios';
import { Resp, AsyncIterableType } from '../interface';
export declare class BaseClient {
    protected controller: AbortController;
    protected QIANFAN_AK?: string;
    protected QIANFAN_SK?: string;
    protected QIANFAN_ACCESS_KEY?: string;
    protected QIANFAN_SECRET_KEY?: string;
    protected Endpoint?: string;
    protected headers: {
        'Content-Type': string;
        Accept: string;
    };
    protected axiosInstance: AxiosInstance;
    access_token: string;
    expires_in: number;
    constructor(options?: {
        QIANFAN_AK?: string;
        QIANFAN_SK?: string;
        QIANFAN_ACCESS_KEY?: string;
        QIANFAN_SECRET_KEY?: string;
        Endpoint?: string;
    });
    /**
     * 使用 AK，SK 生成鉴权签名（Access Token）
     * @return string 鉴权签名信息（Access Token）
     */
    private getAccessToken;
    protected sendRequest(IAMpath: string, AKPath: string, requestBody: string, stream?: boolean): Promise<Resp | AsyncIterableType>;
}
