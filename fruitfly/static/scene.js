// Perspective-projected geometry. All locomotion remains driven by neural outputs.
const stage=document.querySelector('.arena'), cam=document.querySelector('.camera-stage');
stage.appendChild(cam); document.querySelector('.hero').classList.add('immersive');
const heading=document.createElement('div');heading.className='direction';heading.textContent='YOU / CAMERA';stage.appendChild(heading);
const compass=document.createElement('div');compass.className='compass';stage.appendChild(compass);
for(const [id,icon,label] of [['camera','◉','Camera'],['microphone','♩','Microphone']]){
 const b=document.getElementById(id);b.classList.add('icon-control');b.dataset.icon=icon;b.title=label;b.setAttribute('aria-label','Toggle '+label);
}
let pose={x:0,z:0,a:Math.PI/2},seenTick=null,trail=[];
function project(x,y,z,w,h){const depth=5+z*.55;return [w/2+x*w*.40/depth,h*.49+(z*.44-y)*h*.48/depth,1/depth]}
function segment(c,a,b,color,width=1){c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.strokeStyle=color;c.lineWidth=width;c.stroke()}
window.drawFly=function(s){
 const w=arena.width,h=arena.height,m=s.motor,dt=seenTick===null?0:Math.max(0,s.tick-seenTick)*s.dt_ms/1000;seenTick=s.tick;
 if(!s.paused&&dt&&dt<2){pose.a+=m.turn*dt*2;pose.x+=Math.cos(pose.a)*m.speed*dt*1.4;pose.z+=Math.sin(pose.a)*m.speed*dt*1.4;pose.x=clamp(pose.x,-2.8,2.8);pose.z=clamp(pose.z,-2.5,2.5);if(m.speed>0){trail.push([pose.x,pose.z]);if(trail.length>100)trail.shift()}}
 const bg=ac.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#07151e');bg.addColorStop(1,'#172b32');ac.fillStyle=bg;ac.fillRect(0,0,w,h);
 for(let i=-6;i<=6;i++){segment(ac,project(i,0,-6,w,h),project(i,0,6,w,h),'#27434b');segment(ac,project(-6,0,i,w,h),project(6,0,i,w,h),'#27434b')}
 for(let i=1;i<trail.length;i++)segment(ac,project(trail[i-1][0],.01,trail[i-1][1],w,h),project(trail[i][0],.01,trail[i][1],w,h),`rgba(92,224,204,${i/trail.length*.5})`,2);
 const transform=(x,y,z)=>project(pose.x+x*Math.cos(pose.a)-z*Math.sin(pose.a),y,pose.z+x*Math.sin(pose.a)+z*Math.cos(pose.a),w,h);
 const shadow=transform(0,0,0);ac.fillStyle='#0006';ac.beginPath();ac.ellipse(shadow[0],shadow[1],54,15,0,0,7);ac.fill();
 const phase=s.tick*.3,walk=s.paused?0:m.speed;
 for(const side of [-1,1])for(let i=0;i<3;i++){const x=(i-1)*.27,swing=Math.sin(phase+i*2+side)*walk*.13;segment(ac,transform(x,.24,side*.08),transform(x-.12+swing,.12,side*.40),'#b4b6a6',3);segment(ac,transform(x-.12+swing,.12,side*.40),transform(x+.07+swing,.015,side*.60),'#829a92',2)}
 // Surface patches on ellipsoids, depth-sorted for a true perspective body.
 let patches=[];
 function ellipsoid(cx,cy,cz,rx,ry,rz,base){for(let j=0;j<12;j++)for(let i=0;i<20;i++){let vertices=[];for(const [a,b] of [[i,j],[i+1,j],[i+1,j+1],[i,j+1]]){let u=a/20*Math.PI*2,v=b/12*Math.PI;vertices.push(transform(cx+rx*Math.sin(v)*Math.cos(u),cy+ry*Math.cos(v),cz+rz*Math.sin(v)*Math.sin(u)))}let light=.42+.58*Math.max(0,Math.cos((j+.5)/12*Math.PI));patches.push({vertices,depth:vertices.reduce((a,p)=>a+p[2],0)/4,color:`rgb(${base.map(v=>Math.round(v*light)).join(',')})`})}
 }
 ellipsoid(-.28,.30,0,.47,.24,.24,[147,128,91]);ellipsoid(.13,.34,0,.28,.29,.25,[112,128,129]);ellipsoid(.43,.36,0,.22,.22,.23,[126,143,143]);ellipsoid(.49,.40,-.17,.13,.16,.10,[233,87,58]);ellipsoid(.49,.40,.17,.13,.16,.10,[233,87,58]);
 patches.sort((a,b)=>a.depth-b.depth);for(const p of patches){ac.beginPath();p.vertices.forEach((v,i)=>i?ac.lineTo(v[0],v[1]):ac.moveTo(v[0],v[1]));ac.closePath();ac.fillStyle=p.color;ac.fill()}
 for(const side of [-1,1]){const wing=[transform(.10,.57,side*.10),transform(-.60,.59+walk*.02*Math.sin(phase*3),side*.65),transform(-.88,.47,side*.45),transform(-.4,.48,side*.13)];ac.beginPath();wing.forEach((v,i)=>i?ac.lineTo(v[0],v[1]):ac.moveTo(v[0],v[1]));ac.closePath();ac.fillStyle='#bde3e54d';ac.fill();ac.strokeStyle='#ddfafa80';ac.lineWidth=1;ac.stroke();segment(ac,wing[0],wing[2],'#bde3e566')}
 const toward=Math.sin(pose.a);compass.textContent=m.speed===0?'STILL · waiting for neural output':toward>.25?'↓ TOWARD CAMERA':toward<-.25?'↑ AWAY FROM CAMERA':'↔ ACROSS YOUR VIEW';
};
let brainAngle=.2;
window.drawBrain=function(s){const w=brain.width,h=brain.height;bc.fillStyle='#09151d';bc.fillRect(0,0,w,h);brainAngle+=.003;const ca=Math.cos(brainAngle),sa=Math.sin(brainAngle);let dots=s.points.map(p=>{let x=p[0]-.5,z=p[2]-.5;return {x:x*ca-z*sa,y:p[1]-.5,z:x*sa+z*ca,v:p[3]}}).sort((a,b)=>a.z-b.z);for(const p of dots){let k=1/(1.8+p.z*.5),x=w/2+p.x*w*.95*k,y=h/2+p.y*h*1.3*k,v=clamp(p.v/25);bc.beginPath();bc.arc(x,y,(1.2+v*4)*k,0,7);bc.fillStyle=v>.05?`rgba(255,${Math.round(193-v*90)},85,${.5+v*.5})`:`rgba(76,174,190,${.18+(p.z+.5)*.35})`;bc.fill()}
 $('#count').textContent='Live neural activity';const p=s.populations;if(p)$('#neuralReadout').textContent=`Vision ${p.vision.toFixed(1)} · Sound ${p.sound.toFixed(1)} · Motor ${p.output.toFixed(3)} spikes/s`;
};
const readout=document.createElement('p');readout.id='neuralReadout';document.querySelector('.brain').appendChild(readout);
document.querySelector('.legend').textContent='1,800 neurons · actual 3D positions · amber = computed firing';
