/* Original local spotlight. No network requests, synthetic inference or live controls. */
(() => {
  const doc=window.parent.document, win=window.parent, owner=window.frameElement;
  doc.getElementById('bio-tour-root')?.remove();
  const root=doc.createElement('div'); root.id='bio-tour-root';
  const data=tourData, light=data.light;
  root.innerHTML=`<style>
  #bio-tour-root{position:fixed;inset:0;z-index:2147483000;pointer-events:none;font-family:Inter,system-ui,sans-serif;color:${light?'#172033':'#eef2f6'};}
  #bio-tour-root .tour-block{position:fixed;pointer-events:auto;}
  #bio-tour-root svg{position:fixed;inset:0;width:100%;height:100%;pointer-events:none;}
  #bio-tour-root .tour-ring{position:fixed;border:2px solid #20b9ca;border-radius:12px;box-shadow:0 0 0 3px #20b9ca18;pointer-events:none;box-sizing:border-box;}
  #bio-tour-card{position:fixed;box-sizing:border-box;width:min(440px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;pointer-events:auto;background:${light?'#fff':'#151e29'};border:1px solid ${light?'#dbe2ea':'#4b5b6d'};box-shadow:0 16px 56px #09132144;border-radius:12px;padding:18px;}
  #bio-tour-card .tour-head{display:flex;justify-content:space-between;align-items:center;gap:12px;}
  #bio-tour-card .tour-counter{font-size:12px;font-weight:650;color:${light?'#00766f':'#6ce4cb'};}
  #bio-tour-card h2{font-size:20px;line-height:1.4;margin:12px 0 8px;color:inherit!important;letter-spacing:-.03em;}
  #bio-tour-card p{font-size:13px;line-height:1.7;margin:0 0 12px;color:inherit;}
  #bio-tour-card figure{margin:10px 0;overflow:hidden;border:1px solid ${light?'#e0e7ee':'#435366'};border-radius:7px;background:${light?'#f8fafc':'#0b0f14'};}
  #bio-tour-card img{display:block;width:100%;height:86px;object-fit:cover;object-position:top;}
  #bio-tour-card figcaption{padding:4px 8px;font-size:10px;color:${light?'#526276':'#b4c1d0'};}
  #bio-tour-card .tour-tip{padding:9px 10px;background:${light?'#f2fafb':'#143238'};border:1px solid ${light?'#cdebf0':'#36606c'};border-radius:6px;font-size:11px;line-height:1.6;color:${light?'#41667a':'#bdd6df'};}
  #bio-tour-card button{pointer-events:auto;cursor:pointer;font:500 12px system-ui;padding:8px 12px;border:1px solid ${light?'#d1d9e2':'#617184'};border-radius:8px;color:inherit;background:${light?'#fff':'#1c2939'};}
  #bio-tour-card button:focus-visible{outline:2px solid #14b8a6;outline-offset:3px;}
  #bio-tour-card button:disabled{opacity:.4;cursor:default;}
  #bio-tour-card .tour-primary{background:#007e77;border-color:#007e77;color:#fff;}
  #bio-tour-card .tour-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:13px;}
  #bio-tour-card .tour-actions{display:flex;gap:7px;}
  #bio-tour-card .tour-dots{display:flex;gap:5px;margin-top:14px;}
  #bio-tour-card .tour-dots i{height:5px;flex:1;border-radius:4px;background:${light?'#d5dde6':'#49586a'};}
  #bio-tour-card .tour-dots i.done{background:#0aa99d;}
  #bio-tour-card .tour-replay{font-size:10px;color:${light?'#5a6a7c':'#b4c1d0'};margin:10px 0 0;}
  </style>
  <svg aria-hidden="true"><defs><mask id="bio-tour-mask"><rect width="100%" height="100%" fill="white"/><rect id="bio-tour-hole" fill="black" rx="12"/></mask></defs><rect width="100%" height="100%" fill="rgba(20,31,49,.57)" mask="url(#bio-tour-mask)"/></svg>
  <div class="tour-ring"></div>${'<div class="tour-block"></div>'.repeat(4)}
  <section id="bio-tour-card" role="dialog" aria-modal="true" aria-label="Guided tutorial" lang="en" tabindex="-1">
  <div class="tour-head"><span class="tour-counter"></span><button data-action="exit_demo" aria-label="Close tutorial">Close</button></div>
  <h2></h2><p class="tour-body"></p><figure hidden><img alt="Actual screen for this step"/><figcaption>Actual screen example</figcaption></figure><div class="tour-tip"></div>
  <div class="tour-dots"></div><div class="tour-foot"><button data-action="exit_demo">Skip</button><div class="tour-actions"><button data-action="tour_play">${data.playing?'Pause':'Autoplay'}</button><button data-action="tour_back">Back</button><button class="tour-primary" data-action="${data.index===data.count-1?'exit_demo':'tour_next'}">${data.index===data.count-1?'Finish':'Next'}</button></div></div>
  <p class="tour-replay">REPLAY · real local checks and saved results · no new model calls</p>
  </section>`;
  const card=root.querySelector('#bio-tour-card');
  card.querySelector('.tour-counter').textContent=`Step ${data.index+1} of ${data.count}`;
  card.querySelector('h2').textContent=data.title;
  card.querySelector('.tour-body').textContent=data.body;
  card.querySelector('.tour-tip').textContent=data.tip;
  card.querySelector('.tour-dots').innerHTML=Array.from({length:data.count},(_,i)=>`<i class="${i<=data.index?'done':''}"></i>`).join('');
  card.querySelector('[data-action="tour_back"]').disabled=data.index===0;
  if(data.picture){card.querySelector('img').src=data.picture;card.querySelector('figure').hidden=false;}
  let disposed=false, initialTarget=null;
  const activate=key=>{const button=doc.querySelector(`.st-key-${key} button`); if(button&&!button.disabled)button.click();};
  card.addEventListener('click',e=>{const button=e.target.closest('button[data-action]');if(button)activate(button.dataset.action);});
  function update(){
    if(disposed)return;
    const target=doc.querySelector(data.selector);
    if(!target)return;
    if(initialTarget!==target){initialTarget=target; target.scrollIntoView({block:data.focus_height?'start':'center',behavior:'instant'});}
    const b=target.getBoundingClientRect(), w=win.innerWidth,h=win.innerHeight,pad=7;
    const x=Math.max(7,b.left-pad), y=Math.max(7,b.top-pad),right=Math.min(w-7,b.right+pad),bottom=Math.min(h-7,b.bottom+pad,data.focus_height?b.top+data.focus_height:h);
    const width=Math.max(20,right-x),height=Math.max(20,bottom-y);
    const hole=root.querySelector('#bio-tour-hole');
    for(const [key,value] of Object.entries({x,y,width,height}))hole.setAttribute(key,String(value));
    Object.assign(root.querySelector('.tour-ring').style,{left:x+'px',top:y+'px',width:width+'px',height:height+'px'});
    const blocks=root.querySelectorAll('.tour-block');
    const rects=[[0,0,w,y],[0,y,x,height],[right,y,w-right,height],[0,bottom,w,h-bottom]];
    blocks.forEach((el,i)=>{const [l,t,ww,hh]=rects[i];Object.assign(el.style,{left:l+'px',top:t+'px',width:Math.max(0,ww)+'px',height:Math.max(0,hh)+'px'});});
    const sideSpace=Math.max(x,w-right), preferred=Math.min(440,w-28);
    card.style.width=(sideSpace>340?Math.min(preferred,sideSpace-32):preferred)+'px';
    const cw=card.offsetWidth,ch=card.offsetHeight;
    let cx=Math.max(14,Math.min(w-cw-14,x)),cy;
    if(x>cw+32){cx=x-cw-18;cy=Math.max(14,Math.min(h-ch-14,y));}
    else if(w-right>cw+32){cx=right+18;cy=Math.max(14,Math.min(h-ch-14,y));}
    else if(h-bottom>ch+24){cy=bottom+14;}
    else if(y>ch+24){cy=y-ch-14;}
    else{cy=Math.max(14,h-ch-14);}
    Object.assign(card.style,{left:cx+'px',top:cy+'px'});
  }
  function keydown(e){
    if(e.key==='Escape'){e.preventDefault();activate('exit_demo');}
    if(e.key==='ArrowRight' && !/INPUT|TEXTAREA|SELECT/.test(doc.activeElement?.tagName||'')){e.preventDefault();activate(data.index===data.count-1?'exit_demo':'tour_next');}
    if(e.key==='Tab'){
      const target=doc.querySelector(data.selector), nodes=[...(target?target.querySelectorAll('input,select,textarea,button,[tabindex="0"]'):[]),...card.querySelectorAll('button:not(:disabled)')].filter(n=>n.getClientRects().length&&!n.disabled);
      if(!nodes.length)return;
      const index=nodes.indexOf(doc.activeElement),next=e.shiftKey?(index<=0?nodes.length-1:index-1):(index+1)%nodes.length;
      e.preventDefault();nodes[next].focus();
    }
  }
  doc.body.append(root); doc.body.classList.add('tour-overlay-active');
  win.addEventListener('resize',update);doc.addEventListener('scroll',update,true);doc.addEventListener('keydown',keydown,true);
  const observer=new win.ResizeObserver(update);observer.observe(doc.body);
  const cleanup=new win.MutationObserver(()=>{if(!owner?.isConnected){disposed=true;observer.disconnect();cleanup.disconnect();win.removeEventListener('resize',update);doc.removeEventListener('scroll',update,true);doc.removeEventListener('keydown',keydown,true);if(doc.getElementById('bio-tour-root')===root){root.remove();doc.body.classList.remove('tour-overlay-active');}}});
  cleanup.observe(doc.body,{childList:true,subtree:true});
  update();win.requestAnimationFrame(update);win.setTimeout(update,200);
  card.querySelector('.tour-primary').focus({preventScroll:true});
})();
