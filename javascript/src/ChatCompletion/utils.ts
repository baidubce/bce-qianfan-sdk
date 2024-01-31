import {base_host} from '../constant';
import {QfLLMInfo, IAMConfig} from '../interface';

const UNSPECIFIED_MODEL = 'UNSPECIFIED_MODEL';

export interface QfLLMInfoMap {
    [modelName: string]: QfLLMInfo;
}

export const modelInfoMap: QfLLMInfoMap = {
    'ERNIE-Bot-turbo': {
        endpoint: '/chat/eb-instant',
        required_keys: new Set(['messages']),
        optional_keys: new Set([
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'tools',
            'tool_choice',
            'system',
        ]),
    },
    'ERNIE-Bot': {
        endpoint: '/chat/completions',
        required_keys: new Set(['messages']),
        optional_keys: new Set([
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'functions',
            'system',
            'user_id',
            'user_setting',
            'stop',
            'disable_search',
            'enable_citation',
            'max_output_tokens',
            'tool_choice',
        ]),
    },
    'ERNIE-Bot-4': {
        endpoint: '/chat/completions_pro',
        required_keys: new Set(['messages']),
        optional_keys: new Set([
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'functions',
            'system',
            'user_id',
            'stop',
            'disable_search',
            'enable_citation',
            'max_output_tokens',
        ]),
    },
    [UNSPECIFIED_MODEL]: {
        endpoint: '',
        required_keys: new Set(['messages']),
        optional_keys: new Set(),
    },
};

export function getIAMConfig(ak: string, sk: string): IAMConfig {
    return {
        credentials: {
            ak,
            sk,
        },
        endpoint: base_host,
    };
}