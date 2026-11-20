# 阿德录屏校形 · 刘海与衣纹

以录屏原帧及两张斜侧参考比对。按原帧位置增加有厚度的中央刘海和两侧上翘发束，收整后颈发束。将帽饰改为一个带收口的布团曲面。前襟、袖褶、内翻袖口与不等长腰带按录像重新调整。

正面衣纹来自原帧四片可见衣料。先排除皮肤、背景和腰带，再提取局部明暗变化以降低录屏光照对纹理的影响。将纹理颜色混入衣服网格顶点，在侧背面逐渐过渡到此前制作的竹纹。保留上一轮的独立曲面眼睛。背面遮挡区域仍根据可见角度推断，细发丝和布料褶皱仍有差异。

运行 `python preview.py` 后访问 http://127.0.0.1:4197/ 。预览可旋转，并可并排查看正面和左右斜侧。三版对照、五视图及轮廓叠加来自本轮实际渲染。当前版本用于静态外观比较。

## 源文件

在 Python 3.11、bpy 4.5.3 环境中依次运行 `recording_details.py`、`prepare_textures.py`、`fit_details.py` 和 `build_refined.py`。运行 `make_comparison.py` 及 `render_outline.py` 生成对照。运行 `verify_candidate.py` 验证网格属性。安装 package.json 中的 glTF Validator 后运行 `npm run validate:gltf`。本地可编辑场景为 `ade.blend`。

上轮模型参照提交 36dfc4410beb31c03be68fe5c9a95bef2a60b920。原始头发几何沿用 Hunyuan3D-2 结果。录屏文件、时间与裁剪来源见 [参考帧记录](../../assets/reconstruction-reference-20261119/provenance.json)。
