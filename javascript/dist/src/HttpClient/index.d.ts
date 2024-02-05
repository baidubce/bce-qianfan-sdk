/// <reference types="node" />
/// <reference types="node" />
/// <reference types="node" />
import * as stream from 'stream';
import { EventEmitter } from 'events';
import * as Q from 'q';
declare class HttpClient extends EventEmitter {
    private config;
    private readonly defaultHeaders;
    private axiosInstance;
    constructor(config: any);
    sendRequest(httpMethod: string, path: string, body?: string | Buffer | stream.Readable, headers?: Record<string, any>, params?: Record<string, any>, signFunction?: () => [string, string] | string, outputStream?: stream.Writable): Q.Promise<any>;
    private _doRequest;
    private _recvResponse;
    private failure;
    private setAuthorizationHeader;
    private _getRequestUrl;
    private buildQueryString;
    private _guessContentLength;
    private isPromise;
    private createSignature;
}
export default HttpClient;
