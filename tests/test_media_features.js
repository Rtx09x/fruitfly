const assert=require('assert');
const f=require('../fruitfly/static/media_features.js');
let a=new Uint8ClampedArray(8*4),b=new Uint8ClampedArray(a);b[0]=80;b[1]=80;b[2]=80;
let m=f.motion(b,a,4,2);assert(m.left>0);assert.strictEqual(m.right,0);
let quiet=f.audio(new Float32Array(64));assert.deepStrictEqual(quiet,{rms:0,zcr:0});
let wave=f.audio(Float32Array.from([1,-1,1,-1]));assert.strictEqual(wave.rms,1);assert.strictEqual(wave.zcr,1);
console.log('media feature tests passed');
