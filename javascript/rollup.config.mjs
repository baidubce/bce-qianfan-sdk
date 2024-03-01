import typescript from 'rollup-plugin-typescript2';
import json from '@rollup/plugin-json';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import eslint from '@rollup/plugin-eslint';

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
        json(),
        resolve(),
        commonjs({
            include: /node_modules/,
        }),
        eslint({
            throwOnError: true,
            throwOnWarning: true,
            include: ['src/'],
            exclude: ['node_modules/'],
        }),
    ],
};
