
/**
 * 对话请求公共服务模型信息
 */
export interface QfLLMInfo {
    endpoint: string;
    required_keys: Set<string>;
    optional_keys: Set<string>;
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
}

export interface IAMConfig{
    credentials: {
        ak: string;
        sk: string;
    };
    endpoint: string;
}
/**
 * 对话请求公共服务模型列表
 */
export type ChatModel =
    | 'ERNIE-Bot-4'
    | 'ERNIE-Bot-8K'
    | 'ERNIE-Bot'
    | 'ERNIE-Bot-turbo'
    | 'EB-turbo-AppBuilder'
    | 'Yi-34B-Chat'
    | 'BLOOMZ-7B'
    | 'Qianfan-BLOOMZ-7B-compressed'
    | 'Llama-2-7b-chat'
    | 'Llama-2-13b-chat'
    | 'Llama-2-70b-chat'
    | 'Qianfan-Chinese-Llama-2-7B'
    | 'Qianfan-Chinese-Llama-2-13B'
    | 'ChatGLM2-6B-32K'
    | 'XuanYuan-70B-Chat-4bit'
    | 'ChatLaw'
    | 'AquilaChat-7B';

/**
 * 对话请求公共服务模型信息
 */
export type ChatModelInfo = Record<
    ChatModel,
    {
        /**
         * API 请求节点
         */
        endpoint: string;
        /**
         * 模型描述
         */
        description?: string;
    }
>;

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
export interface ChatMessageBase {
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
}

/**
 * 带function的对话消息
 */
export interface ChatMessageWithFunction {
    /**
     * function: 表示函数
     */
    role: 'function';
    /**
     * 对话内容，可为空
     */
    content?: string;
    /**
     * message 作者，是 function_call 中的 name
     */
    name: string;
    function_call: FunctionCall;
}

/**
 * 对话消息
 */
export type ChatMessage<T extends ChatModel> = T extends 'ERNIE-Bot-4'
    ? ChatMessageBase | ChatMessageWithFunction
    : T extends 'ERNIE-Bot-8K'
    ? ChatMessageBase | ChatMessageWithFunction
    : T extends 'ERNIE-Bot'
    ? ChatMessageBase | ChatMessageWithFunction
    : ChatMessageBase;

/**
 * 对话请求基类
 */
export interface ChatBodyBase<T extends ChatModel> {
    /**
     * 聊天上下文信息
     * 1. messages 成员不能为空，1 个成员表示单轮对话，多个成员表示多轮对话
     * 2. 最后一个 message 为当前请求的信息，前面的 message 为历史对话信息
     * 3. 必须为奇数个成员
     */
    messages: ChatMessage<T>[];
    /**
     * 是否以流式接口的形式返回数据，默认为 false（当前版本 SDK 未实现流式接口支持）
     */
    stream?: false;
    /**
     * 表示最终用户的唯一标识符，可以监视和检测滥用行为，防止接口恶意调用
     */
    user_id?: string;
}

/**
 * ERNIE-Bot-turbo 对话请求
 */
export interface ChatBodyErnieBotTurbo<T extends ChatModel>
    extends ChatBodyBase<T> {
    /**
     * 1. 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定
     * 2. 默认 0.95，范围 (0, 1.0]，不能为 0
     * 3. 建议该参数和 top_p 只设置1个
     * 4. 建议 top_p 和 temperature 不要同时更改
     */
    temperature?: number;
    /**
     * 1. 影响输出文本的多样性，取值越大，生成文本的多样性越强
     * 2. 默认 0.8，取值范围 [0, 1.0]
     * 3. 建议该参数和 temperature 只设置 1 个
     * 4. 建议 top_p 和 temperature 不要同时更改
     */
    top_p?: number;
    /**
     * 通过对已生成的token增加惩罚，减少重复生成的现象。说明：
     * 1. 值越大表示惩罚越大
     * 2. 默认 1.0，取值范围：[1.0, 2.0]
     */
    penalty_score?: number;
    /**
     * 模型人设，主要用于人设设定，例如，你是 xxx 公司制作的AI助手，说明：
     * 1. 长度限制 1024 个字符
     * 2. 如果使用 functions 参数，不支持设定人设 system
     */
    system?: string;
}

/**
 * 可触发函数
 */
export type ErnieBotFunction<T extends ChatModel> = {
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
    examples: ChatMessage<T>[];
};

/**
 * ERNIE-Bot 和 ERNIE-Bot-4 对话请求
 */
export interface ChatBodyErnieBot<T extends ChatModel>
    extends ChatBodyErnieBotTurbo<T> {
    /**
     * 一个可触发函数的描述列表
     */
    functions?: ErnieBotFunction<T>[];
}

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
    completion_tokens: number;
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
export type TokenUsage<T extends ChatModel> = T extends 'ERNIE-Bot-4'
    ? TokenUsageWithPlugins
    : T extends 'ERNIE-Bot-8K'
    ? TokenUsageWithPlugins
    : T extends 'ERNIE-Bot'
    ? TokenUsageWithPlugins
    : TokenUsageBase;

/**
 * 对话响应基类
 */
export interface ChatRespBase<T extends ChatModel> {
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
     * 当前生成的结果是否被截断
     */
    is_truncated?: boolean;
    /**
     * 对话返回结果
     */
    result: string;
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
    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    usage: TokenUsage<T>;
}

/**
 * ERNIE-Bot 和 ERNIE-Bot-4 对话响应
 */
export interface ChatRespErnieBot<T extends ChatModel> extends ChatRespBase<T> {
    /**
     * 由模型生成的函数调用，包含函数名称，和调用参数
     */
    function_call?: FunctionCall;
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

/**
 * 对话请求参数
 */
export type ChatBody<T extends ChatModel> = T extends 'ERNIE-Bot-4'
    ? ChatBodyErnieBot<T>
    : T extends 'ERNIE-Bot-8K'
    ? ChatBodyErnieBot<T>
    : T extends 'ERNIE-Bot'
    ? ChatBodyErnieBot<T>
    : T extends 'ERNIE-Bot-turbo'
    ? ChatBodyErnieBotTurbo<T>
    : ChatBodyBase<T> & {extra_parameters?: unknown};

/**
 * 对话响应
 */
export type ChatResp<T extends ChatModel> = T extends 'ERNIE-Bot-4'
    ? ChatRespErnieBot<T>
    : T extends 'ERNIE-Bot-8K'
    ? ChatRespErnieBot<T>
    : T extends 'ERNIE-Bot'
    ? ChatRespErnieBot<T>
    : T extends 'ERNIE-Bot-turbo'
    ? ChatRespErnieBot<T>
    : ChatRespBase<T>;