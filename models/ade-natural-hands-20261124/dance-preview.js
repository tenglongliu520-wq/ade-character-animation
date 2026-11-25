import { Ade3DAvatar } from './avatar-3d.js';

const byId = (id) => document.getElementById(id);
const status = byId('status');
const audio = byId('sound');
const play = byId('play');
const timeline = byId('timeline');
const file = byId('song');
const tempo = byId('tempo');
const restore = byId('restore');
const clipName = 'RowingDance';
const defaultTempo = 96;
const params = new URLSearchParams(window.location.search);
const referenceTrack = params.get('track') === 'reference';
const source = referenceTrack ? './rowing-reference-local.wav' : './rowing-beat.wav';
const sourceLabel = referenceTrack ? '你提供的视频配乐' : '原创划桨节拍 · 96 BPM';
const sourceTempo = referenceTrack ? Math.min(180, Math.max(45, Number(params.get('tempo')) || defaultTempo)) : defaultTempo;

let audioUrl = null;
let frame = 0;

try {
  const avatar = new Ade3DAvatar(byId('stage'), {modelUrl: './ade-rowing.glb?v=forearms'});
  avatar.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
  avatar.setPaused(true);
  await avatar.ready;
  avatar.setView('leftQuarter');
  const action = avatar.actions.get(clipName);
  if (!action) throw new Error('Missing dance clip');
  const clip = action.getClip();
  const clipStart = Math.min(...clip.tracks.map(track => track.times[0]));
  const duration = clip.duration - clipStart;
  action.play();

  function displayPose() {
    const speed = (Number(tempo.value) || defaultTempo) / defaultTempo;
    const seconds = audio.currentTime * speed;
    action.time = clipStart + (audioUrl ? seconds % duration : Math.min(duration, seconds));
    avatar.mixer.update(0);
    avatar.schedule();
    timeline.value = String(audio.currentTime);
  }

  function advance() {
    frame = 0;
    displayPose();
    if (!audio.paused && !audio.ended) frame = requestAnimationFrame(advance);
  }

  function updateButton() {
    play.textContent = audio.paused ? '播放舞蹈' : '暂停';
    if (!audio.paused && !frame) frame = requestAnimationFrame(advance);
    if (audio.paused && frame) {
      cancelAnimationFrame(frame);
      frame = 0;
    }
    displayPose();
  }

  function changeSource(url, label, bpm = defaultTempo) {
    audio.pause();
    audio.src = url;
    audio.load();
    byId('sound-label').textContent = label;
    byId('tempo-setting').hidden = !audioUrl;
    restore.hidden = !audioUrl;
    tempo.value = String(bpm);
    status.textContent = '可播放 · 拖动阿德切换角度';
    displayPose();
  }

  play.addEventListener('click', async () => {
    if (!audio.paused) {
      audio.pause();
      return;
    }
    if (audio.ended) audio.currentTime = 0;
    try {
      await audio.play();
      status.textContent = '正在跳舞';
    } catch {
      status.textContent = '音频无法播放，请换一个音频文件。';
    }
  });
  for (const event of ['play', 'pause', 'ended']) audio.addEventListener(event, updateButton);
  audio.addEventListener('ended', () => { status.textContent = '舞蹈已结束'; });
  audio.addEventListener('loadedmetadata', () => { timeline.max = String(audio.duration); });
  audio.addEventListener('error', () => { status.textContent = '音频加载失败，请选择本地音频。'; });
  timeline.addEventListener('input', () => {
    audio.currentTime = Number(timeline.value);
    displayPose();
  });
  tempo.addEventListener('change', () => {
    tempo.value = String(Math.min(180, Math.max(45, Number(tempo.value) || defaultTempo)));
    displayPose();
  });
  file.addEventListener('change', () => {
    const song = file.files[0];
    if (!song) return;
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = URL.createObjectURL(song);
    changeSource(audioUrl, song.name);
  });
  restore.addEventListener('click', () => {
    URL.revokeObjectURL(audioUrl);
    audioUrl = null;
    file.value = '';
    changeSource(source, sourceLabel, sourceTempo);
  });
  for (const button of document.querySelectorAll('[data-view]')) {
    button.disabled = false;
    button.addEventListener('click', () => avatar.setView(button.dataset.view));
  }
  timeline.max = String(Number.isFinite(audio.duration) ? audio.duration : duration);
  play.disabled = timeline.disabled = file.disabled = false;
  if (referenceTrack) changeSource(source, sourceLabel, sourceTempo);
  else {
    status.textContent = '20 秒舞蹈 · 拖动阿德切换角度';
    displayPose();
  }
} catch (error) {
  status.textContent = '舞蹈模型加载失败。';
  console.error(error);
}
