import {Headers} from 'node-fetch';
import {Readable} from 'stream';

/**
 * 处理返回的头部信息
 * @param headers Headers
 * @returns
 */
export const extractHeaders = (headers: Headers) => {
    const headersParser = Array.from(headers.entries()).reduce((acc, [key, value]) => {
        return {
            ...acc,
            [key]: value.length === 1 ? value[0] : value
        };
    }, {});
    return JSON.stringify(headersParser);
};

/**
 * 使用stream-to-promise的方式，处理流并将其转换为完整的字符串或缓冲区
 * @param stream
 * @returns Promise<string>
 */
export const getStreamData = (stream: Readable): Promise<string> => {
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        stream.on('data', (chunk: Buffer) => chunks.push(chunk));
        stream.on('end', () => resolve(Buffer.concat(chunks).toString()));
        stream.on('error', reject);
    });
};

export const buildErrorMessage = async (response, contentType, responseHeaders) => {
    const baseMessage = `
        HTTP error, status = ${response.status}\n
        Response Header ${responseHeaders}
    `;

    if (response.body instanceof Readable) {
        const responseBody = await getStreamData(response.body as Readable);
        return `${baseMessage}\nResponse Body ${responseBody}`; // 返回新的错误消息
    }
    return baseMessage; // 返回不可变的错误消息
};
