# Переработка разделов служебных модулей

Дата чтения источников: 12.09.2026. Источник — действующая веб-справка МИС 26.1. Перенос выполняется в рабочую редакцию локального стенда, без изменения опубликованной справки и снимков 26.1/25.2.

## Карта содержания

| Исходный раздел | Локальная редакция | Способ переноса |
|---|---|---|
| [Система обновлений](https://help.infoclinica.ru/26.1/services1/cp-upgrader/) | `docs/services1/cp-upgrader/index.mdx` | Назначение, подготовка, резервирование и выбор режима |
| [Базовый режим](https://help.infoclinica.ru/26.1/services1/cp-upgrader/cp-db_upgrade_basic/) | `basic.mdx` в том же каталоге | Пошаговая процедура; последствия пропуска и повтора ошибок |
| [Pro](https://help.infoclinica.ru/26.1/services1/cp-upgrader/cp-db_upgrade-pro/) и [мастер](https://help.infoclinica.ru/26.1/services1/cp-upgrader/cp-db_upgrade-pro/cp-upgrade-pro-master/) | `pro.mdx` | Выбор режима и источника, монопольный доступ, ограничения обработки ошибок |
| [Журнал обновлений](https://help.infoclinica.ru/26.1/services1/cp-upgrader/cp-db_upgrade-pro/cp-upgrade_upd_jrn/) | `check.mdx` | Проверка каждой целевой БД, статусов и результата |
| [Пользовательский режим](https://help.infoclinica.ru/26.1/services1/cp-upgrader/cp-upgrade_user/) | `user.mdx` | Подготовка пакета и ревизии; развёртывание объектов требует сверки |
| [Система репликации](https://help.infoclinica.ru/26.1/services1/replic/), [ReplServer](https://help.infoclinica.ru/26.1/services1/replic/replserv/) | `docs/services1/replic/index.mdx` | Компоненты и последовательность работы |
| [Установка](https://help.infoclinica.ru/26.1/services1/replic/intro_replsetup/), [запуск](https://help.infoclinica.ru/26.1/services1/replic/replserv/replserv_run/), [настройки](https://help.infoclinica.ru/26.1/services1/replic/replserv/replserv_params/) | `setup.mdx` | Последовательность установки; явно отмечено отсутствие подробных параметров |
| [ReplConf](https://help.infoclinica.ru/26.1/services1/replic/replconf/), [задачи](https://help.infoclinica.ru/26.1/services1/replic/replconf/replconf_tasks/) | `configuration.mdx` | Сущности, проверка групп, задач и признака использования |
| [Консоль](https://help.infoclinica.ru/26.1/services1/replic/replconf/replconf_console/), [журналы](https://help.infoclinica.ru/26.1/services1/replic/replconf/replconf_reports/), [журнал репликации](https://help.infoclinica.ru/26.1/services1/replic/replconf/replconf_reports/replconf_reports_repl/) | `check.mdx` | Общая процедура контроля службы, задач и данных |
| [Менеджер Загрузок](https://help.infoclinica.ru/26.1/sync_manager/), [мастер](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_general/) | `docs/sync_manager/index.mdx` | Назначение и разделение загрузки/обработки |
| [Настройки](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_settings/), [справочники](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_handbooks/), [профили](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_profiles/) | `settings.mdx` | Основные поля и проверки; подробные параметры файловых форматов оставлены по ссылке |
| [Загрузка](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_general/sync_manager_master/), [обработка](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_general/sync_manager_reworking/) | `synchronization.mdx` | Две последовательные процедуры и проверка результата |
| [Командная строка](https://help.infoclinica.ru/26.1/sync_manager/sync_manager_handbooks/sync_manager_handbooks_adm/) | `automation.mdx`, `check.mdx` | REFCODE, журнал, PUID; диагностика автоматического выполнения |

Это переработанная эксплуатационная редакция, а не полная копия всех дочерних страниц и изображений. Сведения о метаданных репликации, всех типах задач и групп, специальных журналах, подробных справочниках Pro и всех параметрах XSLT/SAX остаются в исходной справке. Их перенос следует выполнять по потребностям подтверждённых сценариев; не объявлять эти справочники завершёнными локально.

## Редакционные изменения и ограничения

- Внутренняя страница `internal/egisz/replicator.mdx` содержала заглушку. Она удалена; `/internal/egisz/replicator` перенаправляется на `/trunk/services1/replic/check`.
- Общие проверки доступны администраторам МО в отдельном разделе. Внутренние процедуры поддержки ссылаются на них.
- Порядок фиксации результатов, диагностические развилки и критерии завершения добавлены методически и отмечены на страницах. Они не выдаются за результаты испытания реальной системы.
- Страница настроек ReplServer в источнике содержит только указание на параметры командной строки и многоточие. Полные параметры не восстановлены по догадке.
- Командная строка SyncManager и служба SyncServer описаны отдельно. Последующее [дополнение по локальной поставке](SYNC_MANAGER-2026-09-12.md) подтверждает имя службы, параметры конфигурации, связь с `infodent.ini`, расписание и журнал инициализации; завершённый цикл НСИ ещё требует испытания.
- В описании пользовательских обновлений встречаются `Upgrade.exe` и `Upgrader.exe`; противоречие отмечено до проверки комплекта.
- Старые примеры перехода между версиями 13.1/14.1 не перенесены как действующие маршруты. Необходима матрица совместимости текущей поставки.
- Отсутствие ошибок в журнале не объявлено доказательством всей интеграции; необходимы проверка данных и тестовая передача.

## Дальнейшая работа

Состав необходимых источников, доступов и итоговых документов приведён в [плане](WORK_PLAN-2026-09-12.md). Notion сохраняет приоритет по задачам ЕГИСЗ; текущая справка используется для поведения общих модулей и названий интерфейса.

## Проверка локального стенда

- TypeScript: `docker compose exec -T dev npm run typecheck` — код 0.
- Две последовательные статические сборки: `docker compose exec -T build sh -c 'npm run build && npm run build'` — код 0, ссылки и якоря проверены в строгом режиме.
- На 3007 в браузере проверены общий раздел, переход к проверке репликатора и перенаправление с прежней внутренней страницы.
- При массовом добавлении страниц сервер разработки на 3006 сохранил ошибки разрешения новых Markdown-ссылок. Выполнен `docker compose restart dev`; после запуска журнал содержит `Compiled successfully` и `compiled successfully` без ошибок новой компиляции.
- После перезапуска в браузере на 3006 проверены страница ЕГИСЗ без перекрытия ошибками, переход из проверки готовности к синхронизации и переход из диагностики к репликатору.
- `git diff --check` — код 0. Docker-контейнеры оставлены работающими.

Процедуры установки служб, обновления МИС, загрузки НСИ и передачи документов в тестовом контуре не выполнялись.
