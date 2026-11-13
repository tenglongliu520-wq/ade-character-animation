# 古装阿德分层动画接入

版本：2026-11-13；来源为得体说主站本地提交 f77091f 及已获用户确认的古装阿德设计。

本轮迁入 src/web 的 Canvas 动画模型、分层渲染器、首页挂载及 iframe 联动接入，以及 assets/hanfu-20261112 的内置 imagegen 生成透明分层素材。

运行依赖：网页先加载 ade-motion-model.js，再加载 companion-avatar.js。素材 ade-puppet-atlas-20261112.png 需放到渲染脚本所在的相同可访问目录；当前仓库已补充 tools/preview.py 和 examples/ 独立演示。首页挂载还依赖主站既有DOM与样式。

动作包含交替腿脚小跑入场、独立手臂挥手、头身呼吸、眨眼及随实际音频能量变化的嘴型；支持暂停、减少动态和后台停止。setState(mode)、setPaused(value)、analyser、setSpeechLevel(level) 为接入接口。

iframe 使用 source 与 origin 双重检查及 ade-avatar-connect 握手，ade-avatar-motion 仅携带 mode、level、paused，不包含音频或对话文本。声音模型、问答模型、密钥和录音不属于本库。

与语音仓库同步后，云端聊天入口使用同一角色渲染器；配音选择为用户指定 I/M09。未配音的新文本不切换其他声音。

验证在主站执行：node --test tests/ade-coordinated.cjs tests/mascot-motion.cjs。仓库可独立运行 node --test tests/ade-coordinated.cjs；主站挂载集成仍应在主站验证。
