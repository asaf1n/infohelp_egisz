import path from 'path';
import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import type * as PluginContentDocs from '@docusaurus/plugin-content-docs';
import type * as PluginClientRedirects from '@docusaurus/plugin-client-redirects';
import type * as ThemeSearchLocal from '@easyops-cn/docusaurus-search-local';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const localEditUrl = ({docPath}: {docPath: string}) =>
  `file:///${path.resolve(process.cwd(), 'docs', docPath).replace(/\\/g, '/')}`;

const config: Config = {
  title: 'Справка МИС «Инфоклиника» — стенд ЕГИСЗ',
  tagline: 'Локальный стенд подготовки документации раздела «Интеграция с ЕГИСЗ»',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'http://192.168.26.202:3006',
  baseUrl: '/',

  organizationName: 'sds',
  projectName: 'egisz-docs-stand',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',
  onBrokenAnchors: 'throw',

  i18n: {
    defaultLocale: 'ru',
    locales: ['ru'],
  },

  markdown: {
    mermaid: true,
    format: 'detect',
  },

  themes: [
    '@docusaurus/theme-mermaid',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['ru'],
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
          editUrl: localEditUrl,
          showLastUpdateTime: true,
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
        editUrl: ({docPath}: {docPath: string}) =>
          `file:///${path.resolve(process.cwd(), 'internal', docPath).replace(/\\/g, '/')}`,
        showLastUpdateTime: true,
      } satisfies Partial<PluginContentDocs.Options>,
    ],
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [],
      } satisfies PluginClientRedirects.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Инфоклиника — Справка (стенд)',
      logo: {
        alt: 'Инфоклиника',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'egiszSidebar',
          position: 'left',
          label: 'ЕГИСЗ',
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
