import { getAccessToken } from "../index";
import axios, { AxiosResponse } from 'axios';

jest.mock('axios');

describe('getAccessToken', () => {
    const API_KEY = 'api_key_placeholder';
    const SECRET_KEY = 'secret_key_placeholder';

    it('should return access token when API call is successful', async () => {
        // Arrange
        const expectedAccessToken = 'expected_access_token';
        const mockResponse: AxiosResponse = {
            data: { access_token: expectedAccessToken },
            status: 200,
            statusText: 'OK',
            headers: {},
            config: {
                headers: undefined
            },
        };

        (axios.post as jest.MockedFunction<typeof axios.post>).mockResolvedValueOnce(mockResponse);

        // Act
        const accessToken = await getAccessToken(API_KEY, SECRET_KEY);

        // Assert
        expect(accessToken).toBe(expectedAccessToken);
    });
});