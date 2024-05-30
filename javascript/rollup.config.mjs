import babel from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import resolve from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import json from '@rollup/plugin-json';
import eslint from '@rollup/plugin-eslint';
import inject from '@rollup/plugin-inject';
import ignore from 'rollup-plugin-ignore';
import nodeGlobals from 'rollup-plugin-node-globals';
import nodePolyfills from 'rollup-plugin-node-polyfills';
import nodeBuiltins from 'rollup-plugin-node-builtins';

const isBrowserBuild = format => ['es', 'iife'].includes(format);

const createConfig = output => {
    const plugins = [
        typescript({
            tsconfig: 'tsconfig.json',
        }),
        json(),
        resolve({
            browser: isBrowserBuild(output.format),
            preferBuiltins: !isBrowserBuild(output.format),
            dedupe: ['buffer'],
        }),
        commonjs(),
        babel({
            extensions: ['.js', '.ts'],
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
        inject({
            Buffer: ['buffer', 'Buffer'],
            crypto: 'crypto-js',
        }),
    ];

    if (isBrowserBuild(output.format)) {
        plugins.push(
            nodeGlobals(),
            nodePolyfills({
                exclude: ['crypto'],
            }),
            nodeBuiltins()
        );
        plugins.push(ignore(['dotenv', 'os', 'path']));
    }

    return {
        input: 'src/index.ts',
        output,
        plugins,
        external: isBrowserBuild(output.format) ? [] : ['dotenv'],
        onwarn: function (warning, warn) {
            if (warning.code === 'CIRCULAR_DEPENDENCY') {
                if (warning.importer?.includes('node_modules/bottleneck') || warning.importer?.includes('node_modules/asn1.js')) {
                    return;
                }
            }
            warn(warning);
        },
    };
};

export default [
    createConfig({
        file: 'dist/bundle.cjs.js',
        format: 'cjs',
    }),
    createConfig({
        file: 'dist/bundle.esm.js',
        format: 'es',
    }),
    createConfig({
        file: 'dist/bundle.iife.js',
        format: 'iife',
        name: 'QianfanSDK',
        sourcemap: true,
    }),
];
