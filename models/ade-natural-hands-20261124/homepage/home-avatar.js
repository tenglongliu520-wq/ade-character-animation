import * as THREE from 'three';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';

const MODEL = new URL('./ade-84aedc8.glb', import.meta.url).href;
const SMOOTH = (value) => {
  const t = Math.min(1, Math.max(0, value));
  return t * t * (3 - 2 * t);
};

export class HomeAdeAvatar {
  constructor(host, media) {
    this.host = host;
    this.media = media;
    this.mode = 'idle';
    this.paused = true;
    this.visible = true;
    this.time = 0;
    this.speech = { level: 0, at: 0 };
    this.frame = 0;
    this.last = 0;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(32, 1, .05, 16);
    this.camera.position.set(0, 1.17, 4.55);
    this.camera.lookAt(0, 1.17, 0);
    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    host.append(this.renderer.domElement);

    this.scene.add(new THREE.HemisphereLight(0xfff6ee, 0xe7dec9, 2.30));
    for (const [color, intensity, position] of [
      [0xffe2c9, 1.65, [-3, 4.4, 3.1]],
      [0xeaf2ff, .48, [2.5, 2.9, 3]],
      [0xfff2e7, .9, [0, 1.6, 5]],
      [0xffddb0, .72, [1.5, 3.8, -2]],
    ]) {
      const light = new THREE.DirectionalLight(color, intensity);
      light.position.set(...position);
      this.scene.add(light);
    }

    this.wake = () => {
      if (document.hidden) this.last = 0;
      else this.schedule();
    };
    document.addEventListener('visibilitychange', this.wake);
    this.media.addEventListener('change', this.wake);
    this.resizeObserver = new ResizeObserver(() => {
      this.resize();
      this.schedule();
    });
    this.resizeObserver.observe(host);
    this.visibilityObserver = new IntersectionObserver(([entry]) => {
      this.visible = entry.isIntersecting;
      this.last = 0;
      this.schedule();
    });
    this.visibilityObserver.observe(host);
    this.ready = this.load();
  }

  async load() {
    const result = await new GLTFLoader().loadAsync(MODEL);
    this.modelAttach(result);
    this.resize();
    this.renderer.render(this.scene, this.camera);
  }

  modelAttach(result) {
    this.model = result.scene;
    this.scene.add(this.model);
    this.head = this.model.getObjectByName('Head_expression_pivot');
    this.torso = this.model.getObjectByName('Upper_body_balance');
    this.morphs = [];
    this.model.traverse((node) => {
      if (node.morphTargetDictionary) this.morphs.push(node);
    });
    const dance = result.animations.find((clip) => clip.name === 'RowingDance');
    if (!this.head || !this.torso || !dance) throw new Error('Ade model is missing its animation nodes');
    this.mixer = new THREE.AnimationMixer(this.model);
    this.clips = new Map([
      ['hello', this.mixer.clipAction(THREE.AnimationUtils.subclip(dance, 'HomeHello', 1, 68, 30))],
      ['spin', this.mixer.clipAction(THREE.AnimationUtils.subclip(dance, 'HomeSpin', 796, 915, 30))],
    ]);
  }

  resize() {
    const { width, height } = this.host.getBoundingClientRect();
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  setState(mode) {
    this.mode = ['listen', 'talk', 'think', 'idle'].includes(mode) ? mode : 'idle';
    if (this.mode === 'talk') this.finishAction();
    this.schedule();
  }

  setSpeechLevel(level) {
    this.speech = { level: Number.isFinite(level) ? Math.max(0, Math.min(1, level)) : 0, at: performance.now() };
    this.schedule();
  }

  setPaused(paused) {
    if (this.paused === paused) return;
    this.paused = paused;
    this.last = 0;
    this.schedule();
  }

  greet() {
    return this.playAction('hello');
  }

  playAction(name) {
    const durations = { think: 2.0, turn: 2.05 };
    const playback = this.clips?.get(name);
    if (this.paused || this.media.matches || this.mode === 'talk' || this.active ||
        !this.model || (!playback && !durations[name])) return false;
    const duration = playback?.getClip().duration ?? durations[name];
    this.active = { name, elapsed: 0, duration, playback };
    playback?.reset().setLoop(THREE.LoopOnce, 1).setEffectiveWeight(0).play();
    if (playback) playback.clampWhenFinished = true;
    this.host.dataset.motionState = name;
    this.schedule();
    return true;
  }

  finishAction() {
    if (!this.active) return;
    this.active.playback?.stop();
    this.active = null;
    this.model.rotation.y = 0;
    this.head.rotation.set(0, 0, 0);
    this.torso.rotation.set(0, 0, 0);
    delete this.host.dataset.motionState;
  }

  renderFace(now) {
    const blink = Math.max(0, 1 - Math.abs((this.time % 4.8) - 4.55) / .11);
    const talking = this.mode === 'talk' && now - this.speech.at < 240 ? this.speech.level : 0;
    const thinking = this.mode === 'think' || this.active?.name === 'think';
    for (const node of this.morphs) {
      for (const [name, value] of [['blink', blink], ['smileOpen', talking],
        ['smile', .27 + talking * .5], ['cheekLift', .22 + talking * .3],
        ['curiousLift', thinking ? .34 : 0]]) {
        const index = node.morphTargetDictionary[name];
        if (index !== undefined) node.morphTargetInfluences[index] = value;
      }
    }
  }

  schedule() {
    if (!this.model || this.frame || document.hidden || !this.visible) return;
    this.frame = requestAnimationFrame((now) => this.tick(now));
  }

  tick(now) {
    this.frame = 0;
    const moving = !this.paused && !this.media.matches && !document.hidden && this.visible;
    if (moving && this.last && now - this.last < 31) {
      this.schedule();
      return;
    }
    if (moving) {
      const dt = this.last ? (now - this.last) / 1000 : 0;
      this.last = now;
      this.time += dt;
      if (this.active) {
        const action = this.active;
        action.elapsed += dt;
        const elapsed = action.elapsed;
        const weight = SMOOTH(elapsed / .30) * SMOOTH((action.duration - elapsed) / .38);
        if (action.playback) {
          action.playback.setEffectiveWeight(weight);
          this.mixer.update(dt);
        } else if (action.name === 'turn') {
          this.model.rotation.y = 1.42 * Math.sin(Math.PI * Math.min(1, elapsed / action.duration)) ** 2;
        } else {
          this.head.rotation.z = .19 * weight;
          this.head.rotation.y = -.12 * weight;
        }
        if (elapsed >= action.duration) this.finishAction();
      }
      if (!this.active?.playback) {
        this.torso.rotation.x = Math.sin(this.time * 1.9) * .006;
        this.renderFace(now);
      }
    } else this.last = 0;
    this.renderer.render(this.scene, this.camera);
    if (moving) this.schedule();
  }

  destroy() {
    cancelAnimationFrame(this.frame);
    this.resizeObserver.disconnect();
    this.visibilityObserver.disconnect();
    document.removeEventListener('visibilitychange', this.wake);
    this.media.removeEventListener('change', this.wake);
    this.mixer?.stopAllAction();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
