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

export interface DefaultConfig {
    QIANFAN_AK: string;
    QIANFAN_SK: string;
    QIANFAN_ACCESS_KEY: string;
    QIANFAN_SECRET_KEY: string;
    QIANFAN_BASE_URL: string;
    QIANFAN_CONSOLE_API_BASE_URL: string;
    QIANFAN_LLM_API_RETRY_TIMEOUT: string;
    QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR: string;
    QIANFAN_LLM_RETRY_MAX_WAIT_INTERVAL: string;
    QIANFAN_LLM_API_RETRY_COUNT: string;
    QIANFAN_QPS_LIMIT: string;
    QIANFAN_RPM_LIMIT: string;
    QIANFAN_TPM_LIMIT: string;
    version: string;
    // 浏览器字段是否开启鉴权，是则使用鉴权，否则不使用鉴权
    ENABLE_OAUTH: boolean;
}

/**
 * 公共服务模型信息
 */
export interface QfLLMInfoMap {
    [key: string]: {
        endpoint: string;
        required_keys: string[];
        optional_keys: string[];
    };
}
/**
 * getAccessToken返回值
 */
export interface AccessTokenResp {
    /**
     * 访问凭证ß
     */
    access_token: string;
    /**
     * access_token 有效期。单位秒，有效期30天
     */
    expires_in: number;
    /**
     * 错误码 响应失败时返回该字段，成功时不返回
     */
    error?: string;
    /**
     * 错误描述信息，帮助理解和解决发生的错误，响应失败时返回该字段，成功时不返回
     */
    error_description?: string;
}

export interface IAMConfig {
    credentials: {
        ak: string;
        sk: string;
    };
    endpoint: string;
}

export interface ModelEndpointInfo {
    endpoint: string;
    requiredkey: string;
}

export interface FunctionCall {
    /**
     * 触发的 function 名
     */
    name: string;
    /**
     * 请求参数
     */
    arguments: string;
    /**
     * 模型思考过程
     */
    thoughts?: string;
}

/**
 * 对话消息基类
 */
export interface ChatMessage {
    /**
     * user: 表示用户，assistant: 表示对话助手
     */
    role: 'user' | 'assistant';
    /**
     * 对话内容
     */
    content: string;
    /**
     * message作者；当role=function时，必填，且是响应内容中function_call中的name
     */
    function_call?: FunctionCall;
}

interface baseReq {
    /**
     * 埋点信息
     */
    extra_parameters?: {
        /**
         * 用户信息，用于识别用户身份，如手机号、身份证号等
         */
        request_source?: string;
    };
    /**
     * 表示最终用户的唯一标识符，可以监视和检测滥用行为，防止接口恶意调用
     */
    user_id?: string;
}

/**
 * 对话请求
 */
export interface ChatBody extends baseReq {
    /**
     * 聊天上下文信息
     * 1. messages 成员不能为空，1 个成员表示单轮对话，多个成员表示多轮对话
     * 2. 最后一个 message 为当前请求的信息，前面的 message 为历史对话信息
     * 3. 必须为奇数个成员
     */
    messages: ChatMessage[];
    /**
     * 是否以流式接口的形式返回数据，默认为 false
     */
    stream?: boolean;
    /**
     * 其他额外参数
     */
    [key: string]: any;
}

/**
 * 可触发函数
 */
export type ErnieBotFunction = {
    /**
     * 函数名
     */
    name: string;
    /**
     * 函数描述
     */
    description: string;
    /**
     * 函数请求参数
     * 1. JSON Schema 格式，参考 [JSON Schema描述](https://json-schema.org/understanding-json-schema/)
     * 2. 如果函数没有请求参数，parameters 值格式如下：{"type": "object","properties": {}}
     */
    parameters: object;
    /**
     * 函数响应参数，JSON Schema 格式，参考 [JSON Schema描述](https://json-schema.org/understanding-json-schema/)
     */
    responses: object;
    /**
     * function 调用的一些历史示例
     */
    examples: ChatMessage[];
};

/**
 * token 用量基类
 */
export interface TokenUsageBase {
    /**
     * 问题tokens数
     */
    prompt_tokens: number;
    /**
     * 回答tokens数
     */
    completion_tokens?: number;
    /**
     * tokens总数
     */
    total_tokens: number;
}

/**
 * 插件 token 用量
 */
export interface PluginTokenUsage {
    /**
     * plugin名称，chatFile：chatfile插件消耗的tokens
     */
    name: string;
    /**
     * 解析文档tokens
     */
    parse_tokens: number;
    /**
     * 摘要文档tokens
     */
    abstract_tokens: number;
    /**
     * 检索文档tokens
     */
    search_tokens: number;
    /**
     * 总tokens
     */
    total_tokens: number;
}

/**
 * token 用量（包括插件）
 */
export interface TokenUsageWithPlugins extends TokenUsageBase {
    plugins?: PluginTokenUsage[];
}

/**
 * token 用量
 */
export type TokenUsage = TokenUsageBase;

/**
 * 响应基类
 */
export interface RespBase {
    /**
     * 本轮对话的id
     */
    id: string;
    /**
     * 回包类型。
     *
     * chat.completion：多轮对话返回
     */
    object: string;
    /**
     * 时间戳
     */
    created: number;
    /**
     * 表示当前子句的序号。只有在流式接口模式下会返回该字段
     */
    sentence_id?: number;
    /**
     * 表示当前子句是否是最后一句。只有在流式接口模式下会返回该字段
     */
    is_end?: boolean;
    /**
     * 对话返回结果
     */
    result: string;
    /**
     * 1：表示输入内容无安全风险
     * 0：表示输入内容有安全风险
     */
    is_safe?: number;
    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    usage: TokenUsage;
}

export interface SearchResult {
    /**
     * 序号
     */
    index?: number;
    /**
     * 搜索结果 URL
     */
    url?: string;
    /**
     * 搜索结果标题
     */
    title?: string;
    /**
     * 搜索来源 id 大搜解决死链问题需要透传的字段
     */
    datasource_id?: string;
}

export interface SearchInfo {
    /**
     * 是否飞线
     */
    is_beset?: number;
    /**
     * 改写后的搜索 query
     */
    rewrite_query?: string;
    /**
     * 改写后的搜索 query
     */
    search_results?: SearchResult[];
}

export interface BaiduSearchResult {
    /**
     * 结果序号，从1开始
     */
    index?: number;
    /**
     * 搜索结果页面 url
     */
    url?: string;
    /**
     * 搜索结果页面url
     */
    title?: string;
}

export interface ToolsInfo {
    /**
     * 工具名，目前支持 baidu_search
     */
    name?: string;
    /**
     * query 改写结果，表示在使用工具时使用的 query
     */
    rewrite_query?: string;
    /**
     * 当使用 baidu_search 会返回检索结果
     */
    baidu_search?: BaiduSearchResult[];
    /**
     * qianfan
     */
    usage_agent?: string;
}

export interface Choices {
    /**
     * choice 列表中的序号
     */
    index?: number;
    /**
     * 响应信息
     */
    message?: ChatMessage;
    /**
     * 值为 true 表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息
     */
    need_clear_history?: boolean;
    /**
     * 当 need_clear_history 为 true 时，次字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round = -1
     */
    ban_round?: number;
    /**
     * 由模型生成的函数调用，包含函数名称，和调用参数
     */
    function_call?: FunctionCall;
    /**
     * 搜索数据，请求参数 enable_citation 置 true 并且触发搜索时，会返回对应内容
     */
    search_info?: SearchInfo;
    /**
     * 输出内容标识，取值访问及定义如下：
     * normal：输出内容完全由大模型生成，未触发截断、替换；
     * stop：输出结果命中入参 stop 中指定的字段后被截断；
     * length：达到了最大的 token 数，根据 EB 返回结果 is_truncated 来截断；
     * content_filter：输出内容被截断、兜底、替换为**等；
     * function_call：调用了 funtion call 功能；
     */
    finish_reason?: string;
    /**
     * 返回 flag 表示触发安全
     */
    flag?: number;
    /**
     * tool 使用信息，例如当使用 baidu_search 会返回
     */
    tools_info?: ToolsInfo;
}

export interface SseChoices {
    /**
     * choice 列表中的序号
     */
    index?: number;
    /**
     * 响应信息
     */
    delta?: ChatMessage;
    /**
     * 流式接口模式下会返回，表示当前子句是否是最后一句
     */
    is_end?: boolean;
    /**
     * 值为 true 表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息
     */
    need_clear_history?: boolean;
    /**
     * 当 need_clear_history 为 true 时，次字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round = -1
     */
    ban_round?: number;
    /**
     * 由模型生成的函数调用，包含函数名称，和调用参数
     */
    function_call?: FunctionCall;
    /**
     * 搜索数据，请求参数 enable_citation 置 true 并且触发搜索时，会返回对应内容
     */
    search_info?: SearchInfo;
    /**
     * 输出内容标识，取值访问及定义如下：
     * normal：输出内容完全由大模型生成，未触发截断、替换；
     * stop：输出结果命中入参 stop 中指定的字段后被截断；
     * length：达到了最大的 token 数，根据 EB 返回结果 is_truncated 来截断；
     * content_filter：输出内容被截断、兜底、替换为**等；
     * function_call：调用了 funtion call 功能；
     */
    finish_reason?: string;
    /**
     * 返回 flag 表示触发安全
     */
    flag?: number;
    /**
     * tool 使用信息，例如当使用 baidu_search 会返回
     */
    tools_info?: ToolsInfo;
}

export interface ChatRespV2 {
    /**
     * 响应列表
     * strem = false 时为 choices
     * stream = true 时为 sse_choices
     */
    choices?: Choices | SseChoices;
}

export interface ChatResp extends RespBase {
    /**
     * 当前生成的结果是否被截断
     */
    is_truncated?: boolean;
    /**
     * 表示用户输入是否存在安全，是否关闭当前会话，清理历史会话信息
     *
     * true：是，表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息
     * false：否，表示用户输入无安全风险
     */
    need_clear_history: boolean;
    /**
     * 当 need_clear_history 为 true 时，此字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round=-1
     */
    ban_round: number;
}

/**
 * 对话响应错误
 */
export interface ChatRespError {
    /**
     * 错误码
     */
    error_code: number;
    /**
     * 错误描述信息，帮助理解和解决发生的错误
     */
    error_msg: string;
}

export interface CompletionBodyV2 {
    /**
     * appid 应用ID ，不传使用静默 appid
     */
    appid?: string;
    /**
     * 是否开启排队抢占，错峰使用，开启后响应时间会有所增加，不保证 SLA，默认 false
     * true 开启抢占
     */
    preemptible?: boolean;
    /**
     * 用户画像，仅千亿EB支持，需要开白名单权限
     */
    user_setting?: string;
    /**
     * 返回搜索溯源信息的数量，默认由系统内部指定
     */
    trace_number?: number;
}

export interface CompletionBody extends baseReq, CompletionBodyV2 {
    /**
     * 聊天上下文信息 兼容Chat模型
     * 1. messages 成员不能为空，1 个成员表示单轮对话，多个成员表示多轮对话
     * 2. 最后一个 message 为当前请求的信息，前面的 message 为历史对话信息
     * 3. 必须为奇数个成员
     */
    messages?: ChatMessage[];
    /*
     * 请求信息
     */
    prompt: string;
    /*
     * 是否以流式接口的形式返回数据，默认false
     */
    stream?: boolean;
    /*
     * 1）较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定
     * 2）范围 (0, 1.0]，不能为0
     */
    temperature?: number;
    /*
     *Top-K 采样参数，在每轮token生成时，保留k个概率最高的token作为候选。说明：
     *（1）影响输出文本的多样性，取值越大，生成文本的多样性越强
     *（2）取值范围：正整数
     */
    top_k?: number;
    /*
     *（1）影响输出文本的多样性，取值越大，生成文本的多样性越强
     *（2）取值范围 [0, 1.0]
     */
    top_p?: number;
    /*
     * 通过对已生成的token增加惩罚，减少重复生成的现象。说明：
     *（1）值越大表示惩罚越大
     *（2）取值范围：[1.0, 2.0]
     */
    penalty_score?: number;
    /*
     * 生成停止标识。当模型生成结果以stop中某个元素结尾时，停止文本生成。说明：
     *（1）每个元素长度不超过20字符。
     *（2）最多4个元素
     */
    stop?: string[];
}

export interface EmbeddingBody extends baseReq {
    /**
     * 输入文本以获取embeddings
     *（1）不能为空List，List的每个成员不能为空字符串
     *（2）文本数量不超过16
     * (3）每个文本token数不超过384且长度不超过1000个字符
     */
    input: string[];
}

interface EmbeddingData {
    /**
     * 固定值"embedding"
     */
    object: string;
    /**
     * embedding 内容
     */
    embedding: number[];
    /*
     * 序号
     */
    index: number;
}

export interface EmbeddingResp {
    /**
     * 本轮对话的id
     */
    id: string;
    /**
     * 回包类型, 固定值“embedding_list”
     */
    object: string;
    /**
     * 时间戳
     */
    created: number;
    data: EmbeddingData[];
    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    usage: TokenUsage;
}

export interface Text2ImageBody extends baseReq {
    /**
     * 提示词
     * 即用户希望图片包含的元素。长度限制为1024字符，建议中文或者英文单词总数量不超过150个
     */
    prompt: string;
    /**
     * 反向提示词
     * 即用户希望图片不包含的元素。长度限制为1024字符，建议中文或者英文单词总数量不超过150个
     */
    negative_prompt?: string;
    /**
     * 生成图片长宽
     * 默认值 1024x1024，取值范围: ["768x768", "768x1024", "1024x768", "576x1024", "1024x576", "1024x1024"]
     */
    size?: string;
    /**
     * 生成图片数量，
     * 默认值为1，取值范围为1-4
     */
    n?: number;
    /**
     * 迭代轮次，默认值为20，取值范围为10-50
     */
    steps?: number;
    /**
     * 采样方式，默认值为"Euler a"
     */
    sampler_index?: string;
    /**
     * 随机种子，默认自动生成随机数，取值范围 [0, 4294967295]
     */
    seed?: number;
    /**
     * 提示词相关性，默认值为5，取值范围0-30
     */
    cfg_scale?: number;
    /**
     * 生成风格，默认值为Base
     */
    style?: string;
}

export interface ImageData {
    object: string; // 固定值 "image"
    b64_image: string; // 图片base64编码内容
    index: number; // 序号
}
export interface Text2ImageResp {
    id: string; // 请求的id
    object: string; // 回包类型。例如："image" 表示图像生成返回
    created: number; // 时间戳
    data: ImageData[]; // 生成图片结果
    usage: TokenUsage; // token统计信息
}
export interface PluginsBody extends baseReq {
    /**
     * 查询信息
     * 成员不能为空，长度不能超过1000个字符
     */
    query: string;
    /**
     * 需要调用的插件ID列表
     * 知识库插件固定值为["uuid-zhishiku"]
     * 智慧图问插件固定值为["uuid-chatocr"]
     * 天气插件固定值为["uuid-weatherforecast"]
     */
    plugins: string[];
    /**
     * 文件URL地址
     *（1）图片要求是百度BOS上的图片，即用户必须现将图片上传至百度BOS，图片url地址包含bcebos.com；只有在访问北京区域BOS，才不会产生BOS的外网流出流量费用
     *（2）图片支持jpg、jpeg、png，必须带后缀名
     *（3）图像尺寸最小为80*80，如果图像小于该尺寸，则无法识别
     */
    fileurl?: string;
    /**
     * 是否以流式接口的形式返回数据
     * 默认为false
     */
    stream?: boolean;
    /**
     * llm相关参数
     * 不指定参数时，使用调试过程中的默认值
     * 参数示例："llm":{"temperature":0.1,"top_p":1,"penalty_score":1}
     */
    llm?: {
        temperature: number;
        top_p: number;
        penalty_score: number;
    };
    /**
     * 如果prompt中使用了变量，推理时可以填写具体值
     * 如果prompt中未使用变量，该字段不填
     */
    input_variables?: Record<string, string>;
    /**
     * 聊天上下文信息
     */
    history?: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
    /**
     * 是否返回插件的原始请求信息
     * 默认为false
     */
    verbose?: boolean;
}

export interface YiYanPluginBody extends baseReq {
    /**
     * 聊天上下文信息
     * messages成员不能为空，1个成员表示单轮对话，多个成员表示多轮对话；
     * 最后一个message为当前请求的信息，前面的message为历史对话信息；
     * 必须为奇数个成员，成员中message的role必须依次为user、assistant；
     * 最后一个message的content长度（即此轮对话的问题）不能超过4800个字符；
     * 当messages中content的总长度大于4800字符时，系统会依次遗忘最早的历史QA，直到content的总长度不超过4800字符；
     */
    messages: ChatMessage[];
    /**
     * 需要调用的插件，当前支持["eChart", "ImageAI", "ChatFile"]。
     * 最多3个插件，最少1个插件。插件触发由ERNIE-Bot控制。
     * - ImageAI：最大支持10M以内图片
     * - Chatfile：最大支持10M以内文档
     */
    plugins: ('eChart' | 'ImageAI' | 'ChatFile')[];
    /**
     * 是否以流式接口的形式返回数据；
     * 默认false
     */
    stream?: boolean;
    /**
     * 表示最终用户的唯一标识符，可以监视和检测滥用行为，防止接口恶意调用。
     */
    user_id?: string;
}

interface MetaInfo {
    plugin_id: string; // 插件 Id，为“uuid-zhishiku”
    request: any; // 知识库原始请求参数
    response: any; // 知识库原始返回结果
}

export interface PluginsResp {
    /**
     * 唯一的log id，用于问题定位
     */
    log_id: number;
    /**
     * 本轮对话的id
     */
    id: string;
    /**
     * 回包类型。例如 chat.completion：多轮对话返回
     */
    object: string;
    /**
     * 时间戳
     */
    created: number;
    /**
     * 表示当前子句的序号，只有在流式接口模式下会返回该字段
     */
    sentence_id?: number;
    /**
     * 表示当前子句是否是最后一句，只有在流式接口模式下会返回该字段
     */
    is_end?: boolean;
    /**
     * 插件返回结果
     */
    result: string;
    /**
     * 当前生成的结果是否被截断
     */
    is_truncated: boolean;
    /**
     * 表示用户输入是否存在安全风险，是否关闭当前会话，清理历史会话信息
     * true：是，表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息
     * false：否，表示用户输入无安全风险
     */
    need_clear_history: boolean;
    /**
     * 当need_clear_history为true时，此字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round = -1
     */
    ban_round?: number;
    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    usage: TokenUsage;
    /**
     * 插件的原始请求信息
     */
    meta_info?: MetaInfo; // 根据实际meta_info的结构进一步定义
}

export interface Image2TextBody extends baseReq {
    /**
     * 请求信息
     */
    prompt: string;
    /**
     * 图片数据，说明：base64编码，要求base64编码后大小不超过4M，最短边至少15px，最长边最大4096px，支持jpg/png/bmp格式，注意请去掉头部
     */
    image: string;
    /**
     * 是否以流式接口的形式返回数据，默认false
     */
    stream?: boolean;
    /**
     * 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定。范围 (0, 1.0]，不能为0
     */
    temperature?: number;
    /**
     * Top-K 采样参数，在每轮token生成时，保留k个概率最高的token作为候选。影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围：正整数
     */
    top_k?: number;
    /**
     * 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
     */
    top_p?: number;
    /**
     * 通过对已生成的token增加惩罚，减少重复生成的现象。值越大表示惩罚越大。取值范围：[1.0, 2.0]
     */
    penalty_score?: number;
    /**
     * 生成停止标识。当模型生成结果以stop中某个元素结尾时，停止文本生成。每个元素长度不超过20字符。最多4个元素
     */
    stop?: string[];
}

export interface RerankerBody extends baseReq {
    /**
     * 查询文本
     * 长度不超过1600个字符，token数若超过400做截断
     */
    query: string;
    /**
     * 需要重排序的文本
     *（1）不能为空List，List的每个成员不能为空字符串
     *（2）文本数量不超过64
     *（3）每条document文本长度不超过4096个字符，token数若超过1024做截断
     */
    documents: string[];
    /**
     * 返回的最相关文本的数量
     * 默认为document的数量
     */
    top_n?: number;
}

type RerankerData = {
    /**
     * 文本内容
     */
    document: string;
    /**
     * 相似性得分
     */
    relevance_score: number;
    /**
     * 序号
     */
    index: number;
};
type UsageType = {
    /**
     * 问题tokens数（包含历史QA）
     */
    prompt_tokens: number;
    /**
     * tokens总数
     */
    total_tokens: number;
};

export interface RerankerResp {
    /**
     * 本轮对话的id
     */
    id: string;
    /**
     * 回包类型, 固定值“rerank_list”
     */
    object: string;
    /**
     * 时间戳
     */
    created: number;
    /**
     * 重排序结果，按相似性得分倒序
     */
    results: RerankerData[];
    usage: UsageType;
}

export type ReqBody = ChatBody | CompletionBody | EmbeddingBody | PluginsBody | Text2ImageBody | RerankerBody;
export type Resp = RespBase | ChatResp | EmbeddingResp | PluginsResp | Text2ImageResp | RerankerResp;
export type AsyncIterableType = AsyncIterable<ChatResp | RespBase | PluginsResp>;
