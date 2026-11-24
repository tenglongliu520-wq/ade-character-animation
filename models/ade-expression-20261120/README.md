# 阿德 · 脸部神态与短动作

参照录屏斜侧画面修整眼下到脸颊的起伏，收窄下巴，放柔眉毛和嘴角。中央刘海和鬓角的补束更贴近原发团，预览和 Blender 暖主光与轮廓光都经过调整。上一版见人物动画仓库提交 1d7a3e7422aa39406576a2ec0cd97db712ecf448。

GLB 包含约 3.6 秒的「看过来、轻偏头、回正」，头、上身和发带错开运动，双眼眨动，嘴角与脸颊联动。眨眼用贴合脸面的眼部曲面变形，躯干使用层级变换。录屏眼部颜色、推断的背面和衣服细节沿用上一版，完整肢体骨骼与录屏中的完整动作仍待制作。

运行 python preview.py 并访问 http://127.0.0.1:4198/ 。对应按钮可播放动作、停在偏头时刻和拖动进度。Blender 工程 ade.blend 位于本地制作目录。

用 Python 3.11、bpy 4.5.3 依次运行 recording_details.py、prepare_textures.py、fit_details.py 和 build_refined.py。verify_candidate.py 检查默认站姿和动画轨道，npm run validate:gltf 检查 GLB 格式。make_comparison.py 和 render_outline.py 生成渲染对照。参考录屏的时间和裁剪见 [来源记录](../../assets/reconstruction-reference-20261119/provenance.json)。
