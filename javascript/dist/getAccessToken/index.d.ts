/**
 * 认证函数，使用 API_KEY 和 SECRET_KEY 进行 HTTP Basic Auth 认证
 *
 * @param API_KEY API 密钥
 * @param SECRET_KEY 密钥
 * @returns 返回 Promise<AccessTokenRes> 认证结果对象，包含 access_token 和 expires_in
 * @throws 如果认证失败，抛出错误信息
 */
export declare function getAccessToken(API_KEY: any, SECRET_KEY: any): Promise<any>;
