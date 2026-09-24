import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import type * as PluginContentDocs from '@docusaurus/plugin-content-docs';
import type * as ThemeSearchLocal from '@easyops-cn/docusaurus-search-local';

const config: Config = {
  title: 'Справка МИС «Инфоклиника»',
  tagline: 'Подключение к ЕГИСЗ, настройка служебных модулей и сопровождение обмена',

  future: {
    v4: true,
  },

  url: 'http://localhost:3006',
  baseUrl: '/',

  organizationName: 'sds',
  projectName: 'egisz-docs-stand',

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  i18n: {
    defaultLocale: 'ru',
    locales: ['ru'],
  },

  markdown: {
    mermaid: true,
    format: 'detect',
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  themes: [
    '@docusaurus/theme-mermaid',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['ru', 'en'],
        indexDocs: true,
        indexBlog: false,
        indexPages: false,
        docsRouteBasePath: ['/', '/internal'],
      } satisfies ThemeSearchLocal.PluginOptions,
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          lastVersion: '26.1',
          versions: {
            current: {
              label: 'trunk — тестовый стенд',
              path: 'trunk',
              banner: 'none',
            },
            '26.1': {
              label: '26.1 — снимок стенда',
              banner: 'none',
            },
            '25.2': {
              label: '25.2 — макет',
              banner: 'none',
            },
          },
        } satisfies Partial<PluginContentDocs.Options>,
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'internal',
        path: 'internal',
        routeBasePath: 'internal',
        sidebarPath: './sidebarsInternal.ts',
      } satisfies Partial<PluginContentDocs.Options>,
    ],
  ],

  themeConfig: {
    announcementBar: {
      id: 'editorial-stand',
      content: 'Тестовый стенд. Инструкции требуют проверки на используемой версии МИС. Снимки 26.1 и 25.2 не являются утверждёнными выпусками руководства.',
      isCloseable: false,
    },
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Инфоклиника: справка',
      items: [
        {
          to: '/trunk/egisz/',
          position: 'left',
          label: 'ЕГИСЗ',
        },
        {
          to: '/trunk/services1/',
          position: 'left',
          label: 'Служебные модули',
        },
        {
          to: '/internal/egisz/',
          label: 'Внутреннее (ЛТП)',
          position: 'left',
        },
        {
          type: 'docsVersionDropdown',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `СДС — локальный тестовый стенд документации, не для публикации`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
