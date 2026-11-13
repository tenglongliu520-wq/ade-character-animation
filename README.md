# 阿德人物动画库 · ade-character-animation

得体说阿德 IP 的古装分层素材、Canvas 动画运行代码及独立演示。

## 本地预览

需要 Python 3.9+，在本仓库目录运行 `python tools/preview.py`，打开 http://127.0.0.1:4191/ 。无需额外依赖。

可查看小跑入场、挥手、待机、倾听、思考和暂停；选择本地音频后点击播放，嘴型随实际音量变化。所选文件仅在浏览器内播放。系统减少动态设置下保持静态。

若同级有 `ade-voice` 仓库，可点击“I / M09”播放已选角色音频；单独下载本库也可用本地音频演示。预览仅监听本机，不开放外网。

## 目录

- `assets/hanfu-20261112/`：透明分层图集。
- `src/web/`：动画模型、Canvas 渲染及主站挂载代码。
- `animations/states.json`：实际接受的模式。
- `examples/`、`tools/preview.py`：独立预览和本机静态服务。
- `tests/ade-coordinated.cjs`：动作逻辑测试。
- `docs/hanfu-runtime-20261113.md`：主站素材与代码来源。
- `docs/integration.md`：语音联动接口与限制。

## 验证与边界

运行 `node --test tests/ade-coordinated.cjs tests/renderer.cjs`（Node.js 18+）以及 `python tools/verify_preview.py`。

嘴型由音量包络驱动，不是逐字音素对齐。部分可接受的模式共用通用姿态，不能据此宣称所有独立动作均已制作。自动测试不替代实际观看和听审。主站挂载脚本仍依赖主站DOM，独立演示只加载模型和渲染器。

配套语音库：https://github.com/tenglongliu520-wq/ade-voice 。仓库已按用户要求于2026-11-13改为公开，任何人可查看和下载。未添加开源许可证；公开可见不代表已授予任意使用或再分发许可，角色素材与第三方代码授权分别确认。

Windows 本机也可双击 `启动预览.cmd`，再打开上面的本机地址；关闭启动窗口即可停止预览。脚本优先使用本机现有的 D:/AI/Ade-companion-20261104/venv Python，其他电脑使用 PATH 中的 Python。
