// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package qianfan

import (
	"context"
	"fmt"
	"path"
	"strings"
	"sync"
	"time"
)

type modelEndpointRetriever struct {
	service    Service
	modelList  map[string]map[string]string
	lock       sync.Mutex
	lastUpdate time.Time
}

var _modelEndpointRetriever *modelEndpointRetriever = nil
var _modelEndpointRetrieverInitOnce sync.Once

func getModelEndpointRetriever() *modelEndpointRetriever {
	_modelEndpointRetrieverInitOnce.Do(func() {
		_modelEndpointRetriever = &modelEndpointRetriever{
			service:    *NewService(),
			modelList:  map[string]map[string]string{},
			lock:       sync.Mutex{},
			lastUpdate: time.Time{},
		}
		initMap := map[string]map[string]string{
			"chat":        ChatModelEndpoint,
			"completions": CompletionModelEndpoint,
			"embeddings":  EmbeddingEndpoint,
			"text2image":  Text2ImageEndpoint,
			"image2text":  make(map[string]string),
		}
		for modelType, endpointMap := range initMap {
			_modelEndpointRetriever.modelList[modelType] = map[string]string{}
			for model, endpoint := range endpointMap {
				_modelEndpointRetriever.modelList[modelType][model] = endpoint
			}
		}
	})
	return _modelEndpointRetriever
}

func (r *modelEndpointRetriever) shouldRefresh() bool {
	return time.Now().After(
		r.lastUpdate.Add(
			time.Second * time.Duration(GetConfig().InferResourceRefreshInterval),
		),
	)
}

func (r *modelEndpointRetriever) GetEndpoint(ctx context.Context, modelType string, name string) string {
	return r.GetModelList(ctx, modelType)[name]
}

func (r *modelEndpointRetriever) GetEndpointWithRefresh(ctx context.Context, modelType string, name string) string {
	r.lock.Lock()
	defer r.lock.Unlock()

	err := r.refreshModelList(ctx)
	if err != nil {
		logger.Errorf("refresh model list failed: %s", err.Error())
		return ""
	}
	return r.modelList[modelType][name]
}

func (r *modelEndpointRetriever) GetModelList(ctx context.Context, modelType string) map[string]string {
	r.lock.Lock()
	defer r.lock.Unlock()
	// 第一次使用时，需要刷新一次
	if r.lastUpdate.IsZero() {
		err := r.refreshModelList(ctx)
		if err != nil {
			logger.Errorf("refresh model list failed: %s, will fallback to preset config", err.Error())
		}
	}
	return r.modelList[modelType]
}

func (r *modelEndpointRetriever) Refresh(ctx context.Context) error {
	r.lock.Lock()
	defer r.lock.Unlock()

	err := r.refreshModelList(ctx)
	if err != nil {
		logger.Errorf("refresh model list failed: %s", err.Error())
		return err
	}
	return nil
}

func extractEndpoint(url string) string {
	_, endpoint := path.Split(url)
	_, apiType := path.Split(strings.TrimSuffix(url, "/"+endpoint))
	return fmt.Sprintf("/%s/%s", apiType, endpoint)
}

func (r *modelEndpointRetriever) refreshModelList(ctx context.Context) error {
	if !r.shouldRefresh() {
		return nil
	}
	defer func() {
		r.lastUpdate = time.Now()
	}()

	if GetConfig().AccessKey == "" || GetConfig().SecretKey == "" {
		logger.Info("AccessKey or SecretKey is empty, skip refresh model list.")
		return nil
	}
	resp, err := r.service.List(ctx, &ServiceListRequest{})
	if err != nil {
		return nil
	}
	for _, model := range append(resp.Result.Common, resp.Result.Custom...) {
		if _, ok := r.modelList[model.APIType]; !ok {
			r.modelList[model.APIType] = map[string]string{}
		}
		r.modelList[model.APIType][model.Name] = extractEndpoint(model.URL)
	}

	logger.Info("Model list is refreshed successfully.")
	return nil
}
