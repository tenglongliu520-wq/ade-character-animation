# 接入约定（初始草案）

接收语音库的 `listening`、`thinking`、`speech-start`、`speech-level`、`speech-end`、`speech-stop`、`speech-error` 事件。

- 使用 `utteranceId` 识别当前语音，忽略已停止语音的事件。
- `speech-level` 的 `level` 范围为 0–1，来源为实际音频能量；没有播放音频时嘴巴闭合。
- 动作状态切换需平滑，暂停时停止动画循环；恢复时避免启动多个循环。
- 支持系统减少动态设置，后台页面暂停绘制。
- 对外接入前检查手机尺寸显示、素材接缝、停止播放及切后台恢复。

以上为接口草案，尚未实现。
