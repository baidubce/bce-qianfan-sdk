import axios from 'axios';

/**
 * 获取 AccessToken
 *
 * @param API_KEY API 密钥
 * @param SECRET_KEY 密钥
 * @returns 返回 AccessToken
 * @throws 如果获取 AccessToken 失败，则抛出错误
 */
async function getAccessToken(API_KEY, SECRET_KEY) {
    try {
        // 使用 encodeURIComponent 对参数进行 URL 编码，以提高安全性
        const encodedAPIKey = encodeURIComponent(API_KEY);
        const encodedSecretKey = encodeURIComponent(SECRET_KEY);
        const response = await axios.post(`https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${encodedAPIKey}&client_secret=${encodedSecretKey}`);
        const { access_token } = response.data;
        return access_token;
    }
    catch (error) {
        throw new Error(`Failed to get access token: ${error.message}`);
    }
}

function multiply(num1, num2) {
    return num1 * num2;
}

export { getAccessToken, multiply };
