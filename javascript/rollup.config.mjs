import json from '@rollup/plugin-json';
import commonjs from '@rollup/plugin-commonjs';
import resolve from '@rollup/plugin-node-resolve';
import babel from '@rollup/plugin-babel';
import typescript from '@rollup/plugin-typescript';
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
        commonjs(),
        babel({
            extensions: ['.js', '.ts'],
            babelHelpers: 'bundled',
            presets: [
                '@babel/preset-env',
                '@babel/preset-typescript',
            ],
        }),
        eslint({
            throwOnError: true,
            throwOnWarning: true,
            include: ['src/'],
            exclude: ['node_modules/'],
        }),
    ],
};
