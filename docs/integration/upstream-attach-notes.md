# Upstream attach notes

## OpenClaw
По свежим официальным докам OpenClaw канал надо делать не как произвольный Python runtime wrapper, а как **реальный plugin package** через их JS/TS Plugin SDK:
- `defineChannelPluginEntry`
- `api.registerChannel(...)`
- `api.runtime`
- `channel-inbound` / `channel-outbound`

Это значит, что наш текущий `src/hermes_max_adapter/openclaw.py` полезен как local contract model, но **не является нативным upstream OpenClaw plugin package**. Для настоящего attach понадобится отдельный OpenClaw-side package/bridge на их SDK, который будет вызывать наш proven MAX core или повторять его контракт.

## GoClaw
По найденным материалам GoClaw поддерживает custom channels, но на этой машине нет локального upstream checkout, чтобы проверить реальные extension points в коде. Внешние docs указывают на каналы как runtime layer, а GitHub docs прямо говорят смотреть примеры `internal/telegram/` и `internal/http/`.

Это значит, что текущий `src/hermes_max_adapter/goclaw.py` — local runtime-shaped contract, но не доказанный native GoClaw attach.

## Вывод
Сейчас можно честно сказать только это:
- OpenClaw/GoClaw local adapter contracts готовы.
- Для реального upstream attach нужен следующий этап: взять сами runtime repos и сделать отдельную интеграцию по их нативным extension contracts.


## Fresh local repo findings (2026-06-06)

### OpenClaw
- Local upstream repo now available at `~/workspaces/openclaw`.
- Real bundled channel plugins are TypeScript packages under `extensions/<plugin>/`.
- Typical shape is:
  - `package.json` with `openclaw.extensions`
  - `index.ts` using `defineBundledChannelEntry(...)`
  - `channel-plugin-api.ts` exporting `<plugin>Plugin`
  - `api.ts` exporting runtime setter/getter
  - `src/channel.ts` building a `ChannelPlugin` via `createChatChannelPlugin(...)`
- Therefore our current Python `openclaw.py` cannot be attached natively as-is. A true OpenClaw attach requires a new TS plugin package that either bridges to our MAX core or reimplements the proven MAX contract on their SDK.

### GoClaw
- Local upstream repo now available at `~/workspaces/goclaw`.
- Real channels are native Go implementations wired directly in `internal/channels/*` and started from `internal/channels/manager.go`.
- Runtime contracts split into:
  - `internal/channels/types.ManagedChannel` for lifecycle (`Name/Start/Stop/Reload/Status`)
  - `internal/gateway.Channel` for delivery behavior (`DeliverAssistantMessage`, `DeliverSystemMessage`, etc.)
- Manager startup is currently hardwired to built-in channels (telegram/whatsapp/http/tui/voice), not plugin discovery.
- Therefore our current Python `goclaw.py` cannot be attached natively as-is. A true GoClaw attach requires a native Go channel implementation plus manager/config wiring.

## Updated conclusion
We now have stronger proof that both current wrappers are useful design/contract artifacts, but neither is drop-in attachable to the real upstream runtimes without building runtime-native integration layers.
