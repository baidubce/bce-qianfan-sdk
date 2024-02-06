package qianfan

type AccessTokenRequest struct {
	GrantType    string `json:"grant_type"`
	ClientId     string `json:"client_id"`
	ClientSecret string `json:"client_secret"`
}

type AccessTokenResponse struct {
	AccessToken      string `json:"access_token"`
	ExpiresIn        int    `json:"expires_in"`
	Error            string `json:"error"`
	ErrorDescription string `json:"error_description"`
	SessionKey       string `json:"session_key"`
	RefreshToken     string `json:"refresh_token"`
	Scope            string `json:"scope"`
	SessionSecret    string `json:"session_secret"`
}

func GetAccessToken() (string, error) {

}
