package qianfan

import "github.com/mitchellh/mapstructure"

func dumpToMap(input interface{}) (map[string]interface{}, error) {
	target := map[string]interface{}{}
	err := mapstructure.Decode(input, &target)
	if err != nil {
		return nil, err
	}
	return target, nil

}
