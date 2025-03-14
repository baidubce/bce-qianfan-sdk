package com.baidubce.qianfan.core.auth;

import com.baidubce.qianfan.core.QianfanConfig;
import com.baidubce.qianfan.model.chat.v2.other.BearerTokenResponse;
import com.baidubce.qianfan.model.exception.QianfanException;
import com.baidubce.qianfan.model.exception.RequestException;
import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.http.HttpRequest;
import com.baidubce.qianfan.util.http.HttpResponse;

import java.time.Duration;
import java.time.Instant;

public class QianfanV2Auth implements IAuth {
    private static final String BEAR_TOKEN_APPLY_URL = "%s/v1/BCE-BEARER/token?expireInSeconds=%d";
    private static final Duration FAILING_OFFSET = Duration.ofSeconds(10);
    private final IAMAuth auth;
    private final Boolean isPreset;

    private String token;
    private Instant expiredTime;

    public QianfanV2Auth(String accessKey, String secretKey) {
        this.auth = new IAMAuth(accessKey, secretKey);
        this.isPreset = false;
    }

    public QianfanV2Auth(String token) {
        this.auth = null;
        this.token = token;
        this.isPreset = true;

        if (!this.token.startsWith("Bearer ")) {
            this.token = "Bearer " + this.token;
        }
    }

    @Override
    public String authType() {
        return Auth.TYPE_V2;
    }

    @Override
    public IAuth convertToV2() {
        return this;
    }

    @Override
    public HttpRequest signRequest(HttpRequest request) {
        return request
                .addHeader("Content-Type", "application/json")
                .addHeader("Authorization", getToken());
    }

    public void applyNewBearToken() {
        String url = String.format(
                BEAR_TOKEN_APPLY_URL,
                QianfanConfig.getIAMBaseUrl(),
                QianfanConfig.getIamSignExpirationSec()
        );

        HttpRequest iamRequest = this.auth.signRequest(new HttpRequest().get(url));
        try {
            HttpResponse<String> response = iamRequest.executeString();

            BearerTokenResponse bearerTokenResponse = Json.deserialize(
                    response.getStringBody(), BearerTokenResponse.class
            );
            this.token = String.format("Bearer %s", bearerTokenResponse.getToken());
            this.expiredTime = Instant.parse(bearerTokenResponse.getExpireTime());
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Auth request failed: %s", e.getMessage()), e);
        }
    }

    public String getToken() {
        if (!this.isPreset && this.isExpired()) {
            synchronized (this) {
                if (this.isExpired()) {
                    this.applyNewBearToken();
                }
            }
        }
        return token;
    }

    public boolean isExpired() {
        if (this.expiredTime == null || this.token == null) {
            return true;
        }

        return Duration.between(Instant.now(), this.expiredTime).compareTo(FAILING_OFFSET) <= 0;
    }
}
