import {defineConfig} from 'vite';

export default defineConfig({
    plugins: [],
    build: {
        lib: {
            entry: 'packages/index.ts',
            name: 'qianfan-sdk',
            fileName: format => `qianfan-sdk.${format}.js`,
        },
        rollupOptions: {
            external: ['react', 'svg'],
        },
    },
});