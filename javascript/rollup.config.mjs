import typescript from 'rollup-plugin-typescript2';

export default {
    input: 'src/index.ts',
    output: [
        {
            file: 'dist/bundle.js',
            format: 'umd',
            name: 'MyLibrary',
        },
        {
            file: 'dist/bundle.esm.js',
            format: 'es',
        },
    ],
    plugins: [
        typescript({
            tsconfig: 'tsconfig.json',
        }),
    ],
};
