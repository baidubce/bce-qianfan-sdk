module.exports = {
    parser: '@typescript-eslint/parser',
    rules: {
        'comma-dangle': ['error', 'always-multiline']
    },
    extends: [
        '@ecomfe/eslint-config',
    ],
    env: {
        jest: true,
    },
};