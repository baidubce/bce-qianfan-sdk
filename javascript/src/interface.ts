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
}

export interface IAMConfig{
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

/**
 * 对话请求
 */
export interface ChatBody {
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
     * 表示最终用户的唯一标识符，可以监视和检测滥用行为，防止接口恶意调用
     */
    user_id?: string;
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
export type TokenUsage = TokenUsageBase;

/**
 * 响应基类
 */
export interface RespBase{
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
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    usage: TokenUsage;
}

export interface ChatResp extends RespBase{
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


export interface CompletionBody {
    /*
    * 请求信息
    */
    prompt:	string,
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
    penalty_score? :number;	
    /*
    * 生成停止标识。当模型生成结果以stop中某个元素结尾时，停止文本生成。说明：
    *（1）每个元素长度不超过20字符。
    *（2）最多4个元素
    */
    stop?: string[];
    /*
    * 表示最终用户的唯一标识符
    */
    user_id?: string;
    extra_parameters?: {
        /**
         * 用户信息，用于识别用户身份，如手机号、身份证号等
         */
        request_source?: string;
    };
}

