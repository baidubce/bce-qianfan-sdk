module.exports = {
    presets: [
        [
            '@babel/preset-env',
            {
                'targets': {
                    'node': 'current',
                },
                'modules': false,
                'useBuiltIns': 'usage',
            },
        ],
        '@babel/preset-react',
        '@babel/preset-typescript',
    ],
};
