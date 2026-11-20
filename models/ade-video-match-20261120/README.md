# 阿德 · 视频形象校形

以用户提供的四段录屏为目标。已检查四段录屏的采样帧，采用同一正面帧和左右斜侧原帧校对。录屏里的动作与角度有限。后三维轮廓、遮挡处与衣服内侧为重建时的推断。

本轮沿用有厚度的层叠发束几何，在侧面平滑混合录屏栗棕色与背部推断色。重新校正两个眼部曲面的边界与深度，眼形、眼线、虹膜及高光采用原帧颜色。眉、鼻、微笑和耳朵保留独立网格。加宽外衣下摆、修小肩部、重做白色翻袖，并调整大竹叶、手的位置和双层青色发带。色彩校正和外观检查用 Blender 完成。

运行 `python preview.py` 后访问 http://127.0.0.1:4196/ 。可以用正面、左右斜侧按钮切换录屏帧和模型角度。另有正面三版对照、多角度渲染和轮廓叠加。当前 GLB 为静态外观版本。动作、眨眼和口型仍待绑定。衣服褶皱、内耳、后脑发束和帽饰遮挡处仍存在差异。

## 重建

在 Python 3.11、Blender bpy 4.5.3 环境中按顺序运行 `python recording_details.py`、`python prepare_textures.py`、`python build_refined.py`、`python make_comparison.py` 和 `python render_outline.py`。`python verify_candidate.py` 检查体积、嵌入贴图和独立五官网格。`npm run validate:gltf` 调用 Khronos glTF Validator。Windows 对照图使用系统微软雅黑。

可编辑 `ade.blend` 在本地制作目录保存。仓库保存可复现源码、输入和导出资产。上轮对照与头发输入沿用人物仓库的 bdf2e388e67e90749e9351754deb01a69e43536f 版本。录屏截取来源及帧时间参照 [参考帧的来源记录](../../assets/reconstruction-reference-20261119/provenance.json)。
