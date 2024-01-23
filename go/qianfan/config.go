package qianfan

import (
	"github.com/spf13/viper"
)

type Config struct {
	AccessKey                string `mapstructure:"QIANFAN_ACCESS_KEY"`
	SecretKey                string `mapstructure:"QIANFAN_SECRET_KEY"`
	BaseURL                  string `mapstructure:"QIANFAN_BASE_URL"`
	IAMSignExpirationSeconds int    `mapstructure:"QIANFAN_IAM_SIGN_EXPIRATION_SEC"`
}

func setConfigDeafultValue(vConfig *viper.Viper) {
	defConfig := map[string]string{
		"QIANFAN_ACCESS_KEY":              "",
		"QIANFAN_SECRET_KEY":              "",
		"QIANFAN_BASE_URL":                "https://aip.baidubce.com",
		"QIANFAN_IAM_SIGN_EXPIRATION_SEC": "300",
	}
	for k, v := range defConfig {
		vConfig.SetDefault(k, v)
	}
}

func loadConfigFromEnv() (*Config, error) {
	vConfig := viper.New()

	vConfig.SetConfigFile(".env")
	vConfig.SetConfigType("env")
	vConfig.AutomaticEnv()
	setConfigDeafultValue(vConfig)

	// ignore error if config file not found
	_ = vConfig.ReadInConfig()

	config := &Config{}
	if err := vConfig.Unmarshal(&config); err != nil {
		return nil, err
	}
	return config, nil
}
