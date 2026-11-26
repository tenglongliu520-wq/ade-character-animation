# 阿德 · 自然手掌

## 得体说网页版首页

首页复用 `ade-rowing-minute.glb` 的 2026-11-26 转身修复版（84aedc8039f02a96fde01307fffc2240cdd10446），取中性姿势，点击时才播放招呼或小动作。透明底图 `homepage/ade-poster.webp` 来自同一个模型。浏览器同时保留暂停、减少动态和对话状态驱动的表情。

接入时，把 `homepage/home-avatar.js` 和 `homepage/ade-poster.webp` 放入站点的 `public/ade-home-3d/`，将 `ade-rowing-minute.glb` 复制为该目录下的 `ade-84aedc8.glb`，同时复制现有的 `vendor/`。页面在加载首页脚本前，通过 import map 将 `three` 映射到 `/ade-home-3d/vendor/three.module.js`。`homepage/mascot-motion.js` 接管 `#welcomeView .welcome-character` 并保留 `adeAvatar` 接口。首页图片地址使用 `/ade-home-3d/ade-poster.webp`。

## 双桨舞

`dance.html` 播放 32 个编排拍点组成的 `RowingDance`，包含双手抬起、左右侧步、张臂、交叉和鞠躬。`ade-rowing.glb` 是可单独使用的舞蹈模型，取自已校正左右五官的阿德，来源提交 1af31d0a927e31030305659e13eb29d7195274e1。以 96 BPM 播放时长 20 秒。浏览器用音频时钟推进动作，并支持载入本地音轨和设置速度。公开预览附 `rowing_music.py` 生成的原创节拍。

双臂从袖内延伸到手掌，前臂、手腕和手掌为连续网格。手臂、袖子和袖口共用肩部动作及屈肘形变，宽袖抬起时可见前臂。`rowing-dance-review.jpg` 展示六个姿势。补齐手臂前的版本见 d3c72048109f900274977165871a2961af2bb226。

本地打开 `http://127.0.0.1:4205/dance.html`。运行 `python rowing_dance.py` 可从本地 `ade.blend` 重新导出双桨舞。

### 北海公园远景版

`render_beihai_dance.py` 将双桨舞合成到北京北海公园的湖畔。阿德约占画面高度六成，石岸、湖面和白塔留在画面里。镜头缓慢横移，水波带动倒影和微光，脚下的接触阴影随动作变化。`beihai-lake.png` 是使用内置 ImageGen 生成的背景，舞蹈来源为提交 e1bd274cf2cdfcc1dfa9bca0fa27b8b0c0b7387e。

在装好 `requirements.txt` 后，运行 `python build_refined.py` 和 `python rowing_dance.py --no-review` 生成所需的 `ade-rowing.blend`。再运行 `python render_beihai_dance.py` 导出使用原创节拍的 MP4。可用 `--audio` 和 `--tempo` 指定本地音轨和编排节拍。

<details>
<summary>ImageGen 背景提示词</summary>

Create a high-quality background plate for compositing an existing full-height, centered 3D chibi Chinese character dancing. Do not depict the character or any people, text or graphics. Portrait with framing approximately 5:6. Beijing Beihai Park, recognizable view from the western lakeside in late spring, soft warm morning light matching a gentle polished animated film, realistic landscape with soft natural color, graceful willows and red-walled shoreline temples on Qionghua Island. The authentic Beihai White Dagoba (white inverted-bowl Tibetan stupa with a finial, not a tiered pagoda) rises above the trees in the upper-right, with its spire near 77–82% of the frame width and 20% of the height so it can be seen clear of the central figure; include a little pastel sky above. Distant treeline ends at approximately 43–47% of the frame height. Include the stupa's glimmering reflection and lightly textured horizontal ripples in soft blue-green water, which fills the broad middle and lower frame. The last 13–16% at the bottom is a flat, clean gray-beige stone lakeside terrace on which the character can stand, separated from the lake by a clean unbroken edge, no railing or steps. Reserve the central portion as quiet negative space for the figure; avoid paths or bright focal points there. No modern skyline, no crowds, no graphic overlay, no writing, no letterbox. Single coherent scene from water's edge, natural depth and softly detailed background, locally bright but no hard shadows.

</details>

### 北海一分钟街舞版

`ade-rowing-minute.glb` 含 64 个编排拍点。前半段借鉴录屏 `1a6acea2…` 的双手抬起、`cbda065f…` 的侧移抬袖，以及 `e78beafb…` 的开臂回收。后半段用街舞两步律动接划桨，侧步最大横移从 0.185 增至 0.222 模型单位，之后交替踩步转 360 度，接脚跟脚尖点步和鞠躬。转圈时支撑脚保持落点，头部先看回前方，衣摆和发带跟随旋转。人物和北海布景来源为 4ca95abecd87bfd36d0a80e8c055811d0aeb674c。

约第 40 秒的转身使用脚踝处的旋转中心和更短的交替踩步。转身时裤腿上端随腰胯，裤脚随鞋，二者之间的布料沿腿长渐变，裤腿上缘收进衣摆。修复前版本见 fa071d1fa218569efa30dc93c3b87cc44db4b63f。

运行 `python rowing_minute.py` 生成长舞段，从 `ade.blend` 读取角色。使用 16 位 PCM WAV 作为输入，运行 `python render_beihai_dance.py --minute --audio 原始音轨.wav --audio-start 7.68` 生成一分钟版。默认以 67.5 BPM 编排，对应配乐约 135 BPM。成片从北海湖面开场，约 1.3 秒起舞，约 58.2 秒回到湖面。公开仓库包含舞蹈模型、渲染代码和分镜预览，视频用的配乐由本地输入。

`python add_beihai_lake_motion.py 原版一分钟视频.mp4` 会在 480 × 576 的一分钟成片上加入动云和小木船。船上的孩子交替伸手、拉桨和回桨，入水时有小水圈，船尾留下水纹。天空蒙版限制云层在白塔和柳枝周围的移动范围。输出沿用输入视频的舞蹈时序和配乐。

`python add_detishuo_opening.py 北海一分钟成片.mp4` 将得体说片头放在首帧，约在 1.2 至 1.7 秒淡出，同时导出一张同名 PNG 封面。标志取自得体说小程序首页的 `brand.webp`，片头使用 Windows 楷体和微软雅黑。转身修复版来源为 84aedc8039f02a96fde01307fffc2240cdd10446。

流畅版参考 `cbda065…` 的单袖上扬与重心摆动，以及 `e78beafb…` 的开臂和回收。逐帧采样衔接曲线，身体重心先起，肩和肘错时跟进，抬脚和落脚用弧线。衣摆、腰带和发带随后回落。动作保留 32 个编排拍点和同一音频时钟。原舞蹈版本见 b15f4d4e5c5e85d4c80df61baa91c52210e86b5d。

大动作版从 `1a6acea2…`、`cbda065…` 和 `e78beafb…` 三段录屏取动作，再按配乐编排双袖上提、左右跨步与单袖抬手、双臂展开、胸前交叉回收和鞠躬。最大横向步幅 0.185 模型单位，肩部展开峰值 72°。双袖上提在第 2 拍，左右跨步压重心在第 6、10、18、22 拍，展开回收主要在第 14、19–20、23–24 和 28–29 拍。每个编排拍点对应参考配乐的两拍。上一版见 d0d599f5876350c4c8d87fe110d35df9d47ed11e。

检查头部中线两侧的耳朵、眼睛和眉毛。耳廓已是镜像网格。两眼共用同一眼型和虹膜颜色，眼高取原来两眼之间的中间值。眉形从同一网格镜像，抬眉和眨眼幅度一致。`face-symmetry-comparison.jpg` 展示同镜头的正面对照。修改前的版本见 4bea15f39f44f49f2ae4c121dadafcf93ed5880f。

根据用户提供的耳朵近景重建耳廓。手工描出的不对称外轮廓从耳上缘延伸到贴近脸颊的耳垂。耳轮、耳窝和靠脸侧的小软骨褶均雕在同一网格上。`ear-shape-comparison.jpg` 展示参考图和同镜头的修改前后效果。修改前的版本见 8e48f0c9797f4ebd129472f00fd7121240205f95。

根据用户提供的下巴和领口近景重塑脖子。下巴下方收窄并略向后，脖根逐渐展宽，内领抬高后贴合交领曲面。脖子和衣领一起随身体移动，头部偏转时仍在颈根处相接。`neck-collar-comparison.jpg` 展示同镜头的正面、斜侧和偏头效果。修改前的版本见 6ffbac3e9463447ee7b874a406d0c705b537d0cd。

以用户最新的 401 × 225 脸部截图描出正面下颌轮廓。用瞳距对应的比例换算眼下各截面的宽度，削减两颊外凸，保留圆下巴。面部五官沿新曲面重新贴合，腮红也随脸颊收窄。`face-trace-comparison.jpg` 展示截图参考和同镜头前后渲染。修改前的版本见 dbe112c9f43acdfea1b0aba9c9f9f0c07c6b8a53。

根据录屏脸部近景再修眉形和耳廓。两侧眉弧单独拟合，缩短眉尾并微调眉眼间距。耳廓略向外转，塑出柔和的外缘和内凹耳窝，耳垂收向脸颊。`brow-ear-comparison.jpg` 展示录屏参考及本轮修改前后的正面和斜侧。修改前的版本见 e18ce8704c171abdec7f46b3e2abaf5cf296604a。

依据用户提供的红心参考，将单枚珊瑚红胸针放在阿德左胸外袍衣襟，正面观看时位于画面右侧。胸针沿衣料表面塑形，与衣袍一起运动。`heart-placement.jpg` 展示全身比例、左胸正面及斜侧。调整前的版本见 17295e49b21b4d15d8ede24f597cdcb918f5f907。

根据录屏的正面与斜侧帧重做发缝、刘海和鬓角。收起额前裁切过的旧边，沿录屏发束走向铺出圆弧和渐细的发梢。点头动作中，五束主要发梢随头部动作分段跟随并回到静止姿势。`hair-flow-comparison.jpg` 展示同视角的正面、斜侧和动作对比。修改前的版本见 17364791437e370cdf4a2de23b090783edf8a5d1。

沿用 2026-11-25 的脸部参考图重塑耳朵。耳廓略收小并上移，下缘向脸颊收，耳窝和耳缘使用同一曲面及柔和的粉色渐变。耳朵随头部一同运动。`ear-comparison.jpg` 提供正面和斜侧对照，上一版见 6f601d44cdc0f59ea0ff25339c390b9fac147870。

根据用户 2026-11-25 提供的脸部参考截图，缩短下巴到嘴部之间的距离，圆化下颌，并在外眼角下方增加苹果肌体积。眉弧降低，眉身加厚，眉尾渐细，桃粉色腮红落在苹果肌上。`face-proportion-comparison.jpg` 以相同镜头对比修改前后的正面及斜侧。修改前的版本见 8774fd21e96d447fb5a2cd4329a91d049d050892。单独更新腮红贴图可运行 `python prepare_textures.py --skin-only`。

双手按阿德本人的视角标注左右。正面看，画面左侧是阿德的右手，画面右侧是左手。两边掌心都略朝前，拇指各自在外侧，四指朝身体一侧依次排列。`python review_hands.py` 检查十个指尖、两边虎口和拇指朝向，并生成正面及掌面近景 `hand-order.jpg`。双手统一朝向前的版本见 81dac89a177b6ba36c1a42e22f550d9230aa395c。

每只手使用单一连续网格。手腕自然收细，四指错落并轻弯。手部重建前的版本见 8ff6d77b975628e9a45eb3d374d3a0fb05d8a241。

嘴角使用两端渐细的浅玫瑰色曲面。嘴内开合和嘴角共享轮廓，并和脸颊的表情关键帧配合。青雾灰竹纹造型来自提交 43de157e5888e33cbbe844f7c6076063e759c6c2。

将内搭、领口、袖口内侧与裤脚由冷浅灰换成青雾灰（sRGB #CFDCD8），并在胸前和下摆做浅浮雕竹纹，作为单独试色版。前后截图用同一场景、灯光和镜头。上一版见 cafa0da6d3c7809a1288661256a1f813c3d48ede。

对照用户提供的脸部参考，将肤色基底调亮为暖白，腮红向浅粉收。脸、耳缘、脖子和眼皮沿用同一套肤色，保留面部体积。灯光、造型和表情动作沿自上一版 e21c22bce4a38117f59b1d17e33bf24385f57ca6。约 3.6 秒的短动作中，阿德先移动视线，两边眉毛同步抬起。上下眼皮覆盖眼部曲面完成眨眼。微笑时嘴角上扬，脸颊抬起，下眼皮收一点，最后回到起始姿态。视线通过眼部曲面局部变形实现，继续沿用录屏眼部颜色，近看仍可辨出少量纹理伸缩和眼皮接缝。动作覆盖脸部、头、身体和发带的试演段落。完整骨骼和口型另有待制作。

运行 python preview.py 并打开 http://127.0.0.1:4205/ 。可播放，拖动进度条或看笑容定格。可编辑的 ade.blend 在本地制作目录。

Python 3.11 与 bpy 4.5.3 的重建顺序是 recording_details.py、prepare_textures.py、fit_details.py、build_refined.py。facial_expression.py 和 expression_motion.py 分别定义表情形变及关键帧。verify_candidate.py 检查站姿与动作轨道，npm run validate:gltf 检查格式。参考录屏的时间和裁剪见 [来源记录](../../assets/reconstruction-reference-20261119/provenance.json)。

