package qianfan

import (
	"context"
)

type Service struct {
	consoleBase
}

type ServiceListRequest struct {
	BaseRequestBody `mapstructure:"-"`
	APITypeFilter   *[]string `mapstructure:"apiTypeFilter,omitempty"`
}

type ServiceListResponse struct {
	Result ServiceListResponseResult `json:"result"`
	ConsoleResponse
}

type ServiceListResponseResult struct {
	Common []ServiceListItem `json:"common"`
	Custom []ServiceListItem `json:"custom"`
}

type ServiceListItem struct {
	ServiceID    string                   `json:"serviceId"`
	ServiceUUID  string                   `json:"serviceUuid"`
	Name         string                   `json:"name"`
	URL          string                   `json:"url"`
	APIType      string                   `json:"apiType"`
	ChargeStatus string                   `json:"chargeStatus"`
	VersionList  []ServiceListItemVersion `json:"versionList"`
}

type ServiceListItemVersion struct {
	AIModelID        string `json:"aiModelId,omitempty"`
	AIModelVersionID string `json:"aiModelVersionId,omitempty"`
	TrainType        string `json:"trainType"`
	ServiceStatus    string `json:"serviceStatus"`
}

func (service *Service) List(ctx context.Context, request *ServiceListRequest) (*ServiceListResponse, error) {
	var s ServiceListResponse
	req, err := newConsoleRequest("POST", serviceListURL, request)
	if err != nil {
		return nil, err
	}
	err = service.requestResource(ctx, req, &s)
	if err != nil {
		return nil, err
	}
	return &s, nil
}

func NewService(optionList ...Option) *Service {
	options := makeOptions(optionList...)
	return &Service{
		consoleBase{
			Requestor: newRequestor(options),
		},
	}
}
