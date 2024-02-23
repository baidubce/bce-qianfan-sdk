declare class Auth {
    private ak;
    private sk;
    constructor(ak: string, sk: string);
    generateAuthorization(method: string, resource: string, params?: Record<string, any>, headers?: Record<string, any>, timestamp?: number, expirationInSeconds?: number, headersToSign?: string[]): string;
    private normalize;
    private getTimestamp;
    private generateCanonicalUri;
    private queryStringCanonicalization;
    private headersCanonicalization;
    private hash;
}
export default Auth;
