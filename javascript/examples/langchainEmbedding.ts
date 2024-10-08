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

import { BaiduQianfanEmbeddings } from "@langchain/baidu-qianfan";

// 参数传AK/SK。如果预设了环境变量QIANFAN_AK/QIANFAN_SK，则可以不用传
const embeddings = new BaiduQianfanEmbeddings({qianfanAK: '*****', qianfanSK: '*****'});

// 参数传ACCESS_KEY/SECRET_KEY。如果预设了环境变量QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY，则可以不用传
// const embeddings = new BaiduQianfanEmbeddings({qianfanAccessKey: '*****', qianfanSecretKey: '*****'});

const res = await embeddings.embedQuery("Introduce the city Beijing");