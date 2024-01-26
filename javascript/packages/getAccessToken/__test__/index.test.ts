import {getAccessToken} from '../index';
import {expect, describe, it} from 'vitest';

describe('getAccessToken', () => {
    const API_KEY = 'test_api_key';
    const SECRET_KEY = 'test_secret_key';

    it('the data is access_token', async () => {
        const data = await getAccessToken(API_KEY, SECRET_KEY);
        expect(data).toBe({
            access_token: 'mock_access_token',
            expires_in: 3600,
        });
    });
});