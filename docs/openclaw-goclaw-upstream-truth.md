# OpenClaw / GoClaw upstream attach truth

## ДОКАЗАНО РАБОТАЕТ
- В repo `hermes-max-adapter` есть local attach-ready слой для `openclaw.py` и `goclaw.py`, покрытый локальными тестами.
- Для OpenClaw найден официальный plugin SDK и docs по channel plugins:
  - `defineChannelPluginEntry`
  - `api.registerChannel(...)`
  - `api.runtime`
  - channel inbound/outbound SDK surfaces
- Для GoClaw найден живой upstream проект и docs, что custom channels существуют, но пока без локального checkout рантайма.

## НЕ РАБОТАЕТ / НЕ ПРОВЕРЕНО
- Реальная загрузка нашего MAX adapter как OpenClaw plugin внутри локально доступного upstream OpenClaw runtime не проверена: локального checkout `openclaw/openclaw` в `~/workspaces` сейчас нет.
- Реальная загрузка нашего MAX adapter как GoClaw channel внутри локально доступного upstream GoClaw runtime не проверена: локального checkout `goclaw` в `~/workspaces` сейчас нет.
- Client-visible E2E через OpenClaw runtime не проверено.
- Client-visible E2E через GoClaw runtime не проверено.

## Текущий блокер
- На этой машине в `~/workspaces` сейчас нет локальных upstream repos/runtimes OpenClaw и GoClaw, куда можно физически вмонтировать адаптер и прогнать настоящий attach.
- Встроенный `web_search` не настроен, поэтому внешний ресёрч шёл через Exa/GitHub; этого хватило для contract discovery, но не для локальной runtime-приёмки.

## Что нужно для следующего шага
1. Локальный checkout OpenClaw runtime repo.
2. Локальный checkout GoClaw runtime repo.
3. Понять их package/build layout на месте.
4. Вмонтировать `hermes-max-adapter` как plugin/channel extension.
5. Прогнать реальную attach + startup + inbound/outbound smoke.
