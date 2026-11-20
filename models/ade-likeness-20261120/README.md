# 阿德形象修订候选 · 2026-11-20

用户明确反馈 11月19日版本与录屏“差别很大”。本目录保存继续修订的真实三维候选，**尚未通过用户形象验收，不能替换正式首页**。旧版内部检查不代表用户认可。

本轮重点是头脸相似度：使用腾讯官方公开 Hunyuan3D-2 的 shape-only 结果保留层叠头发体积，重建平滑脸部，以录屏原帧的眼眉、嘴和腮红做羽化投射贴图，接回此前自建的干净古装、腰带、红心和手脚。未把录屏当成三维模型，也没有恢复原 Meshy 网格。

## 文件

- `ade.glb`：本轮静态三维候选，可旋转；`front.png`、`quarter.png`、`back.png` 是该模型真实渲染。
- `comparison.jpg`：目标录屏、上一版和本轮的统一人物高度对照。
- `source-geometry.glb`：公开模型服务输出的原始体积几何；`authored-body.glb`：此前自建角色输入，取干净衣身并移除旧头部。
- `build_candidate.py`、`prepare_color.py`：本轮可重复组装与纹理准备源码，输入网格保持原样。
- `ade.blend`：可编辑场景在本地制作目录保存，按现有忽略规则不提交。公共仓库通过脚本和输入网格重建。
- `candidate-check.json`、`gltf-validation.json`：结构与格式检查；不证明相似度。
- `vendor/`：本地 Three.js 及其 MIT 许可，版本见 VERSION。

## 当前限制

五官目前主要来自录屏贴图，眼皮、眼球、嘴部尚无独立三维结构或控制。**本候选未绑定骨骼、没有动画**；上一版的动作不应被算作本版已完成。发际线、帽饰与发带材质接缝、后脑发束、衣服垂感/竹纹密度、鞋底厚度仍需修订。后脑和遮挡区域含推断，不能声称已精确恢复。

曾尝试另一 shape-only 结果，实际厚高比约0.0097，已判为薄片并排除。完整公开演示因单任务免费 GPU 时长限制而未执行；没有购买、订阅或重新请求 fal 授权。本目录当前候选有真实体积，具体世界坐标尺寸与厚高比见 candidate-check.json。

## 预览与重建

在本目录运行 `python preview.py`，打开 http://127.0.0.1:4194/。页面只展示录屏对照和角度控制；没有虚假的动作按钮。

重建环境：Python3.11、Blender bpy4.5.3、Pillow13、NumPy1.26.4；依次运行 `python prepare_color.py`、`python build_candidate.py`、`python verify_candidate.py`。`python make_comparison.py` 更新对照图。源码会重写本目录生成物，不修改输入网格。

官方 glTF 格式检查：安装 package.json 指定的 gltf-validator 后运行 `npm run validate:gltf`。详细结果与观察范围见 qa.md。没有变更语音接口或正式首页。
