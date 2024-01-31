import axios from 'axios';

/**
 * 认证函数，使用 API_KEY 和 SECRET_KEY 进行 HTTP Basic Auth 认证
 *
 * @param API_KEY API 密钥
 * @param SECRET_KEY 密钥
 * @returns 返回 Promise<AccessTokenRes> 认证结果对象，包含 access_token 和 expires_in
 * @throws 如果认证失败，抛出错误信息
 */
async function getAccessToken(API_KEY, SECRET_KEY) {
    try {
        // 使用encodeURIComponent对参数进行编码
        const encodedAPIKey = encodeURIComponent(API_KEY);
        const encodedSecretKey = encodeURIComponent(SECRET_KEY);
        const response = await axios.post(`https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${encodedAPIKey}&client_secret=${encodedSecretKey}`);
        console.log(response.data);
        return response.data.access_token;
    }
    catch (error) {
        // 包装错误消息并提供更多上下文
        throw new Error(`Failed to get access token: ${error.message}`);
    }
}

function multiply(num1, num2) {
    return num1 * num2;
}

export { getAccessToken, multiply };
