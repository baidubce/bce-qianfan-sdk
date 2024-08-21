module.exports = {
    parser: '@typescript-eslint/parser',
    rules: {
        'comma-dangle': ['error', 'always'],
    },
    extends: [
        '@ecomfe/eslint-config',
    ],
    env: {
        jest: true,
    },
};