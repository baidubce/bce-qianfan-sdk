import babel from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import resolve from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import json from '@rollup/plugin-json';
import eslint from '@rollup/plugin-eslint';
import inject from '@rollup/plugin-inject';
import ignore from 'rollup-plugin-ignore';
import nodePolyfills from 'rollup-plugin-node-polyfills';
import nodeBuiltins from 'rollup-plugin-node-builtins';
import {terser} from 'rollup-plugin-terser';

const isBrowserBuild = format => ['es', 'iife'].includes(format);

const createConfig = output => {
    const plugins = [
        typescript({
            tsconfig: 'tsconfig.json',
        }),
        json(),
        resolve({
            extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
            browser: isBrowserBuild(output.format),
            preferBuiltins: !isBrowserBuild(output.format),
            dedupe: ['buffer'],
        }),
        commonjs(),
        babel({
            babelrc: false,
            configFile: './babel.config.cjs',
            extensions: ['.js', '.jsx', '.ts', '.tsx'],
        }),
        eslint({
            throwOnError: true,
            throwOnWarning: true,
            include: ['src/'],
            exclude: ['node_modules/'],
        }),
        inject({
            Buffer: ['buffer', 'Buffer'],
            crypto: 'crypto-js',
        }),
    ];

    if (isBrowserBuild(output.format)) {
        plugins.push(
            nodePolyfills({
                exclude: ['crypto'],
            }),
            nodeBuiltins()
        );
        plugins.push(ignore(['dotenv', 'os', 'path']));
        plugins.push(terser());
    }

    return {
        input: 'src/index.ts',
        output,
        plugins,
        external: isBrowserBuild(output.format) ? [] : ['dotenv'],
        onwarn: function (warning, warn) {
            if (warning.code === 'CIRCULAR_DEPENDENCY') {
                if (
                    warning.importer?.includes('node_modules/bottleneck')
                    || warning.importer?.includes('node_modules/asn1.js')
                ) {
                    return;
                }
            }
            warn(warning);
        },
    };
};

export default [
    createConfig({
        file: 'dist/bundle.cjs',
        format: 'cjs',
        exports: 'named',
    }),
    createConfig({
        file: 'dist/bundle.esm.js',
        format: 'es',
        preferConst: true,
        exports: 'named',
    }),
    createConfig({
        file: 'dist/bundle.iife.js',
        format: 'iife',
        name: 'QianfanSDK',
        sourcemap: true,
    }),
];
