# 阿德 · 暖白肤色

对照用户提供的脸部参考，将肤色基底调亮为暖白，腮红向浅粉收。脸、耳缘、脖子和眼皮沿用同一套肤色，保留面部体积。灯光、造型和表情动作沿自上一版 e21c22bce4a38117f59b1d17e33bf24385f57ca6。约 3.6 秒的短动作中，阿德先移动视线，两边眉毛不同幅度地抬起。上下眼皮覆盖眼部曲面完成眨眼。微笑时嘴角上扬，脸颊抬起，下眼皮收一点，最后回到起始姿态。视线通过眼部曲面局部变形实现，继续沿用录屏眼部颜色，近看仍可辨出少量纹理伸缩和眼皮接缝。动作覆盖脸部、头、身体和发带的试演段落。完整骨骼和口型另有待制作。

运行 python preview.py 并打开 http://127.0.0.1:4200/ 。可播放，拖动进度条或看笑容定格。可编辑的 ade.blend 在本地制作目录。

Python 3.11 与 bpy 4.5.3 的重建顺序是 recording_details.py、prepare_textures.py、fit_details.py、build_refined.py。facial_expression.py 和 expression_motion.py 分别定义表情形变及关键帧。verify_candidate.py 检查站姿与动作轨道，npm run validate:gltf 检查格式。参考录屏的时间和裁剪见 [来源记录](../../assets/reconstruction-reference-20261119/provenance.json)。

