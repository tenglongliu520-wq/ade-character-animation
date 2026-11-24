# 阿德 · 眼神和笑意

参照用户录屏与上一版提交 289fe84c19cc1c5c06086946b7048ccad2fc000b。约 3.6 秒的短动作中，阿德先移动视线，两边眉毛不同幅度地抬起。上下眼皮覆盖眼部曲面完成眨眼。微笑时嘴角上扬，脸颊抬起，下眼皮收一点，最后回到起始姿态。视线通过眼部曲面局部变形实现，继续沿用录屏眼部颜色，近看仍可辨出少量纹理伸缩和眼皮接缝。动作覆盖脸部、头、身体和发带的试演段落。完整骨骼和口型另有待制作。

运行 python preview.py 并打开 http://127.0.0.1:4199/ 。可播放，拖动进度条或看笑容定格。可编辑的 ade.blend 在本地制作目录。

Python 3.11 与 bpy 4.5.3 的重建顺序是 recording_details.py、prepare_textures.py、fit_details.py、build_refined.py。facial_expression.py 和 expression_motion.py 分别定义表情形变及关键帧。verify_candidate.py 检查站姿与动作轨道，npm run validate:gltf 检查格式。参考录屏的时间和裁剪见 [来源记录](../../assets/reconstruction-reference-20261119/provenance.json)。
