import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'
import { UI_REV } from './src/constants/ui'

const uiAssetTag = `ui-rev-${UI_REV}`

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'YahahaCoverStudio',
      filename: 'remoteEntry.js',
      exposes: {
        './Page': './src/components/Page.vue',
        './Config': './src/components/Config.vue',
        './Dashboard': './src/components/Dashboard.vue',
      },
      shared: {
        vue: {
          requiredVersion: false,
          generate: false,
        },
        vuetify: {
          requiredVersion: false,
          generate: false,
          singleton: true,
        },
        'vuetify/styles': {
          requiredVersion: false,
          generate: false,
          singleton: true,
        },
      },
      format: 'esm',
    }),
  ],
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: true,
    outDir: '../plugins.v2/yahahacoverstudio/dist',
    rollupOptions: {
      input: {},
      output: {
        entryFileNames: `assets/[name]-${uiAssetTag}.js`,
        chunkFileNames: `assets/[name]-${uiAssetTag}.js`,
        assetFileNames: `assets/[name]-${uiAssetTag}[extname]`,
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: '/* override vuetify styles */',
      },
    },
    postcss: {
      plugins: [
        {
          postcssPlugin: 'internal:charset-removal',
          AtRule: {
            charset: (atRule: any) => {
              if (atRule.name === 'charset') {
                atRule.remove()
              }
            },
          },
        },
        {
          postcssPlugin: 'vuetify-filter',
          Root(root: any) {
            root.walkRules((rule: any) => {
              if (rule.selector && (rule.selector.includes('.v-') || rule.selector.includes('.mdi-'))) {
                rule.remove()
              }
            })
          },
        },
      ],
    },
  },
  server: {
    port: 5001,
    cors: true,
    origin: 'http://localhost:5001',
  },
})
