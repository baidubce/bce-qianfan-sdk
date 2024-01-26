/**
 * getAccessToken 返回值
 */
export interface AccessTokenRes {
    /**
     * 访问凭证
     */
    access_token: string;
    /**
     * access_token 有效期。单位秒，有效期 30 天
     */
    expires_in: number;
}