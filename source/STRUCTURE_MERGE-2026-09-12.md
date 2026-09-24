# Объединение разделов «Об интеграции»/«Подготовка» и «Тестирование»/«Диагностика»

Редакция от 12.09.2026. По задаче пользователя объединены два пункта навигации рабочей редакции `docs/egisz/`: «Об интеграции» с «Подготовкой» и «Тестирование» с «Диагностикой». Объединение — навигационное и по расположению файлов; разделение объяснения, инструкции и справочника внутри раздела сохранено согласно [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md).

## Перенесённые файлы

| Было | Стало |
|---|---|
| `docs/egisz/preparation/index.mdx` | Содержание объединено в `docs/egisz/overview/index.mdx` |
| `docs/egisz/preparation/organizational-requirements.mdx` | `docs/egisz/overview/organizational-requirements.mdx` |
| `docs/egisz/preparation/technical-requirements.mdx` | `docs/egisz/overview/technical-requirements.mdx` |
| `docs/egisz/preparation/frmo-frmr.mdx` | `docs/egisz/overview/frmo-frmr.mdx` |
| `docs/egisz/preparation/digital-signature.mdx` | `docs/egisz/overview/digital-signature.mdx` |
| `docs/egisz/troubleshooting/index.mdx` | Содержание объединено в `docs/egisz/testing/index.mdx` |
| `docs/egisz/troubleshooting/configuration-check.mdx` | `docs/egisz/testing/configuration-check.mdx` |
| `docs/egisz/troubleshooting/error-catalog.mdx` | `docs/egisz/testing/error-catalog.mdx` |
| `docs/egisz/troubleshooting/support-request.mdx` | `docs/egisz/testing/support-request.mdx` |

Категории `sidebars.ts` переименованы: «Об интеграции и подготовка» (ссылка на `egisz/overview/index`), «Тестирование и диагностика» (ссылка на `egisz/testing/index`). Старые маршруты `/trunk/egisz/preparation*` и `/trunk/egisz/troubleshooting*` перенаправляются на новые через `@docusaurus/plugin-client-redirects` в `docusaurus.config.ts`. Все внутренние ссылки (36 файлов в `docs/`, 3 файла в `internal/`, домашняя страница) проверены и обновлены на новые пути; список путей, которые не требовали изменения (историческая переписка в `source/EDITORIAL_REVIEW-2026-09-12.md` и `source/MANIFEST.md`), сохранён без правки как запись о прошлом состоянии.

## Дополнительно по замечанию рецензента (Diátaxis)

- `docs/sync_manager/automation.mdx` содержал таблицу параметров `sync.conf` внутри процедуры настройки службы. Таблица и объяснение правил расписания вынесены в новый справочник `docs/sync_manager/reference.mdx`; `automation.mdx` теперь даёт только порядок действий со ссылками на параметры. Обновлены перекрёстные ссылки в `docs/sync_manager/profiles.mdx` и `docs/sync_manager/check.mdx`, добавлен пункт `sync_manager/reference` в `sidebars.ts`.
- `docs/egisz/testing/error-catalog.mdx` дублировал номера кодов РЭМД из `docs/egisz/operation/statuses.mdx`. Единственный источник кодов — таблица статусов; каталог ошибок теперь ссылается на неё по названию состояния, без повторения номеров.
- `docs/egisz/overview/architecture.mdx` дополнен разделом «Защищённый канал и подпись документа» с явной границей: страница называет применяемые механизмы (OpenVPN ГОСТ, УКЭП) и ссылается на технические требования и подпись, но не приводит обоснование выбора контура шифрования — это вопрос договора и нормативных актов, а не настройки МИС. Обоснование не добавлено как непроверенное; замечание рецензента учтено явной пометкой границы, а не изобретённым текстом.

## Проверка

- `docker compose exec -T dev npm run typecheck` — успешно.
- `docker compose exec -T build npm run build` — две последовательные успешные сборки, строгая проверка ссылок и якорей (`onBrokenLinks: throw`) пройдена.
- В браузере на 3007 проверены `/trunk/egisz/overview/`, `/trunk/egisz/testing/`, `/trunk/sync_manager/reference` и редирект со старого `/trunk/egisz/troubleshooting/configuration-check`.

Испытание процедур на действующей МИС и передача документов в ЕГИСЗ этой правкой не выполнялись; изменения затрагивают только структуру и текст справки.
