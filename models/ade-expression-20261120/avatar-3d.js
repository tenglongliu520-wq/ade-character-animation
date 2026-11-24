import * as THREE from 'three';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
import {OrbitControls} from './vendor/controls/OrbitControls.js';

/** Standalone reference viewer. No change to the live homepage or voice API. */
export class Ade3DAvatar {
  constructor(host, {modelUrl = new URL('./ade.glb', import.meta.url).href} = {}) {
    this.host=host;this.modelUrl=modelUrl;this.mode='idle';this.paused=false;this.destroyed=false;
    this.frame=0;this.time=0;this.last=0;this.speech={level:0,at:0};this.currentAction=null;
    this.motion=matchMedia('(prefers-reduced-motion: reduce)');
    this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#17161b');
    this.camera=new THREE.PerspectiveCamera(32,1,.05,30);this.camera.position.set(0,1.17,4.3);
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    this.renderer.outputColorSpace=THREE.SRGBColorSpace;
    this.renderer.toneMapping=THREE.NoToneMapping;this.renderer.toneMappingExposure=1;
    this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFShadowMap;
    this.renderer.domElement.setAttribute('aria-label','阿德三维角色，可拖动旋转和缩放');
    this.renderer.domElement.setAttribute('role','img');host.append(this.renderer.domElement);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);
    this.controls.target.set(0,1.17,0);this.controls.minDistance=2.8;this.controls.maxDistance=7;
    this.controls.minPolarAngle=.28;this.controls.maxPolarAngle=Math.PI*.72;
    this.controls.enablePan=false;this.controls.enableDamping=true;
    this.scene.add(new THREE.HemisphereLight(0xfff6ee,0xb8c7bd,2.15));
    const key=new THREE.DirectionalLight(0xffe2c9,1.65);key.position.set(-3,4.4,3.1);key.castShadow=true;
    key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.1,far:12});
    key.shadow.normalBias=.025;this.scene.add(key);
    const fill=new THREE.DirectionalLight(0xeaf2ff,.48);fill.position.set(2.5,2.9,3);this.scene.add(fill);
    const rim=new THREE.DirectionalLight(0xffddb0,.85);rim.position.set(1.5,3.8,-2);this.scene.add(rim);
    const floor=new THREE.Mesh(new THREE.CircleGeometry(8,64),new THREE.ShadowMaterial({opacity:.12}));
    floor.rotation.x=-Math.PI/2;floor.position.y=-.006;floor.receiveShadow=true;this.scene.add(floor);
    this.onVisibility=()=>this.schedule();this.onMotion=()=>this.schedule();
    document.addEventListener('visibilitychange',this.onVisibility);this.motion.addEventListener('change',this.onMotion);
    this.resizeObserver=new ResizeObserver(()=>{this.resize();this.schedule();});this.resizeObserver.observe(host);
    this.controls.addEventListener('change',()=>this.schedule());this.resize();
    this.ready=this.load();
  }
  async load() {
    const gltf=await new GLTFLoader().loadAsync(this.modelUrl);
    if(this.destroyed){this.disposeModel(gltf.scene);return false;}
    this.model=gltf.scene;this.scene.add(this.model);this.morphs=[];this.skinCount=0;
    this.model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}
      if(o.isSkinnedMesh)this.skinCount++;
      if(o.morphTargetDictionary)this.morphs.push(o);
    });
    this.mixer=new THREE.AnimationMixer(this.model);this.actions=new Map();
    for(const clip of gltf.animations)this.actions.set(clip.name,this.mixer.clipAction(clip));
    this.setState('idle');this.host.dataset.ready='true';this.schedule();return true;
  }
  resize(){const {width,height}=this.host.getBoundingClientRect();if(!width||!height)return;
    this.camera.aspect=width/height;this.camera.updateProjectionMatrix();this.renderer.setSize(width,height,false);}
  setState(state){
    const key={listen:'idle',talk:'idle',hello:'wave'}[state]||state;
    if(!['idle','wave','think'].includes(key))return false;
    this.mode=state;this.host.dataset.state=state;
    const next=this.actions?.get(key);if(!next)return false;
    if(this.currentAction!==next){
      const previous=this.currentAction;next.reset().setEffectiveTimeScale(1).setEffectiveWeight(1).play();
      if(previous)previous.crossFadeTo(next,.22,false);this.currentAction=next;
    }
    this.schedule();return true;
  }
  setSpeechLevel(level){this.speech={level:Math.max(0,Math.min(1,Number(level)||0)),at:performance.now()};this.schedule();}
  setPaused(value){this.paused=Boolean(value);this.schedule();}
  setFace({blink=0,mouth=0}){for(const o of this.morphs||[]){
    for(const [name,value] of [['blink',blink],['jawOpen',mouth]]){
      const i=o.morphTargetDictionary[name];if(i!==undefined)o.morphTargetInfluences[i]=Math.max(0,Math.min(1,value));
    }
  }}
  setView(name){const p={front:[0,1.17,4.3],side:[4.3,1.30,0],back:[0,1.30,-4.3],quarter:[2.2,1.6,3.7],rightQuarter:[-2.2,1.4,3.7],leftQuarter:[2.2,1.4,3.7]}[name];
    if(!p)return;this.camera.position.set(...p);this.controls.target.set(0,1.17,0);this.controls.update();this.schedule();}
  schedule(){if(this.destroyed||this.frame)return;this.frame=requestAnimationFrame(t=>this.tick(t));}
  tick(now){
    this.frame=0;if(this.destroyed)return;
    const moving=!this.paused&&!this.motion.matches&&!document.hidden;
    const dt=this.last?Math.min(.05,(now-this.last)/1000):0;this.last=now;
    if(moving){this.time+=dt;this.mixer?.update(dt);}
    const blink=moving?Math.max(0,1-Math.abs((this.time%4.6)-4.35)/.11):0;
    const mouth=moving&&now-this.speech.at<260?this.speech.level:0;
    if (!this.actions?.has('LookTiltReturn')) this.setFace({blink,mouth});
    this.controls.update();this.renderer.render(this.scene,this.camera);
    if(moving)this.schedule();
    else this.last=0;
  }
  disposeModel(root){root.traverse(o=>{o.geometry?.dispose();const materials=o.material?(Array.isArray(o.material)?o.material:[o.material]):[];
    for(const m of materials){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});}
  destroy(){this.destroyed=true;cancelAnimationFrame(this.frame);this.resizeObserver.disconnect();
    document.removeEventListener('visibilitychange',this.onVisibility);this.motion.removeEventListener('change',this.onMotion);
    this.controls.dispose();this.mixer?.stopAllAction();if(this.model)this.mixer?.uncacheRoot(this.model);
    this.disposeModel(this.scene);this.renderer.dispose();this.renderer.domElement.remove();}
}

