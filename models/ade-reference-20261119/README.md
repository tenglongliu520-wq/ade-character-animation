# 阿德三维参照模型 · 2026-11-19

本目录包含依据用户提供的阿德动作录屏重新建模的三维候选版本。它具有真实网格、嵌入材质、骨骼、动画和面部形变，可以旋转查看；没有把原始录屏或平面贴图作为角色模型播放。

这不是从视频恢复出的原始 Meshy 工程。录屏未提供完整背面和身体内部，这些部分为补充设计。发型、五官和布纹需要与录屏对照，不能把文件格式通过当作形象已经审定。

## 文件

- `ade.glb`：可独立加载的二进制 glTF；贴图已嵌入。
- `build_ade.py`：可复现的 Blender Python 建模、绑定、动画和导出源码。
- `bamboo-cloth.png`：本轮程序绘制的竹纹布料。
- `front.png`、`three-quarter.png`、`side.png`、`back.png`、`wave.png`：实际 Blender 渲染。
- `avatar-3d.js`、`index.html`、`vendor/`、`preview.py`：独立本地预览。
- `verify_glb.py`、`model-check.json`：实际 GLB 的结构与内容检查。
- `validate_gltf.cjs`、`gltf-validation.json`：Khronos 官方 glTF Validator 的完整校验，不截断问题。

本地另保存有可编辑 `ade.blend`。仓库现有忽略规则排除 `.blend`，因此不强行加入版本库；建模源码和最终 GLB 正常同步。

## 本地预览

使用 Python 3.9+，在本目录运行：

```text
python preview.py --port 4193
```

然后打开 http://127.0.0.1:4193/ 。Windows 本机可双击 `启动预览.cmd`。仅监听本机，不开放局域网；预览不需要安装 Node、Blender，也不访问在线模型服务。浏览器需要支持 WebGL 2。直接双击 HTML 会受浏览器模块加载限制，请通过本地服务器查看。

拖动旋转、滚轮缩放，或使用正面/斜侧面/侧面/背面按钮。支持待机、招呼、轻微歪头思考、暂停及张嘴检查。张嘴检查是形变演示，不是语音合成或音素口型。系统减少动态时不自动运行动作。

## 重新构建与验证

建模需要 **CPython 3.11**；建议使用单独虚拟环境：

```text
python -m pip install -r requirements.txt
python build_ade.py --render
python render_checks.py
python verify_glb.py
npm install --ignore-scripts --no-audit --no-fund
npm run validate:gltf
```

预览用的 Three.js 0.187.0 已打包到 `vendor/`，版本和来源见 `vendor/VERSION`，其 MIT 许可证保留于 `vendor/LICENSE`。GLB 只导出角色，不包含摄影棚灯光或地板。

## 来源、范围与限制

身份参考为用户提供的四段 MP4：`1a6acea2b9c36af025bd6a591eebd389.mp4`、`64258107a84437fbf7bd966dcf19be0a.mp4`、`cbda065fffc6fa7e5630c96733cff944.mp4`、`e78beafb926601e87bcd04d7a632e5ea.mp4`。已提取参考图及原视频散列位于仓库 `assets/reconstruction-reference-20261119/`。

- 手工编写几何与动作，未使用视频动作捕捉或原始 Meshy 骨骼数据。
- 保留棕发、大眼、浅青绿竹纹古装、米白内搭、深绿腰带、红心、黑白鞋与浅绿头饰。
- 当前采用按部件骨骼权重，适合已制作的克制动作；没有布料模拟，也不意味着可以任意套用剧烈舞蹈而无穿模。
- 脸部有 `blink` 与 `jawOpen` 控制。`setSpeechLevel(0–1)` 接收音量，260ms 无更新归零，不提供逐字音素对齐。
- 独立类 `Ade3DAvatar` 提供 `ready`、`setState`、`setSpeechLevel`、`setPaused` 和 `destroy`，但本轮没有替换现有主站 `CompanionAvatar`，没有修改语音库或发布正式首页。
- 结构校验和桌面浏览器预览不等同于真实微信手机性能或全帧服装质量验收。验收范围见 `qa-notes.md`。

本轮使用本地 Blender，不依赖尚未恢复授权的 fal，未提交付费生成任务。素材公开可见不代表给原始阿德 IP 添加新的开放授权。
