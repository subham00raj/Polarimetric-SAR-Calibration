/* The individual slide HTML files are the source of truth. No build step. */
(() => {
  const entries=window.THESIS_SLIDES||[];
  if(!entries.length)return;
  const frame=document.getElementById('presentation');
  const isStatic=new URLSearchParams(location.search).has('static');
  const limit=index=>Math.max(0,Math.min(entries.length-1,index));
  const fromHash=()=>limit((parseInt(location.hash.slice(1),10)||1)-1);
  let current=-1, ready=false;
  const pendingKeys=[];
  if(isStatic){
    document.documentElement.classList.add('static');frame.remove();
    entries.forEach((entry,index)=>{
      const page=document.createElement('iframe');page.className='print-slide';
      page.title=`${index+1}. ${entry.name}`;page.src=entry.file+'?static';
      document.body.appendChild(page);
    });
    return;
  }
  function show(index,atEnd=false){
    index=limit(index);current=index;ready=false;pendingKeys.length=0;
    frame.title=`${index+1}. ${entries[index].name}`;
    frame.src=entries[index].file+'?embedded=1&deck='+entries.length+(atEnd?'#end':'');
    history.replaceState(null,'','#'+(index+1));
    document.title=`${String(index+1).padStart(2,'0')} · ${entries[index].name} · PolSAR Defence`;
  }
  function refreshFrameSize() {
    requestAnimationFrame(()=>frame.contentWindow?.postMessage({type:'thesis:resize'},'*'));
  }
  frame.addEventListener('load',()=>{frame.contentWindow.focus();refreshFrameSize();});
  addEventListener('resize',refreshFrameSize);
  window.visualViewport?.addEventListener('resize',refreshFrameSize);
  document.addEventListener('fullscreenchange',()=>{
    refreshFrameSize();
    // Browser fullscreen chrome can settle after the initial event.
    setTimeout(refreshFrameSize,150);
    setTimeout(refreshFrameSize,700);
  });
  async function toggleFullscreen() {
    try {
      if(document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch(error) { console.warn('Fullscreen unavailable:',error.message); }
  }
  function forwardKey(key,code) {
    const message={type:'thesis:key',key,code};
    if(ready) frame.contentWindow.postMessage(message,'*');
    else pendingKeys.push(message);
  }
  addEventListener('message',event=>{
    if(event.source!==frame.contentWindow)return;
    if(event.data?.type==='thesis:ready') {
      ready=true;
      pendingKeys.splice(0).forEach(message=>frame.contentWindow.postMessage(message,'*'));
    } else if(event.data?.type==='thesis:fullscreen') {
      toggleFullscreen();
    } else if(event.data?.type==='thesis:goto') {
      const index=event.data.index;
      if(Number.isInteger(index)&&index>=0&&index<entries.length)show(index,event.data.atEnd===true);
    }
  });
  addEventListener('hashchange',()=>{if(fromHash()!==current)show(fromHash());});
  addEventListener('keydown',event=>{
    if(event.ctrlKey||event.metaKey||event.altKey)return;
    const key=({KeyF:'f',KeyM:'m',KeyO:'o'})[event.code]||event.key;
    const keys=['ArrowRight','ArrowDown',' ','PageDown','Enter','ArrowLeft','ArrowUp','PageUp','Backspace','Home','End','m','M','o','O','Escape'];
    if(key==='f'||key==='F'){
      event.preventDefault();
      toggleFullscreen();
    }else if(keys.includes(key)){
      event.preventDefault();forwardKey(key,event.code);
    }
  });
  show(fromHash());
})();
