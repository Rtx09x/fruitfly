(function(root){
  function motion(frame, previous, width, height){
    if(!previous || frame.length!==previous.length) return {left:0,right:0};
    let left=0,right=0,half=Math.floor(width/2),pixels=half*height;
    for(let y=0;y<height;y++) for(let x=0;x<half;x++){
      let i=(y*width+x)*4;
      left+=Math.abs(frame[i]-previous[i])+Math.abs(frame[i+1]-previous[i+1])+Math.abs(frame[i+2]-previous[i+2]);
      i=(y*width+x+half)*4;
      right+=Math.abs(frame[i]-previous[i])+Math.abs(frame[i+1]-previous[i+1])+Math.abs(frame[i+2]-previous[i+2]);
    }
    return {left:Math.min(1,left/(pixels*80)),right:Math.min(1,right/(pixels*80))};
  }
  function audio(samples){
    if(!samples.length) return {rms:0,zcr:0};
    let power=0,crossings=0;
    for(let i=0;i<samples.length;i++){power+=samples[i]*samples[i];if(i&&((samples[i]>=0)!==(samples[i-1]>=0)))crossings++}
    return {rms:Math.min(1,Math.sqrt(power/samples.length)*4),zcr:crossings/Math.max(1,samples.length-1)};
  }
  const api={motion,audio};if(typeof module!=='undefined')module.exports=api;root.MediaFeatures=api;
})(typeof window==='undefined'?globalThis:window);
