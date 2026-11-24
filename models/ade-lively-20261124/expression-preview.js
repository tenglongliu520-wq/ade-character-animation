import { Ade3DAvatar } from './avatar-3d.js';

const stage = document.querySelector('#stage');
const status = document.querySelector('#status');
const reference = document.querySelector('figure img');
const playButton = document.querySelector('#play');
const poseButton = document.querySelector('#pose');
const timeline = document.querySelector('#timeline');
const avatar = new Ade3DAvatar(stage);
avatar.setPaused(true);

function setView(view) {
  avatar.setView(view);
  const images = {
    front: 'reference-front.png',
    rightQuarter: 'reference-right.png',
    leftQuarter: 'reference-left.png',
  };
  if (images[view]) reference.src = images[view];
}

try {
  await avatar.ready;
  const action = avatar.actions.get('LookTiltReturn');
  if (!action) throw new Error('LookTiltReturn clip unavailable');
  const duration = action.getClip().duration;
  action.play();
  let frame = 0;

  function displayPose(seconds) {
    action.time = Math.min(duration, Math.max(0, seconds));
    avatar.mixer.update(0);
    timeline.value = String(action.time);
    avatar.schedule();
  }

  function stop() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    playButton.textContent = '播放「看过来」';
  }

  timeline.max = String(duration);
  timeline.disabled = false;
  playButton.disabled = false;
  poseButton.disabled = false;
  displayPose(0);
  status.textContent = '本轮三维模型 · 可播放短动作';
  playButton.addEventListener('click', () => {
    if (frame) {
      stop();
      return;
    }
    displayPose(0);
    playButton.textContent = '暂停动作';
    const start = performance.now();
    function advance(now) {
      const seconds = (now - start) / 1000;
      displayPose(seconds);
      if (seconds < duration) frame = requestAnimationFrame(advance);
      else stop();
    }
    frame = requestAnimationFrame(advance);
  });
  poseButton.addEventListener('click', () => {
    stop();
    setView('portrait');
    displayPose(50 / 30);
  });
  timeline.addEventListener('input', () => {
    stop();
    displayPose(Number(timeline.value));
  });
  for (const button of document.querySelectorAll('[data-view]')) {
    button.disabled = false;
    button.addEventListener('click', () => {
      stop();
      displayPose(0);
      setView(button.dataset.view);
    });
  }
  document.querySelector('#portrait').disabled = false;
  document.querySelector('#portrait').addEventListener('click', () => setView('portrait'));
} catch (error) {
  status.textContent = '预览加载失败';
  console.error(error);
}
