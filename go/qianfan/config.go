package qianfan

import (
	"fmt"

	"github.com/mitchellh/mapstructure"
	"github.com/spf13/viper"
)

var defaultConfig = map[string]string{
	"QIANFAN_ACCESS_KEY":              "",
	"QIANFAN_SECRET_KEY":              "",
	"QIANFAN_BASE_URL":                "https://aip.baidubce.com",
	"QIANFAN_IAM_SIGN_EXPIRATION_SEC": "300",
}

type Config struct {
	AccessKey                string `mapstructure:"QIANFAN_ACCESS_KEY"`
	SecretKey                string `mapstructure:"QIANFAN_SECRET_KEY"`
	BaseURL                  string `mapstructure:"QIANFAN_BASE_URL"`
	IAMSignExpirationSeconds int    `mapstructure:"QIANFAN_IAM_SIGN_EXPIRATION_SEC"`
}

func setConfigDeafultValue(vConfig *viper.Viper) {
	for k, v := range defaultConfig {
		vConfig.SetDefault(k, v)
	}
}

func DefConfig() *Config {
	var config Config
	err := mapstructure.Decode(defaultConfig, &config)
	if err != nil {
		e := fmt.Sprintf("decode default config failed with error `%v`, this maybe a bug in qianfan sdk. please report.", err)
		panic(e)
	}
	return &config
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
