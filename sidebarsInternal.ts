import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/** Ручная конфигурация внутреннего дерева (репетиция public/internal разделения). */
const sidebarsInternal: SidebarsConfig = {
  internalSidebar: [
    'egisz/index',
    'egisz/support-process',
    'egisz/escalation-checklist',
    'egisz/precheck',
    'egisz/deep-diagnostics',
    'egisz/database',
    'egisz/corporate-resources',
    'egisz/escalation-to-development',
    'egisz/knowledge-loop',
  ],
};

export default sidebarsInternal;
