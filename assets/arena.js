/* Arena MyTickets: minijogos (futebol, basquete, field goal, tiro ao alvo) em canvas, sem bibliotecas.
   Carregado só quando um quadro .mta-slot chega perto da tela (ver arena_home em scripts/gerar_paginas.py). */
(()=>{
const root=document.getElementById('mt-arena');if(!root)return;
const BASE='https://mytickets.tours';
const T={
pt:{kicker:'Arena MyTickets',title:'Aqueça antes do embarque',sub:'Quatro portões, quatro esportes. Faça sua melhor marca e veja o ingresso do evento de cada portão.',legal:'Guia independente. Ingressos vendidos e entregues pela Sports Events 365; podemos receber comissão, sem custo extra para você.',
 tabs:{soccer:'Futebol',basket:'Basquete',fg:'Futebol americano',tennis:'Tênis / Softball'},gate:'Portão',boarding:'Cartão de embarque',play:'▶ Jogue!',again:'▶ Jogar de novo',ctaB:'Jogue!',cta:'Escolha um portão, bata seu recorde e confira o evento de cada jogo. Leva 30 segundos.',
 how:{soccer:'👆 Arraste da bola para o gol',basket:'👆 Puxe para trás e solte',fg:'👆 Arraste para cima para chutar',tennis:'👆 Toque no alvo para lançar'},
 tix:'Ver ingressos →',guide:'Guia do evento',score:'Placar',left:'Restam',time:'Tempo',best:'Recorde',newb:'Novo recorde!',over:'Fim de jogo',wind:'Vento',goals:'gols',drag:'ARRASTE',tap:'TOQUE NO ALVO',others:'Outros jogos',mini:{soccer:'⚽ Pênaltis',basket:'🏀 Arremesso',fg:'🏈 Field goal',tennis:'🥎 Tiro ao alvo'},here:'▶ Jogar aqui',close:'Fechar o jogo',full:'Tela cheia',sound:'Som',
 hint:{soccer:'Arrasto mais longo = chute mais alto. O goleiro se mexe e lê o seu chute; as traves devolvem a bola. 5 cobranças.',basket:'Funciona como um estilingue. A mira mostra só o começo do arco: o resto é com você. Sem tocar no aro vale 3. 8 arremessos.',fg:'Mais longo = mais força. Passe entre as hastes do Y e por cima do travessão, de olho no vento. 6 chutes, cada vez mais longe.',tennis:'A bola leva um instante para chegar: mire à frente do alvo. Centro vale 100; acertos seguidos multiplicam. 30 segundos.'},
 r:{goal:'GOL!',save:'DEFENDEU!',post:'NA TRAVE!',high:'POR CIMA!',wide:'PRA FORA!',swish:'CHUÁ! +3',bank:'CESTA! +2',miss:'ERROU!',good:'É BOM! +',short:'CURTO!',bar:'NO TRAVESSÃO!',fwide:'TORTO!',fpost:'NA HASTE!'}},
en:{kicker:'MyTickets Arena',title:'Warm up before boarding',sub:'Four gates, four sports. Set your best score and see the tickets for each gate’s event.',legal:'Independent guide. Tickets are sold and delivered by Sports Events 365; we may earn a commission at no extra cost to you.',
 tabs:{soccer:'Football',basket:'Basketball',fg:'Field goal',tennis:'Tennis / Softball'},gate:'Gate',boarding:'Boarding pass',play:'▶ Play!',again:'▶ Play again',ctaB:'Play!',cta:'Pick a gate, beat your best score and check out each game’s event. Takes 30 seconds.',
 how:{soccer:'👆 Swipe from the ball to the goal',basket:'👆 Pull back and release',fg:'👆 Swipe up to kick',tennis:'👆 Tap the target to throw'},
 tix:'See tickets →',guide:'Event guide',score:'Score',left:'Left',time:'Time',best:'Best',newb:'New best!',over:'Full time',wind:'Wind',goals:'goals',drag:'SWIPE',tap:'TAP THE TARGET',others:'Other games',mini:{soccer:'⚽ Penalties',basket:'🏀 Hoops',fg:'🏈 Field goal',tennis:'🥎 Target'},here:'▶ Play here',close:'Close the game',full:'Full screen',sound:'Sound',
 hint:{soccer:'Longer swipe = higher shot. The keeper moves and reads your kick; the posts bounce the ball back. 5 penalties.',basket:'It works like a slingshot. The guide only shows the start of the arc: the rest is up to you. Nothing but net scores 3. 8 shots.',fg:'Longer = more power. Split the Y-shaped uprights and clear the crossbar, and watch the wind. 6 kicks, each one longer.',tennis:'The ball takes a moment to arrive, so lead the target. Bullseye scores 100; streaks multiply. 30 seconds.'},
 r:{goal:'GOAL!',save:'SAVED!',post:'OFF THE POST!',high:'OVER THE BAR!',wide:'WIDE!',swish:'SWISH! +3',bank:'BUCKET! +2',miss:'MISS!',good:'IT’S GOOD! +',short:'SHORT!',bar:'OFF THE CROSSBAR!',fwide:'NO GOOD!',fpost:'OFF THE UPRIGHT!'}},
es:{kicker:'Arena MyTickets',title:'Calienta antes de embarcar',sub:'Cuatro puertas, cuatro deportes. Haz tu mejor marca y mira las entradas del evento de cada puerta.',legal:'Guía independiente. Entradas vendidas y entregadas por Sports Events 365; podemos recibir una comisión sin costo extra para ti.',
 tabs:{soccer:'Fútbol',basket:'Básquet',fg:'Fútbol americano',tennis:'Tenis / Softball'},gate:'Puerta',boarding:'Tarjeta de embarque',play:'▶ ¡Juega!',again:'▶ Jugar otra vez',ctaB:'¡Juega!',cta:'Elige una puerta, supera tu récord y conoce el evento de cada juego. Toma 30 segundos.',
 how:{soccer:'👆 Desliza del balón al arco',basket:'👆 Tira hacia atrás y suelta',fg:'👆 Desliza hacia arriba para patear',tennis:'👆 Toca el blanco para lanzar'},
 tix:'Ver entradas →',guide:'Guía del evento',score:'Marcador',left:'Quedan',time:'Tiempo',best:'Récord',newb:'¡Nuevo récord!',over:'Final del juego',wind:'Viento',goals:'goles',drag:'DESLIZA',tap:'TOCA EL BLANCO',others:'Otros juegos',mini:{soccer:'⚽ Penales',basket:'🏀 Tiro al aro',fg:'🏈 Field goal',tennis:'🥎 Tiro al blanco'},here:'▶ Jugar aquí',close:'Cerrar el juego',full:'Pantalla completa',sound:'Sonido',
 hint:{soccer:'Más largo = tiro más alto. El arquero se mueve y lee tu tiro; los postes devuelven el balón. 5 penales.',basket:'Funciona como una resortera. La guía solo muestra el inicio del arco: el resto depende de ti. Sin tocar el aro vale 3. 8 tiros.',fg:'Más largo = más fuerza. Pasa entre los postes de la Y y por encima del travesaño, atento al viento. 6 patadas, cada vez más lejos.',tennis:'La pelota tarda un instante en llegar: apunta por delante del blanco. El centro vale 100; los aciertos seguidos multiplican. 30 segundos.'},
 r:{goal:'¡GOL!',save:'¡PARADA!',post:'¡AL PALO!',high:'¡POR ARRIBA!',wide:'¡AFUERA!',swish:'¡LIMPIA! +3',bank:'¡CANASTA! +2',miss:'¡FALLÓ!',good:'¡ES BUENO! +',short:'¡CORTO!',bar:'¡AL TRAVESAÑO!',fwide:'¡DESVIADO!',fpost:'¡AL POSTE!'}}
};
const EV={
 soccer:{e:'⚽',slug:'mexico-vs-jamaica-2026-11-17',g:16,from:'BOG',to:'MTY',d:[2026,11,17],
  n:{pt:'México x Jamaica',en:'Mexico vs Jamaica',es:'México vs Jamaica'},
  v:{pt:'Estadio BBVA · Monterrey',en:'Estadio BBVA · Monterrey',es:'Estadio BBVA · Monterrey'}},
 basket:{e:'🏀',slug:'knicks-vs-nuggets-2027-01-11',g:10,from:'MEX',to:'JFK',d:[2027,1,11],
  n:{pt:'New York Knicks x Denver Nuggets',en:'New York Knicks vs Denver Nuggets',es:'New York Knicks vs Denver Nuggets'},
  v:{pt:'Madison Square Garden · Nova York',en:'Madison Square Garden · New York',es:'Madison Square Garden · Nueva York'}},
 fg:{e:'🏈',slug:'ireland-vs-south-africa-2026-11-21',g:4,from:'LHR',to:'DUB',d:[2026,11,21],
  n:{pt:'Irlanda x África do Sul · Rúgbi',en:'Ireland vs South Africa · Rugby',es:'Irlanda vs Sudáfrica · Rugby'},
  v:{pt:'Aviva Stadium · Dublin',en:'Aviva Stadium · Dublin',es:'Aviva Stadium · Dublín'}},
 tennis:{e:'🥎',slug:'final-australian-open-2027-01-31',g:13,from:'EZE',to:'MEL',d:[2027,1,31],
  n:{pt:'Final do Australian Open',en:'Australian Open Final',es:'Final del Australian Open'},
  v:{pt:'Rod Laver Arena · Melbourne',en:'Rod Laver Arena · Melbourne',es:'Rod Laver Arena · Melbourne'}}
};
const KEYS=['soccer','basket','fg','tennis'];
const p0=location.pathname;
let L=(root.dataset.lang||(p0.startsWith('/en')?'en':p0.startsWith('/es')?'es':(document.documentElement.lang||'pt'))).slice(0,2).toLowerCase();
if(!T[L])L='pt';const g=T[L];
const MO={pt:['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'],es:['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'],en:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']};
const fdate=([y,m,d])=>L==='en'?`${MO.en[m-1]} ${d}, ${y}`:`${String(d).padStart(2,'0')} ${MO[L][m-1]} ${y}`;
const guideURL=k=>`${BASE}${L==='pt'?'/eventos/':L==='en'?'/en/events/':'/es/eventos/'}${EV[k].slug}/?utm_source=mytickets&utm_medium=arena&utm_campaign=${k}`;
const tixURL=k=>`${BASE}/go/ticketmaster/${L}/${EV[k].slug}/`;
root.querySelectorAll('[data-t]').forEach(el=>el.textContent=g[el.dataset.t]);

/* ---------- utilidades ---------- */
let W=960,H=540,PORT=false,UIS=1;
const stage=root.querySelector('.mta-stage'),cv=stage.querySelector('canvas'),ctx=cv.getContext('2d');
const ov=stage.querySelector('.mta-ov'),h1=stage.querySelector('.mta-h1'),h2=stage.querySelector('.mta-h2'),xb=stage.querySelector('.mta-x'),live=root.querySelector('.mta-live');
const fsb=root.querySelector('.mta-fs'),snd=root.querySelector('.mta-snd');
xb.setAttribute('aria-label',g.close);fsb.setAttribute('aria-label',g.full);fsb.title=g.full;snd.setAttribute('aria-label',g.sound);snd.title=g.sound;
const DPR=Math.min(window.devicePixelRatio||1,2);
const sizeCanvas=()=>{cv.width=Math.round(W*DPR);cv.height=Math.round(H*DPR)};
const clamp=(v,a,b)=>v<a?a:v>b?b:v,lerp=(a,b,t)=>a+(b-a)*t,rand=(a,b)=>a+Math.random()*(b-a);
function mk(){const c=document.createElement('canvas');c.width=Math.round(W*DPR);c.height=Math.round(H*DPR);const x=c.getContext('2d');x.setTransform(DPR,0,0,DPR,0,0);return[c,x];}
function pl(c,pts,close){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));if(close)c.closePath();}
function crowd(c,x0,y0,x1,y1,st){const cols=['#FFC23D','#f4f7fb','#3d7bd8','#e0574f','#7fb2ff','#2a4a70'];for(let y=y0;y<y1;y+=st*.8)for(let x=x0+Math.random()*st;x<x1;x+=st){c.fillStyle=cols[(Math.random()*6)|0];c.globalAlpha=.3+Math.random()*.4;c.beginPath();c.arc(x+rand(-2,2),y+rand(-2,2),st*.3,0,7);c.fill();}c.globalAlpha=1;}
function glow(c,x,y,r){const q=c.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,'rgba(255,240,200,.5)');q.addColorStop(1,'rgba(255,240,200,0)');c.fillStyle=q;c.fillRect(x-r,y-r,2*r,2*r);}
function sky(c,y1){const q=c.createLinearGradient(0,0,0,y1);q.addColorStop(0,'#050d18');q.addColorStop(1,'#14304f');c.fillStyle=q;c.fillRect(0,0,W,y1);}
function dashed(c,x0,y0,x1,y1){c.save();c.setLineDash([8*UIS,8*UIS]);c.strokeStyle='rgba(255,194,61,.9)';c.lineWidth=3*UIS;c.beginPath();c.moveTo(x0,y0);c.lineTo(x1,y1);c.stroke();c.restore();}
function label(c,txt,x,y,size=13,al='left'){size=Math.round(size*UIS);const pd=7*UIS;c.font=`700 ${size}px ui-monospace,Menlo,Consolas,monospace`;c.textAlign=al;c.fillStyle='rgba(11,23,38,.78)';const w=c.measureText(txt).width;const bx=al==='center'?x-w/2:al==='right'?x-w:x;c.fillRect(bx-pd,y-size-pd*.6,w+pd*2,size+pd*1.6);c.fillStyle='#FFC23D';c.fillText(txt,x,y);}

let muted=false;try{muted=localStorage.getItem('mta-mute')==='1'}catch(e){}
const setSnd=()=>{snd.textContent=muted?'🔇':'🔊';snd.setAttribute('aria-pressed',String(!muted))};setSnd();
snd.onclick=()=>{muted=!muted;setSnd();if(muted)bedOff();else if(run)bedOn();try{localStorage.setItem('mta-mute',muted?'1':'0')}catch(e){}};
let AC,NB,PB,BED=null,BAB=0;const CR={},FILES={};
const ac=()=>{if(muted)return null;try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();if(AC.state==='suspended')AC.resume();return AC}catch(e){return null}};
const noiseBuf=a=>{if(!NB){NB=a.createBuffer(1,a.sampleRate*2,a.sampleRate);const d=NB.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1}return NB};
/* ruído rosa estéreo: base do som de estádio */
function pink(a,sec=3){const n=Math.floor(a.sampleRate*sec),B=a.createBuffer(2,n,a.sampleRate);for(let ch=0;ch<2;ch++){const d=B.getChannelData(ch);let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0;for(let i=0;i<n;i++){const w=Math.random()*2-1;b0=.99886*b0+w*.0555179;b1=.99332*b1+w*.0750759;b2=.969*b2+w*.153852;b3=.8665*b3+w*.3104856;b4=.55*b4+w*.5329522;b5=-.7616*b5-w*.016898;d[i]=(b0+b1+b2+b3+b4+b5+b6+w*.5362)*.11;b6=w*.115926}}return B}
/* uma voz: corda vocal (dente de serra com leve tremor) + 2 formantes de vogal, posicionada no estéreo */
const VOW={a:[760,1150],o:[560,880],u:[330,800],e:[520,1750],oh:[620,960]};
function voice(a,dst,t,dur,f0,f1,f2,vw,gain,pan){const o=a.createOscillator(),F1=a.createBiquadFilter(),F2=a.createBiquadFilter(),g=a.createGain(),j=a.createOscillator(),jg=a.createGain();
 o.type='sawtooth';o.frequency.setValueAtTime(f0,t);o.frequency.linearRampToValueAtTime(f1,t+dur*.35);o.frequency.linearRampToValueAtTime(f2,t+dur);
 j.frequency.value=4.5+Math.random()*3;jg.gain.value=f0*.025;j.connect(jg).connect(o.frequency);
 F1.type=F2.type='bandpass';F1.frequency.value=vw[0]*(.9+Math.random()*.2);F2.frequency.value=vw[1]*(.9+Math.random()*.2);F1.Q.value=6;F2.Q.value=8;
 o.connect(F1);o.connect(F2);F1.connect(g);F2.connect(g);
 g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(gain,t+Math.min(.12,dur*.25));g.gain.setValueAtTime(gain,t+dur*.6);g.gain.linearRampToValueAtTime(0,t+dur);
 let out=g;if(a.createStereoPanner){const pn=a.createStereoPanner();pn.pan.value=pan;g.connect(pn);out=pn}out.connect(dst);o.start(t);j.start(t);o.stop(t+dur+.02);j.stop(t+dur+.02)}
/* palmas: rajadas curtas de ruído em momentos aleatórios */
function claps(a,dst,t0,sec,count,vol){const nb=noiseBuf(a);for(let i=0;i<count;i++){const t=t0+Math.pow(Math.random(),.8)*sec,s=a.createBufferSource(),f=a.createBiquadFilter(),g=a.createGain();s.buffer=nb;f.type='bandpass';f.frequency.value=1100+Math.random()*1600;f.Q.value=1.2;g.gain.setValueAtTime(vol*(.4+Math.random()*.6),t);g.gain.exponentialRampToValueAtTime(.0001,t+.03+Math.random()*.03);let out=g;if(a.createStereoPanner){const pn=a.createStereoPanner();pn.pan.value=Math.random()*1.8-.9;g.connect(pn);out=pn}s.connect(f).connect(g);out.connect(dst);s.start(t,Math.random()*1.5);s.stop(t+.08)}}
/* "chiado" do estádio: ruído rosa filtrado com envelope */
function swell(a,dst,t,dur,f,q,peak,atk){const s=a.createBufferSource(),fl=a.createBiquadFilter(),g=a.createGain();s.buffer=PB||(PB=pink(a));s.loop=true;fl.type='bandpass';fl.frequency.value=f;fl.Q.value=q;g.gain.setValueAtTime(.0001,t);g.gain.linearRampToValueAtTime(peak,t+atk);g.gain.setValueAtTime(peak,t+dur*.5);g.gain.exponentialRampToValueAtTime(.0001,t+dur);s.connect(fl).connect(g).connect(dst);s.start(t,Math.random()*2);s.stop(t+dur+.05)}
/* receitas de reação da torcida: centenas de vozes, palmas e chiado */
const RECIPES={
 roar:{sec:4.6,make(a,d){swell(a,d,0,4.4,520,.6,.2,.3);swell(a,d,.2,4,850,.5,.1,.5);const V=['oh','oh','o','o','u'];for(let i=0;i<56;i++){const t=Math.random()*.25,f=160+Math.random()*170;voice(a,d,t,2.6+Math.random()*1.4,f,f*1.35,f*1.2,VOW[V[i%5]],.05,Math.random()*1.8-.9)}for(let i=0;i<30;i++){const t=1.1+Math.random()*.4,f=190+Math.random()*150;voice(a,d,t,2+Math.random()*1.2,f*1.1,f*1.3,f*1.05,VOW[i%2?'oh':'o'],.04,Math.random()*1.8-.9)}}},
 cheer:{sec:2.8,make(a,d){swell(a,d,0,2.6,520,.6,.15,.25);for(let i=0;i<32;i++){const t=Math.random()*.2,f=170+Math.random()*140;voice(a,d,t,1.6+Math.random()*.8,f,f*1.3,f*1.12,VOW[i%3?'oh':'o'],.05,Math.random()*1.8-.9)}}},
 ooh:{sec:2.6,make(a,d){swell(a,d,0,2.4,520,.6,.16,.35);for(let i=0;i<40;i++){const t=Math.random()*.18,f=150+Math.random()*170;voice(a,d,t,1.5+Math.random()*.9,f,f*1.28,f*.68,VOW[i%3?'u':'o'],.05,Math.random()*1.8-.9)}}},
 aww:{sec:2.2,make(a,d){swell(a,d,0,2,480,.6,.1,.15);for(let i=0;i<26;i++){const t=Math.random()*.15,f=200+Math.random()*120;voice(a,d,t,1.2+Math.random()*.7,f,f*1.05,f*.6,VOW[i%2?'u':'o'],.045,Math.random()*1.8-.9)}}}
};
/* renderiza cada reação uma única vez (offline) e depois só toca o resultado: leve e sempre igual */
const RP={};function renderOne(k){if(RP[k])return RP[k];const r=RECIPES[k];RP[k]=new Promise(res=>{try{const sr=22050,o=new(window.OfflineAudioContext||window.webkitOfflineAudioContext)(2,Math.ceil(sr*r.sec),sr),m=o.createGain();m.connect(o.destination);r.make(o,m);const pr=o.startRendering();const fin=b=>{const TG={roar:.95,ooh:.75,cheer:.65,aww:.45};let m=0;for(let c=0;c<b.numberOfChannels;c++){const d=b.getChannelData(c);for(let i=0;i<d.length;i++)m=Math.max(m,Math.abs(d[i]))}const gn=(TG[k]||.6)/Math.max(m,1e-4);for(let c=0;c<b.numberOfChannels;c++){const d=b.getChannelData(c);for(let i=0;i<d.length;i++)d[i]*=gn}CR[k]=b;res(b)};if(pr&&pr.then)pr.then(fin,()=>res(null));else o.oncomplete=e=>fin(e.renderedBuffer)}catch(e){res(null)}});return RP[k]}
let PRE=0;function prerender(){if(PRE)return;PRE=1;Object.keys(RECIPES).forEach((k,i)=>setTimeout(()=>renderOne(k),i*150))}
/* gravações reais da torcida: <section data-audio-crowd / -ooh / -goal>. Carregam só quando alguém começa a jogar.
   Se o caminho do atributo falhar (ex.: teste abrindo o arquivo direto no computador), tenta a pasta audio/ ao lado da página. */
const AUD={},AFAIL={};let FL=0,UDT=0;
function loadFiles(){if(FL)return;FL=1;const a=ac(),map={crowd:root.dataset.audioCrowd,ooh:root.dataset.audioOoh,goal:root.dataset.audioGoal};
 Object.entries(map).forEach(([k,u])=>{if(!u)return;const urls=[u,'audio/'+u.split('/').pop()];
  const viaEl=()=>{const el=new Audio();el.preload='auto';el.src=urls[location.protocol==='file:'?1:0];if(k==='crowd')el.loop=true;el.addEventListener('error',()=>{AFAIL[k]=1;if(k==='crowd'&&BED&&BED.pend){bedOff(true);bedOn()}},{once:true});el.addEventListener('canplaythrough',()=>{AUD[k]={el};if(k==='crowd'&&BED&&!BED.file){bedOff(true);bedOn()}},{once:true});el.load();try{el.muted=true;const pp=el.play();if(pp&&pp.then)pp.then(()=>{el.pause();el.currentTime=0;el.muted=false}).catch(()=>{el.muted=false})}catch(e){}};
  const tryFetch=i=>{if(!a||i>=urls.length||location.protocol==='file:')return viaEl();fetch(urls[i]).then(r=>{if(!r.ok)throw 0;return r.arrayBuffer()}).then(b=>new Promise((ok,no)=>a.decodeAudioData(b,ok,no))).then(buf=>{AUD[k]={buf};if(k==='crowd'&&BED&&!BED.file){bedOff(true);bedOn()}}).catch(()=>tryFetch(i+1))};
  tryFetch(0)})}
function playBuf(buf,vol=1,max=0){const a=ac();if(!a)return;const s=a.createBufferSource(),g=a.createGain(),t=a.currentTime;s.buffer=buf;g.gain.setValueAtTime(vol,t);s.connect(g).connect(a.destination);s.start(t);if(max){g.gain.setValueAtTime(vol,t+max-1);g.gain.linearRampToValueAtTime(.0001,t+max);s.stop(t+max+.05)}}
function playFile(k,vol=1,max=0){const f=AUD[k];if(!f||muted)return false;if(f.buf){playBuf(f.buf,vol,max);return true}
 const el=f.el.cloneNode();el.volume=Math.min(1,vol);el.play().catch(()=>{});if(max)setTimeout(()=>{let v=el.volume;const iv=setInterval(()=>{v-=.1;if(v<=0){el.pause();clearInterval(iv)}else el.volume=v},90)},(max-1)*1000);return true}
/* cada reação usa a gravação certa; sem gravação, cai na torcida sintetizada */
const USE={roar:['goal',1,0],cheer:['goal',.6,3.2],ooh:['ooh',1,0],aww:['ooh',.55,2.6]};
function react(k,vol=1){const a=ac();if(!a)return;loadFiles();const u=USE[k];duck();clearTimeout(UDT);UDT=setTimeout(unduck,k==='roar'?4800:2600);if(u&&playFile(u[0],u[1]*vol,u[2]))return;prerender();if(CR[k])return playBuf(CR[k],vol);renderOne(k).then(b=>{if(b)playBuf(b,vol)})}
function nz(dur,f,vol,type='bandpass',q=.8,f2,atk=.02){const a=ac();if(!a)return;const t=a.currentTime,src=a.createBufferSource(),fl=a.createBiquadFilter(),gn=a.createGain();src.buffer=noiseBuf(a);src.loop=true;fl.type=type;fl.Q.value=q;fl.frequency.setValueAtTime(f,t);if(f2)fl.frequency.exponentialRampToValueAtTime(f2,t+dur);gn.gain.setValueAtTime(.0001,t);gn.gain.linearRampToValueAtTime(vol,t+atk);gn.gain.setValueAtTime(vol,t+Math.max(atk,dur*.45));gn.gain.exponentialRampToValueAtTime(.0001,t+dur);src.connect(fl).connect(gn).connect(a.destination);src.start(t,Math.random());src.stop(t+dur+.05)}
function thump(f0,f1,dur,vol){const a=ac();if(!a)return;const t=a.currentTime,o=a.createOscillator(),gn=a.createGain();o.type='sine';o.frequency.setValueAtTime(f0,t);o.frequency.exponentialRampToValueAtTime(f1,t+dur);gn.gain.setValueAtTime(vol,t);gn.gain.exponentialRampToValueAtTime(.0001,t+dur);o.connect(gn).connect(a.destination);o.start(t);o.stop(t+dur+.02)}
const SND={
 kick:()=>{thump(150,45,.16,.55);nz(.05,2600,.25,'highpass',.7)},
 bounce:(k=1)=>{thump(115,55,.11,.45*k);thump(240,140,.05,.18*k);nz(.035,1500,.14*k,'highpass')},
 rim:(k=1)=>{sfx(760,.5,'triangle',.07*k);sfx(1210,.38,'triangle',.05*k);sfx(1890,.22,'sine',.03*k);nz(.03,3500,.08*k,'highpass')},
 board:(k=1)=>{thump(170,80,.09,.4*k);nz(.08,900,.16*k,'lowpass',.7)},
 net:(k=1)=>{nz(.5,3800,.2*k,'highpass',.6,2200,.02);thump(90,60,.08,.15*k)},
 clank:()=>{sfx(1150,.6,'triangle',.1);sfx(1730,.45,'triangle',.06);sfx(2610,.3,'sine',.035);thump(200,120,.06,.3)},
 roar:()=>react('roar',1),cheer:()=>react('cheer',.9),ooh:()=>react('ooh',1),aww:()=>react('aww',.9),
 save:()=>{thump(90,50,.12,.4);react('aww',.8)}
};
/* torcida de fundo: chiado do estádio + burburinho de vozes soltas, em estéreo */
/* fundo: gravação "antes de bater o pênalti" em loop; abaixa quando a bola sai e na reação, volta na próxima cobrança */
let BEDV=.55;
function bedOn(){const a=ac();if(!a||BED)return;loadFiles();const out=a.createGain();out.gain.value=.0001;out.gain.linearRampToValueAtTime(BEDV,a.currentTime+1.2);out.connect(a.destination);const f=AUD.crowd;
 if(!f&&root.dataset.audioCrowd&&!AFAIL.crowd){BED={out,pend:1};return}
 if(f&&f.buf){const src=a.createBufferSource();src.buffer=f.buf;src.loop=true;src.loopStart=.06;src.loopEnd=f.buf.duration-.06;src.connect(out);src.start(0,.06);BED={src,out,file:1};return}
 if(f&&f.el){const el=f.el;el.loop=true;el.volume=BEDV;el.currentTime=.06;el.play().catch(()=>{});BED={el,out,file:1};return}
 const src=a.createBufferSource();src.buffer=PB||(PB=pink(a));src.loop=true;const fl=a.createBiquadFilter(),g=a.createGain();fl.type='bandpass';fl.frequency.value=650;fl.Q.value=.6;g.gain.value=.07;src.connect(fl).connect(g).connect(out);src.start();
 BAB=setInterval(()=>{if(!BED||!AC)return;const t=AC.currentTime;for(let i=0;i<2;i++){if(Math.random()<.75){const fq=110+Math.random()*190,vk=['a','o','e','u','oh'][(Math.random()*5)|0];voice(AC,out,t+Math.random()*.1,.18+Math.random()*.45,fq,fq*(.9+Math.random()*.3),fq*(.8+Math.random()*.3),VOW[vk],.006+Math.random()*.006,Math.random()*1.8-.9)}}},90);
 BED={src,out}}
function bedLevel(v,sec=.4){if(!BED||!AC)return;if(BED.el){const el=BED.el,v0=el.volume,steps=8;let i=0;const iv=setInterval(()=>{i++;el.volume=Math.max(0,Math.min(1,v0+(v-v0)*i/steps));if(i>=steps)clearInterval(iv)},sec*1000/steps);return}const g=BED.out.gain,t=AC.currentTime;g.cancelScheduledValues(t);g.setValueAtTime(g.value,t);g.linearRampToValueAtTime(Math.max(.0001,v),t+sec)}
const duck=()=>bedLevel(BEDV*.35,.25),unduck=()=>bedLevel(BEDV,1.2);
function bedOff(fast){clearInterval(BAB);BAB=0;if(!BED||!AC)return;const b=BED;BED=null;
 if(b.el){const el=b.el;let v=el.volume;const iv=setInterval(()=>{v-=.08;if(v<=0||fast){el.pause();clearInterval(iv)}else el.volume=v},60);return}
 try{b.out.gain.cancelScheduledValues(AC.currentTime);b.out.gain.setTargetAtTime(.0001,AC.currentTime,fast?.05:.3);setTimeout(()=>{try{b.src.stop();b.out.disconnect()}catch(e){}},fast?200:1200)}catch(e){}}
function sfx(f,d=.12,type='sine',v=.07){if(muted)return;try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();if(AC.state==='suspended')AC.resume();const o=AC.createOscillator(),q=AC.createGain(),t=AC.currentTime;o.type=type;o.frequency.setValueAtTime(f,t);q.gain.setValueAtTime(v,t);q.gain.exponentialRampToValueAtTime(.0001,t+d);o.connect(q).connect(AC.destination);o.start(t);o.stop(t+d);}catch(e){}}
const buzz=p=>{if(muted)return;try{navigator.vibrate&&navigator.vibrate(p)}catch(e){}};
const win=()=>{SND.cheer();buzz([18,40,30])},lose=()=>{SND.aww();buzz(45)};

const S={score:0,left:0,flash:null};
function flash(txt,col,ok){S.flash={txt,col,t:0};live.textContent=txt;ok===true?win():ok===false?lose():0;}
function drawFlash(c){const f=S.flash;if(!f||f.t>1.3)return;const a=f.t<1?1:1-(f.t-1)/.3,sc=1+Math.max(0,.2-f.t)*1.5;c.save();c.globalAlpha=a;c.translate(W/2,PORT?H*.17:88+(UIS-1)*45);c.scale(sc,sc);c.font=`900 ${Math.round(46*Math.min(UIS,1.35))}px system-ui,sans-serif`;c.textAlign='center';c.lineJoin='round';c.lineWidth=9;c.strokeStyle='rgba(6,16,28,.9)';c.strokeText(f.txt,0,0);c.fillStyle=f.col;c.fillText(f.txt,0,0);c.restore();}
const OK='#3DDC97',BAD='#FF6B6B',GOLD='#FFC23D';

/* ---------- 1. FUTEBOL ---------- */
let GL=300,GT=150,PL=300,PR=660,SX=480,SY=470,SS=1,GCX=480,GCY=225;
function bgSoccer(){const[o,c]=mk(),s=SS,top=GT-22*s,py=top+19*s;sky(c,top);crowd(c,0,24,W,top-2,9);glow(c,40,20,160);glow(c,W-40,20,160);
 c.fillStyle='#0B1726';c.fillRect(0,top,W,19*s);c.fillStyle=GOLD;c.font=`800 ${Math.round(11*s)}px ui-monospace,Menlo,monospace`;c.textAlign='left';for(let x=12;x<W;x+=180*s)c.fillText('MYTICKETS.TOURS',x,top+14*s);
 let q=c.createLinearGradient(0,py,0,H);q.addColorStop(0,'#1d6f38');q.addColorStop(1,'#2e9e4f');c.fillStyle=q;c.fillRect(0,py,W,H-py);
 for(let i=0;i<10;i+=2){const y0=py+Math.pow(i/10,1.5)*(H-py),y1=py+Math.pow((i+1)/10,1.5)*(H-py);c.fillStyle='rgba(255,255,255,.05)';c.fillRect(0,y0,W,y1-y0);}
 const bf=Math.min(H-30,SY+40*s);c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=3;pl(c,[[0,GL],[W,GL]]);c.stroke();
 pl(c,[[PL-70*s,GL],[PL-100*s,GL+50*s],[PR+100*s,GL+50*s],[PR+70*s,GL]]);c.stroke();pl(c,[[PL-190*s,GL],[PL-290*s,bf],[PR+290*s,bf],[PR+190*s,GL]]);c.stroke();
 c.fillStyle='#fff';c.beginPath();c.ellipse(SX,SY+14*s,7*s,3*s,0,0,7);c.fill();return o;}
function sBall(c,x,y,r,rot){c.fillStyle='#fff';c.beginPath();c.arc(x,y,r,0,7);c.fill();c.fillStyle='#1b2a3a';c.beginPath();for(let i=0;i<5;i++){const a=rot+i*1.2566;c.lineTo(x+Math.cos(a)*r*.4,y+Math.sin(a)*r*.4)}c.fill();c.strokeStyle='rgba(0,0,0,.3)';c.lineWidth=1;c.beginPath();c.arc(x,y,r,0,7);c.stroke();}
const soccer={shots:5,
 lay(){SS=PORT?Math.min(W*.74,400)/360:1;GCX=W/2;PL=GCX-180*SS;PR=GCX+180*SS;GL=PORT?Math.round(H*.42):300;GT=GL-150*SS;SY=PORT?Math.round(H*.74):470;SX=GCX;GCY=(GT+GL)/2;this.D=Math.min(SY-GL,260);this.aim=250*SS*(PORT?1.25:1);this.bg=null;},
 init(){this.diff=0;this.kt=0;this.ready();},
 ready(){unduck();this.b={x:SX,y:SY,r:18*SS,st:'ready',t:0,rot:0};this.kx=GCX;this.dive=0;this.ja=0;this.dir=1;this.net=0;this.drag=null;},
 down(p){if(this.b.st==='ready'&&p.y>GL)this.drag={x0:p.x,y0:p.y,x:p.x,y:p.y};},
 move(p){if(this.drag){this.drag.x=p.x;this.drag.y=p.y}},
 up(){const d=this.drag,s=SS;this.drag=null;if(!d)return;const dx=d.x-d.x0,dy=d.y-d.y0;if(dy>-25)return;
  const len=Math.hypot(dx,dy),D=this.D;this.pow=clamp(len/(.9*D+40),.6,1.7);this.tx=SX+clamp(dx/-dy,-1.5,1.5)*this.aim;this.ty=Math.min(GL-8*s,GL-(len-.27*D)*150*s/(1.22*D));
  const k=this.diff,err=Math.max(30,120-k*15)*s;this.gx=clamp(this.tx+rand(-err,err),PL-10*s,PR+10*s);
  this.react=Math.max(.12,.27-k*.025);this.spd=(170+k*35)*s;const need=Math.abs(this.gx-this.kx);
  this.dir=Math.sign(this.gx-this.kx)||1;this.needDive=need>55*s;this.jump=!this.needDive&&this.ty<GL-100*s;
  this.b.st='fly';this.b.t=0;S.left--;hud();bedLevel(BEDV*.7,.3);SND.kick();buzz(12);},
 update(dt){const b=this.b,s=SS;this.kt+=dt;
  if(b.st==='ready'){this.kx=GCX+(Math.sin(this.kt*1.7)*55+Math.sin(this.kt*.63)*28)*s;return}
  if(b.st==='fly'){b.t+=dt;const e=Math.min(b.t/.55,1);b.x=lerp(SX,this.tx,e);b.y=lerp(SY,this.ty,e)-Math.sin(Math.PI*e)*25*s;b.r=lerp(18,9,e)*s;b.rot+=dt*14;
   if(b.t>this.react){const st=this.spd*dt;this.kx+=clamp(this.gx-this.kx,-st,st);if(this.needDive)this.dive=Math.min(1,this.dive+dt*3.2);if(this.jump)this.ja=Math.min(1,this.ja+dt*4)}
   if(e>=1)this.resolve();return}
  if(b.st==='ingoal'){b.t+=dt;const q=this.g3,G=600*s,top=150*s-9*s;q.vh-=G*dt;q.h+=q.vh*dt;q.u+=q.vu*dt;q.d+=q.vd*dt;
   if(q.h<=0){q.h=0;if(q.vh<-50*s){q.vh=-q.vh*.35;if(q.d>.05&&!q.thud){q.thud=1}}else q.vh=0}
   if(q.d>0&&q.h>top){q.h=top;q.vh=-Math.abs(q.vh)*.3}
   if(q.d>=1){q.d=1;const imp=q.vd;if(imp>0){q.vd=-imp*q.e;q.vu*=.45;q.vh*=.4;if(!q.hit){q.hit=1;const bp=this.proj(q.u,q.h,1);this.net=clamp(imp/2.3,.6,1.25);this.nx=bp[0];this.ny=bp[1];SND.net(clamp(imp/2.3,.5,1.2))}}}
   if(q.d>0){const mL=PL+10*s,mR=PR-10*s;if(q.u<mL){q.u=mL;q.vu=Math.abs(q.vu)*.3}if(q.u>mR){q.u=mR;q.vu=-Math.abs(q.vu)*.3}}
   if(q.h===0){const f=Math.pow(.3,dt);q.vd*=f;q.vu*=f}
   if(q.d<-1.3){q.d=-1.3;q.vd=0}
   const p=this.proj(q.u,q.h,q.d),g0=this.proj(q.u,0,q.d);b.x=p[0];b.y=p[1];b.r=p[2];b.sy=g0[1];b.rot+=(Math.abs(q.vd)*4+Math.abs(q.vu)*.02)*dt;
   this.net=Math.max(0,this.net-dt*1.1);if(b.t>2.2){S.left>0?this.ready():finish()}return}
  b.t+=dt;b.x+=b.vx*dt;b.y+=b.vy*dt;b.vy+=b.g*dt;b.r=clamp(b.r+b.dr*s*dt,5*s,24*s);b.rot+=dt*8;this.net=Math.max(0,this.net-dt*1.4);
  if(b.t>1.2){S.left>0?this.ready():finish()}},
 resolve(){const b=this.b,s=SS,tx=this.tx,ty=this.ty,hw=(28+58*this.dive)*s,top=this.jump?GL-(118+38*this.ja)*s:GL-(118-40*this.dive)*s;let r;
  if(ty<GT-10*s)r='high';else if(Math.abs(tx-PL)<13*s||Math.abs(tx-PR)<13*s||(Math.abs(ty-GT)<11*s&&tx>PL&&tx<PR))r='post';else if(tx<PL||tx>PR)r='wide';else if(Math.abs(tx-this.kx)<hw&&ty>top)r='save';else r='goal';
  b.st='after';b.t=0;b.res=r;
  if(r==='goal'){S.score++;this.diff++;b.st='ingoal';const sp=this.pow;this.g3={u:tx,h:Math.max(0,GL-ty-9*s),d:0,vu:(tx-SX)*.25,vh:-20*s,vd:2.3*sp,e:sp>1.2?.55:sp>.95?.3:.15,hit:0};b.sy=GL;flash(g.r.goal,OK,null);SND.roar();buzz([30,50,30,50,60])}
  else if(r==='post'){Object.assign(b,{vx:(tx-GCX)*.9,vy:240*s,g:500*s,dr:22});flash(g.r.post,GOLD,null);SND.clank();setTimeout(SND.ooh,120);buzz([60,30,20])}
  else if(r==='save'){Object.assign(b,{vx:(tx-this.kx)*4+rand(-60,60)*s,vy:-160*s,g:900*s,dr:6});flash(g.r.save,BAD,null);SND.save();buzz(45)}
  else{Object.assign(b,{vx:(tx-SX)*.5,vy:-140*s,g:0,dr:-8});const near=r==='high'?ty>GT-45*s:Math.min(Math.abs(tx-PL),Math.abs(tx-PR))<45*s;flash(r==='high'?g.r.high:g.r.wide,BAD,null);near?SND.ooh():SND.aww();buzz(45)}hud();},
 proj(u,h,d){const s=SS,bx0=PL+24*s,bx1=PR-24*s,bt=GT+16*s,bb=GL-16*s,r0=9*s;
  if(d>=0){const k=d,sx=lerp(1,(bx1-bx0)/(PR-PL),k),hs=lerp(1,(bb-bt)/(GL-GT),k);return[GCX+(u-GCX)*sx,lerp(GL,bb,k)-h*hs,r0*lerp(1,.86,k)]}
  const k=-d;return[GCX+(u-GCX)*(1+k*.12),GL+k*55*s-h*(1+k*.1),r0*(1+k*.18)]},
 netDraw(c){const s=SS,bx0=PL+24*s,bx1=PR-24*s,bt=GT+16*s,bb=GL-16*s,n=this.net,nx=this.nx,ny=this.ny,K=2600*s*s;
  const B=(x,y)=>{if(n<=0)return[x,y];const dx=x-nx,dy=y-ny,k=n*Math.exp(-(dx*dx+dy*dy)/K)*Math.abs(Math.sin(n*9));return[x+(GCX-x)*.2*k,y+(GCY-y)*.2*k-6*s*k]};
  c.fillStyle='rgba(0,0,0,.2)';c.fillRect(PL,GT,PR-PL,GL-GT);c.strokeStyle='rgba(255,255,255,.5)';c.lineWidth=1;
  for(let i=0;i<=18;i++){c.beginPath();for(let j=0;j<=9;j++){const p=B(lerp(bx0,bx1,i/18),lerp(bt,bb,j/9));j?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}c.stroke()}
  for(let j=0;j<=9;j++){c.beginPath();for(let i=0;i<=18;i++){const p=B(lerp(bx0,bx1,i/18),lerp(bt,bb,j/9));i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}c.stroke()}
  c.beginPath();for(let k=0;k<=6;k++){const a=lerp(GT,GL,k/6),b2=lerp(bt,bb,k/6);c.moveTo(PL,a);c.lineTo(bx0,b2);c.moveTo(PR,a);c.lineTo(bx1,b2)}for(let k=0;k<=12;k++){c.moveTo(lerp(PL,PR,k/12),GT);c.lineTo(lerp(bx0,bx1,k/12),bt)}c.stroke();},
 keeper(c){c.save();c.translate(this.kx,GL-38*this.ja*SS);c.rotate(this.dir*this.dive*1.15);c.scale(SS,SS);
  c.fillStyle='rgba(0,0,0,.25)';c.beginPath();c.ellipse(0,2,26,5,0,0,7);c.fill();
  c.fillStyle='#16263a';c.fillRect(-14,-40,11,40);c.fillRect(3,-40,11,40);
  c.strokeStyle='#B8F23D';c.lineWidth=9;c.lineCap='round';c.beginPath();c.moveTo(-15,-78);c.lineTo(-32,-112);c.moveTo(15,-78);c.lineTo(32,-112);c.stroke();
  c.fillStyle='#B8F23D';c.beginPath();c.roundRect?c.roundRect(-20,-86,40,50,8):c.rect(-20,-86,40,50);c.fill();
  c.fillStyle='#0B1726';c.font='800 16px system-ui';c.textAlign='center';c.fillText('1',0,-56);
  c.fillStyle='#f4f7fb';c.beginPath();c.arc(-33,-116,8,0,7);c.arc(33,-116,8,0,7);c.fill();
  c.fillStyle='#c98d5f';c.beginPath();c.arc(0,-99,11,0,7);c.fill();c.restore();},
 draw(c){const b=this.b,s=SS;if(!this.bg)this.bg=bgSoccer();c.drawImage(this.bg,0,0,W,H);this.netDraw(c);
  const behind=b.st==='ingoal'&&this.g3.d>0;const shadowBall=()=>{c.fillStyle='rgba(0,0,0,.28)';c.beginPath();c.ellipse(b.x,b.sy+b.r*.2,b.r*1.05,b.r*.3,0,0,7);c.fill();sBall(c,b.x,b.y,b.r,b.rot)};if(behind)shadowBall();
  this.keeper(c);
  c.lineCap='butt';c.strokeStyle='rgba(0,0,0,.25)';c.lineWidth=8*s;pl(c,[[PL+4*s,GL],[PL+4*s,GT+4*s],[PR+4*s,GT+4*s],[PR+4*s,GL]]);c.stroke();
  c.strokeStyle='#f4f7fb';pl(c,[[PL,GL],[PL,GT],[PR,GT],[PR,GL]]);c.stroke();
  if(b.st==='ingoal'&&!behind)shadowBall();
  if(!behind&&b.st!=='ingoal'){if(b.st!=='after'){const e=b.st==='fly'?Math.min(b.t/.55,1):0;c.fillStyle='rgba(0,0,0,.3)';c.beginPath();c.ellipse(b.x,lerp(SY+16*s,GL,e),b.r,b.r*.3,0,0,7);c.fill()}sBall(c,b.x,b.y,b.r,b.rot)}
  if(this.drag){const d=this.drag;dashed(c,SX,SY,SX+(d.x-d.x0)*1.4,SY+(d.y-d.y0)*1.4)}
  else if(b.st==='ready'&&S.left===this.shots)label(c,'↑ '+g.drag,SX,SY+58*s+8*UIS,13,'center');}
};

/* ---------- 2. BASQUETE ---------- */
let RIM={l:734,r:800,y:250,cx:767,hw:33},BD={x:806,w:10,t:150,b:282},FLOOR=492;const BR=17,GRAV=1400;
function bgBasket(){const[o,c]=mk();let q=c.createLinearGradient(0,0,0,FLOOR);q.addColorStop(0,'#050d18');q.addColorStop(1,'#132c49');c.fillStyle=q;c.fillRect(0,0,W,FLOOR);
 const cb=Math.min(FLOOR,RIM.y+80);crowd(c,0,60,W,cb,10);c.fillStyle='rgba(5,13,24,.55)';c.fillRect(0,cb,W,FLOOR-cb);glow(c,W/2,0,260);
 const bw=Math.min(300,W-60),bx=(W-bw)/2,by=PORT?90:14;c.fillStyle='#0B1726';c.fillRect(bx,by,bw,40);c.strokeStyle=GOLD;c.lineWidth=2;c.strokeRect(bx,by,bw,40);c.fillStyle=GOLD;c.font='800 16px ui-monospace,Menlo,monospace';c.textAlign='center';c.fillText('MYTICKETS.TOURS · NYC',W/2,by+26);
 q=c.createLinearGradient(0,FLOOR,0,H);q.addColorStop(0,'#d39556');q.addColorStop(1,'#a8692f');c.fillStyle=q;c.fillRect(0,FLOOR,W,H-FLOOR);
 c.strokeStyle='rgba(90,50,20,.35)';c.lineWidth=1;for(let y=FLOOR+8;y<H;y+=10){c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.stroke()}
 c.fillStyle='rgba(30,70,140,.55)';c.fillRect(RIM.l-102,FLOOR,W,H-FLOOR);c.fillStyle='#fff';c.fillRect(0,FLOOR,W,3);
 const px=W-45;c.fillStyle='#22364f';c.fillRect(px-35,FLOOR-46,70,46);c.strokeStyle='#30496a';c.lineWidth=14;c.beginPath();c.moveTo(px,FLOOR-40);c.lineTo(px,RIM.y+50);c.lineTo(BD.x+36,RIM.y-25);c.stroke();
 c.fillStyle='rgba(240,246,252,.9)';pl(c,[[BD.x,BD.t],[BD.x+36,BD.t-12],[BD.x+36,BD.b-12],[BD.x,BD.b]],1);c.fill();c.strokeStyle='#fff';c.lineWidth=3;c.stroke();
 c.strokeStyle='#e0572a';c.lineWidth=3;pl(c,[[BD.x+2,RIM.y-36],[BD.x+18,RIM.y-41],[BD.x+18,RIM.y-3],[BD.x+2,RIM.y+2]],1);c.stroke();return o;}
function bBall(c,x,y,r,rot){c.fillStyle='#e8752a';c.beginPath();c.arc(x,y,r,0,7);c.fill();c.save();c.translate(x,y);c.rotate(rot);c.strokeStyle='#5a2a0e';c.lineWidth=1.6;c.beginPath();c.moveTo(-r,0);c.lineTo(r,0);c.moveTo(0,-r);c.lineTo(0,r);c.stroke();c.beginPath();c.arc(-r*1.15,0,r*.8,-.9,.9);c.stroke();c.beginPath();c.arc(r*1.15,0,r*.8,Math.PI-.9,Math.PI+.9);c.stroke();c.restore();}
const basket={shots:8,
 lay(){FLOOR=PORT?Math.round(H*.86):H-48;const r=W-160;RIM={l:r-66,r,cx:r-33,hw:33,y:FLOOR-242};BD={x:r+6,w:10,t:RIM.y-100,b:RIM.y+32};this.x0=PORT?Math.max(30,RIM.l-330):RIM.l-610;this.x1=PORT?RIM.l-110:RIM.l-310;this.bg=null;},
 init(){this.ready();},
 ready(){this.b={x:rand(this.x0,this.x1),y:FLOOR-rand(37,87),vx:0,vy:0,st:'ready',t:0,rot:0,touch:false,board:false,scored:false,ts:0};this.drag=null;this.sw=0;this.clk=0;},
 down(p){if(this.b.st==='ready')this.drag={x0:p.x,y0:p.y,x:p.x,y:p.y}},
 move(p){if(this.drag){this.drag.x=p.x;this.drag.y=p.y}},
 vel(){const d=this.drag;let vx=(d.x0-d.x)*5,vy=(d.y0-d.y)*5;const m=Math.hypot(vx,vy);if(m>1250){vx*=1250/m;vy*=1250/m}return[vx,vy]},
 up(){if(!this.drag)return;const[vx,vy]=this.vel();this.drag=null;if(Math.hypot(vx,vy)<160)return;Object.assign(this.b,{vx,vy,st:'fly',t:0});S.left--;hud();sfx(180,.06,'triangle',.05);buzz(12)},
 update(dt){const b=this.b;this.sw=Math.max(0,this.sw-dt*1.8);this.clk-=dt;if(b.st!=='fly')return;b.t+=dt;
  const n=5,h=dt/n;for(let i=0;i<n;i++){const py=b.y;b.vy+=GRAV*h;b.x+=b.vx*h;b.y+=b.vy*h;b.rot+=b.vx*h/BR;
   for(const rx of[RIM.l,RIM.r]){const dx=b.x-rx,dy=b.y-RIM.y,d=Math.hypot(dx,dy),m=BR+2;if(d<m&&d>0){const nx=dx/d,ny=dy/d;b.x=rx+nx*m;b.y=RIM.y+ny*m;const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=1.55*vn*nx;b.vy-=1.55*vn*ny;b.vx*=.93;b.vy*=.93}b.touch=true;if(this.clk<=0){SND.rim(clamp(Math.abs(vn)/600,.35,1.2));buzz(10);this.clk=.1}}}
   const cx=clamp(b.x,BD.x,BD.x+BD.w),cy=clamp(b.y,BD.t,BD.b),dx=b.x-cx,dy=b.y-cy,d=Math.hypot(dx,dy);
   if(d<BR){if(d===0){b.x=BD.x-BR;b.vx=-Math.abs(b.vx)*.7}else{const nx=dx/d,ny=dy/d;b.x=cx+nx*BR;b.y=cy+ny*BR;const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=1.65*vn*nx;b.vy-=1.65*vn*ny}}b.board=true;if(this.clk<=0){const k=clamp(Math.abs(b.vx)/700,.35,1.2);SND.board(k);buzz(12);this.clk=.1}}
   if(b.y>FLOOR-BR){b.y=FLOOR-BR;if(b.vy>90)SND.bounce(clamp(b.vy/650,.25,1.2));if(b.vy>0)b.vy*=-.55;b.vx*=.85}
   if(!b.scored&&py<RIM.y&&b.y>=RIM.y&&b.vy>0&&b.x>RIM.l+3&&b.x<RIM.r-3){b.scored=true;b.ts=b.t;const sw=!b.touch&&!b.board;S.score+=sw?3:2;this.sw=1;b.vx*=.35;b.vy*=.55;flash(sw?g.r.swish:g.r.bank,OK,null);SND.net();sw?SND.roar():SND.cheer();buzz([18,40,30]);hud()}}
  if(b.t>3.4||b.x>W+60||b.x<-60||(b.scored&&b.t-b.ts>1.1)){if(!b.scored){flash(g.r.miss,BAD,null);b.touch?SND.ooh():SND.aww();buzz(45)}b.st='done';setTimeout(()=>{if(cur!==basket||!run)return;S.left>0?this.ready():finish()},b.scored?150:700)}},
 netDraw(c){const s=this.sw,sway=Math.sin(s*30)*s*5,by=RIM.y+48-s*12;c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=1.3;c.beginPath();
  for(let i=0;i<=10;i++){const a=Math.PI*i/10;c.moveTo(RIM.cx-Math.cos(a)*RIM.hw,RIM.y+Math.sin(a)*6);c.lineTo(RIM.cx-Math.cos(a)*RIM.hw*.6+sway,by+Math.sin(a)*4)}
  for(let k=1;k<=3;k++){const t=k/4;for(let i=0;i<10;i++){const a=Math.PI*i/10,a2=Math.PI*(i+1)/10;c.moveTo(lerp(RIM.cx-Math.cos(a)*RIM.hw,RIM.cx-Math.cos(a2)*RIM.hw*.6+sway,t),lerp(RIM.y,by,t));c.lineTo(lerp(RIM.cx-Math.cos(a2)*RIM.hw,RIM.cx-Math.cos(a)*RIM.hw*.6+sway,t+.25),lerp(RIM.y,by,t+.25))}}c.stroke();},
 draw(c){const b=this.b;if(!this.bg)this.bg=bgBasket();c.drawImage(this.bg,0,0,W,H);
  c.strokeStyle='#d9481c';c.lineWidth=4;c.beginPath();c.ellipse(RIM.cx,RIM.y,RIM.hw,6,0,Math.PI,2*Math.PI);c.stroke();this.netDraw(c);
  if(b.st==='ready'){c.strokeStyle='rgba(255,255,255,.7)';c.lineWidth=2;c.beginPath();c.ellipse(b.x,FLOOR+10,22,5,0,0,7);c.stroke()}
  const sh=clamp(1-(FLOOR-b.y)/700,.2,1);c.fillStyle='rgba(0,0,0,.25)';c.beginPath();c.ellipse(b.x,FLOOR+4,BR*sh*1.2,4*sh,0,0,7);c.fill();
  if(this.drag){const[vx,vy]=this.vel(),d=this.drag;c.strokeStyle='rgba(255,255,255,.35)';c.lineWidth=2;c.beginPath();c.moveTo(b.x,b.y);c.lineTo(b.x-(d.x0-d.x),b.y-(d.y0-d.y));c.stroke();
   c.fillStyle=GOLD;for(let k=1;k<=6;k++){const t=k*.035;c.globalAlpha=1-k*.13;c.beginPath();c.arc(b.x+vx*t,b.y+vy*t+.5*GRAV*t*t,4,0,7);c.fill()}c.globalAlpha=1;
   const pw=Math.hypot(vx,vy)/1250;c.strokeStyle=GOLD;c.lineWidth=4;c.beginPath();c.arc(b.x,b.y,BR+8,-Math.PI/2,-Math.PI/2+pw*Math.PI*2);c.stroke()}
  bBall(c,b.x,b.y,BR,b.rot);
  c.strokeStyle='#e0572a';c.lineWidth=4;c.beginPath();c.ellipse(RIM.cx,RIM.y,RIM.hw,6,0,0,Math.PI);c.stroke();c.lineWidth=5;c.beginPath();c.moveTo(RIM.r,RIM.y);c.lineTo(BD.x,RIM.y-2);c.stroke();
  if(b.st==='ready'&&!this.drag&&S.left===this.shots)label(c,'← '+g.drag,b.x+20*UIS,b.y-34*UIS,13,'center');}
};

/* ---------- 3. FUTEBOL AMERICANO (field goal, trave em Y) ---------- */
let FGc={f:900,hz:150,ch:1.2,back:4};
const P=(x,y,z)=>{const s=FGc.f/(z+FGc.back);return[W/2+x*s,FGc.hz+(FGc.ch-y)*s,s]};
const HW=2.82,BAR=3.05;
function bgFG(zP){const[o,c]=mk(),hz=FGc.hz;sky(c,hz);crowd(c,0,40,W,hz-6,8);glow(c,60,30,150);glow(c,W-60,30,150);
 c.fillStyle='#0B1726';c.fillRect(0,hz-10,W,10);c.fillStyle='#1b5e33';c.fillRect(0,hz,W,H-hz);
 for(let z=-4,i=0;z<160;z+=4.57,i++){const y0=P(0,0,z)[1],y1=P(0,0,z+4.57)[1];c.fillStyle=i%2?'#237a42':'#2a8a4b';c.fillRect(0,y1,W,y0-y1+1)}
 const zE=zP-9.14,e0=P(0,0,zE)[1],e1=P(0,0,zP)[1];c.fillStyle='rgba(11,23,38,.45)';c.fillRect(0,e1,W,e0-e1);
 c.save();const em=P(0,0,zE+4.57);c.translate(em[0],em[1]);c.scale(1,.28);c.font=`900 ${Math.round(em[2]*1.4)}px system-ui`;c.textAlign='center';c.fillStyle='rgba(255,194,61,.55)';c.fillText('MYTICKETS',0,em[2]*.45);c.restore();
 c.strokeStyle='rgba(255,255,255,.8)';c.lineWidth=2;for(let z=zP;z>-4;z-=4.57){const a=P(-26.8,0,z),b=P(26.8,0,z);c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.stroke()}
 for(const sx of[-26.8,26.8]){const a=P(sx,0,-3.5),b=P(sx,0,zP);c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.stroke()}
 const bz=P(0,0,zP)[1];c.fillStyle='#0f3a22';c.fillRect(0,hz,W,bz-hz);return o;}
const fg={shots:6,dist:[18,23,28,33,39,45],
 lay(){FGc=PORT?{f:1250,hz:Math.round(H*.3),ch:1.5,back:4}:{f:900,hz:150,ch:1.2,back:4};this.bg=null;},
 init(){this.i=0;this.ready();},
 ready(){this.zP=this.dist[Math.min(this.i,5)];this.wind=rand(-1,1)*(.5+this.i*.28);this.bg=null;this.b={x:0,y:0,z:0,vx:0,vy:0,vz:0,st:'ready',t:0,spin:0};this.drag=null;},
 down(p){if(this.b.st==='ready'&&p.y>FGc.hz+40)this.drag={x0:p.x,y0:p.y,x:p.x,y:p.y}},
 move(p){if(this.drag){this.drag.x=p.x;this.drag.y=p.y}},
 up(){const d=this.drag;this.drag=null;if(!d)return;const dx=d.x-d.x0,dy=d.y-d.y0;if(dy>-25)return;
  const v=clamp(Math.hypot(dx,dy)*.085,8,33),yaw=clamp(dx/-dy,-1,1)*.3,el=.68,b=this.b;
  Object.assign(b,{vx:v*Math.cos(el)*Math.sin(yaw),vz:v*Math.cos(el)*Math.cos(yaw),vy:v*Math.sin(el),st:'fly',t:0,res:null});S.left--;this.i++;hud();SND.kick();buzz(15)},
 update(dt){const b=this.b;if(b.st==='ready'||b.st==='done')return;b.t+=dt;
  for(let k=0;k<3;k++){const h=dt/3,pz=b.z,px=b.x,py=b.y;b.vx+=this.wind*h;b.vy-=9.8*h;b.x+=b.vx*h;b.y+=b.vy*h;b.z+=b.vz*h;b.spin+=h*9;
   if(!b.res&&pz<this.zP&&b.z>=this.zP){const t=(this.zP-pz)/(b.z-pz),xc=lerp(px,b.x,t),yc=lerp(py,b.y,t),ax=Math.abs(xc);
    if(yc<BAR-.1){if(yc>2.72&&ax<HW){b.res='bar';b.vz*=-.3;b.vy*=.3;b.z=this.zP-.05}else b.res='short'}
    else if(Math.abs(ax-HW)<.2&&yc<10){b.res='fpost';b.vz*=-.25;b.vx=-Math.sign(xc)*2;b.z=this.zP-.05}
    else b.res=ax<HW?'good':'fwide';this.say(b.res)}
   if(b.y<0){b.y=0;b.vy=-b.vy*.3;b.vz*=.5;b.vx*=.5;if(!b.res){b.res='short';this.say('short')}}}
  if(b.t>3.2){b.st='done';setTimeout(()=>{if(cur!==fg||!run)return;S.left>0?this.ready():finish()},300)}},
 say(r){if(r==='good'){const pts=3+(this.zP>=33?1:0)+(this.zP>=39?1:0);S.score+=pts;flash(g.r.good+pts,OK,null);SND.roar();buzz([30,50,30]);hud()}else if(r==='bar'||r==='fpost'){flash(g.r[r],GOLD,null);SND.clank();setTimeout(SND.ooh,120);buzz([60,30,20])}else flash(g.r[r],BAD,false)},
 post(c){const z=this.zP;c.strokeStyle='#ffd23f';c.lineCap='round';const seg=(a,b,w)=>{c.lineWidth=Math.max(2,w*a[2]);c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.stroke()};
  const b0=P(0,0,z+1.8),b1=P(0,2.6,z+1.8),gq=P(0,3.05,z),cq=P(0,3.2,z+1.5);seg(b0,b1,.2);c.beginPath();c.moveTo(b1[0],b1[1]);c.quadraticCurveTo(cq[0],cq[1],gq[0],gq[1]);c.stroke();
  seg(P(-HW,BAR,z),P(HW,BAR,z),.14);seg(P(-HW,BAR,z),P(-HW,10,z),.12);seg(P(HW,BAR,z),P(HW,10,z),.12);
  c.fillStyle='#0B1726';const pd=P(0,1.6,z+1.8);c.fillRect(pd[0]-.3*pd[2],pd[1],.6*pd[2],b0[1]-pd[1]);
  for(const sx of[-HW,HW]){const t=P(sx,10,z);c.strokeStyle='#ff6b3d';c.lineWidth=2;c.beginPath();c.moveTo(t[0],t[1]);c.lineTo(t[0]+this.wind*6,t[1]+6);c.stroke();c.strokeStyle='#ffd23f'}},
 ball(c){const b=this.b,p=P(b.x,b.y,b.z),sh=P(b.x,0,b.z);c.fillStyle='rgba(0,0,0,.3)';c.beginPath();c.ellipse(sh[0],sh[1],Math.max(2,.2*sh[2]),Math.max(1,.05*sh[2]),0,0,7);c.fill();
  const rx=Math.max(2.5,.11*p[2]),ry=Math.max(3,(.11+.075*Math.abs(Math.cos(b.spin)))*p[2]);c.save();c.translate(p[0],p[1]-ry*.6);c.fillStyle='#7a3f1c';c.beginPath();c.ellipse(0,0,rx,ry,0,0,7);c.fill();
  if(rx>5){c.strokeStyle='#fff';c.lineWidth=Math.max(1,rx*.12);c.beginPath();c.moveTo(0,-ry*.35*Math.sign(Math.cos(b.spin)));c.lineTo(0,ry*.35*Math.sign(Math.cos(b.spin)));c.stroke()}c.restore();},
 draw(c){const b=this.b;if(!this.bg)this.bg=bgFG(this.zP);c.drawImage(this.bg,0,0,W,H);
  if(b.st==='ready'){const t=P(0,0,0);c.fillStyle='#ff6b3d';pl(c,[[t[0]-14,t[1]],[t[0]+14,t[1]],[t[0],t[1]-12]],1);c.fill()}
  const front=b.z<this.zP;if(!front)this.ball(c);this.post(c);if(front)this.ball(c);
  const wkm=Math.round(Math.abs(this.wind)*9),wtxt=L==='en'?`${Math.round(wkm*.62)} mph`:`${wkm} km/h`,arr=this.wind<-.05?'←':this.wind>.05?'→':'·',by=H-16*UIS;
  label(c,`${g.wind} ${arr} ${wtxt}`,16,by,13);label(c,L==='en'?`${Math.round(this.zP*1.094)} yd`:`${this.zP} m`,W-16,by,13,'right');
  if(this.drag){const d=this.drag,t=P(0,0,0);dashed(c,t[0],t[1]-10,t[0]+(d.x-d.x0)*1.2,t[1]-10+(d.y-d.y0)*1.2)}
  else if(b.st==='ready'&&S.left===this.shots){const t=P(0,0,0);label(c,'↑ '+g.drag,t[0],t[1]-40*UIS,13,'center')}}
};

/* ---------- 4. TÊNIS / SOFTBALL (alvo móvel) ---------- */
const RINGS=[[70,10,'#f4f7fb'],[52,25,'#2f6fd6'],[34,50,'#FFC23D'],[16,100,'#ff4d4d']],DUR=30;
function bgTennis(far){const[o,c]=mk(),cx=W/2,fh=W*.156,nh=W*.469,fs=W*.115,ns=W*.26;sky(c,far);crowd(c,0,20,W,far-10,9);glow(c,80,10,170);glow(c,W-80,10,170);
 c.fillStyle='#1d4f8f';c.fillRect(0,far-10,W,H-far+10);c.fillStyle='#2f6fd6';pl(c,[[cx-fh,far],[cx+fh,far],[cx+nh,H],[cx-nh,H]],1);c.fill();
 c.strokeStyle='#fff';c.lineWidth=3;c.stroke();pl(c,[[cx-fs,far],[cx-ns,H]]);c.stroke();pl(c,[[cx+fs,far],[cx+ns,H]]);c.stroke();
 const Y=f=>far+(H-far)*f,sx=f=>[lerp(cx-fs,cx-ns,f),lerp(cx+fs,cx+ns,f)];
 let y=Y(.147),a=sx(.147);pl(c,[[a[0],y],[a[1],y]]);c.stroke();pl(c,[[cx,y],[cx,Y(.676)]]);c.stroke();y=Y(.676);a=sx(.676);pl(c,[[a[0],y],[a[1],y]]);c.stroke();
 const ny=Y(.29),nf=.29,e0=lerp(cx-fh,cx-nh,nf),e1=lerp(cx+fh,cx+nh,nf);c.fillStyle='rgba(10,20,30,.55)';c.fillRect(e0-20,ny,e1-e0+40,28);c.fillStyle='#fff';c.fillRect(e0-20,ny-2,e1-e0+40,4);c.fillStyle='#0B1726';c.fillRect(e0-26,ny-6,8,36);c.fillRect(e1+18,ny-6,8,36);return o;}
const tennis={shots:0,
 lay(){this.far=PORT?Math.round(H*.42):200;this.cy0=PORT?Math.round(H*.28):190;this.ay=PORT?Math.min(170,H*.15):90;this.bg=null;},
 init(){this.t=0;this.balls=[];this.marks=[];this.combo=0;this.ph=rand(0,6);this.mx=-99;this.ended=false;},
 pos(t){const k=1+t/DUR*.9,ax=Math.min(290,W/2-85);return[W/2+ax*Math.sin(t*1.05*k+this.ph),this.cy0+this.ay*Math.sin(t*1.65*k+this.ph*2)]},
 down(p){if(this.t>=DUR||this.balls.length>=3)return;this.balls.push({x:p.x,y:p.y,t:0});thump(260,120,.06,.25);nz(.04,3000,.1,'highpass');buzz(8)},
 move(p,ty){if(ty==='mouse'){this.mx=p.x;this.my=p.y}},up(){},
 update(dt){this.t=Math.min(DUR,this.t+dt);
  for(const b of this.balls){b.t+=dt;if(b.t>=.34&&!b.done){b.done=true;const[cx,cy]=this.pos(this.t),d=Math.hypot(b.x-cx,b.y-cy);let pts=0;for(const r of RINGS)if(d<r[0])pts=r[1];
    if(pts){this.combo=pts>=50?this.combo+1:0;const m=Math.min(1+Math.floor(this.combo/2),4),add=pts*m;S.score+=add;this.marks.push({dx:b.x-cx,dy:b.y-cy,t:0});flash(`+${add}${m>1?' ×'+m:''}`,pts>=50?OK:GOLD,null);thump(200,90,.08,.4);pts===100?SND.roar():pts>=50?SND.cheer():sfx(420,.08,'triangle',.05);buzz(pts>=50?[18,40,30]:15)}
    else{this.combo=0;flash(g.r.miss,BAD,false)}}}
  this.balls=this.balls.filter(b=>b.t<.5);this.marks.forEach(m=>m.t+=dt);this.marks=this.marks.filter(m=>m.t<1.2);
  hud();if(this.t>=DUR&&!this.balls.length&&!this.ended){this.ended=true;setTimeout(()=>{if(cur===tennis&&run)finish()},500)}},
 draw(c){if(!this.bg)this.bg=bgTennis(this.far);c.drawImage(this.bg,0,0,W,H);const[cx,cy]=this.pos(this.t);
  c.fillStyle='rgba(0,0,0,.25)';c.beginPath();c.ellipse(cx,this.far+50+(cy-this.cy0)*.15,50,9,0,0,7);c.fill();
  for(const r of RINGS){c.fillStyle=r[2];c.beginPath();c.arc(cx,cy,r[0],0,7);c.fill();c.strokeStyle='rgba(11,23,38,.6)';c.lineWidth=2;c.stroke()}
  c.fillStyle='#0B1726';c.font='800 10px ui-monospace,Menlo,monospace';c.textAlign='center';c.fillText('10',cx,cy-58);c.fillText('25',cx,cy-40);c.fillText('50',cx,cy-22);
  for(const m of this.marks){c.globalAlpha=1-m.t/1.2;c.fillStyle='#0B1726';c.beginPath();c.arc(cx+m.dx,cy+m.dy,5,0,7);c.fill()}c.globalAlpha=1;
  for(const b of this.balls){const e=Math.min(b.t/.34,1),x=lerp(W/2,b.x,e),y=lerp(H+20,b.y,e)-Math.sin(Math.PI*e)*60,r=lerp(16,7,e);
   c.fillStyle='#d7f33a';c.beginPath();c.arc(x,y,r,0,7);c.fill();c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=1.5;c.beginPath();c.arc(x-r*.9,y,r*.75,-1,1);c.stroke();c.beginPath();c.arc(x+r*.9,y,r*.75,Math.PI-1,Math.PI+1);c.stroke()}
  if(this.mx>0){c.strokeStyle='rgba(255,255,255,.8)';c.lineWidth=2;c.beginPath();c.arc(this.mx,this.my,12,0,7);c.moveTo(this.mx-18,this.my);c.lineTo(this.mx+18,this.my);c.moveTo(this.mx,this.my-18);c.lineTo(this.mx,this.my+18);c.stroke()}
  if(this.combo>=2)label(c,`COMBO ×${Math.min(1+Math.floor(this.combo/2),4)}`,W-16,H-16*UIS,13,'right');
  if(this.t<2.5&&!this.balls.length)label(c,g.tap,W/2,H-30*UIS,13,'center');}
};

/* ---------- controle, tela cheia e modo app ---------- */
const GAMES={soccer,basket,fg,tennis};
let key='soccer',cur=soccer,run=false,raf=0,last=0,vis=false,built=false,app=false,pushed=false,ph=null,fsOn=false;
KEYS.forEach(k=>GAMES[k].lay());
const best=k=>{try{return+localStorage.getItem('mta-best-'+k)||0}catch(e){return 0}};
const wantsApp=()=>matchMedia('(pointer:coarse)').matches||innerWidth<760;
function hud(){h1.textContent=`${g.score}: ${S.score}`;h2.textContent=key==='tennis'?`${g.time}: ${Math.ceil(DUR-tennis.t)}s`:`${g.left}: ${S.left}`;}
function render(){ctx.setTransform(DPR,0,0,DPR,0,0);cur.draw(ctx);drawFlash(ctx);}
function loop(ts){raf=0;if(!run||!(vis||app))return;const dt=Math.min((ts-last)/1000||0,.033);last=ts;cur.update(dt);if(S.flash)S.flash.t+=dt;render();raf=requestAnimationFrame(loop);}
function kick(){if(!raf&&run&&(vis||app)&&!document.hidden){last=performance.now();raf=requestAnimationFrame(loop)}}
function relayout(){let nw=960,nh=540,port=false,sc;
 if(app){const cs=getComputedStyle(stage),cw=stage.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight),ch=stage.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom);
  port=ch>cw*1.05;if(port){nw=540;nh=Math.round(clamp(540*ch/cw,760,1240))}else{nh=540;nw=Math.round(clamp(540*cw/ch,820,1240))}
  sc=Math.min(cw/nw,ch/nh);cv.style.width=Math.floor(nw*sc)+'px';cv.style.height=Math.floor(nh*sc)+'px'}
 else{cv.style.width=cv.style.height='';sc=(cv.getBoundingClientRect().width||960)/960}
 stage.classList.toggle('mta-port',app&&port);
 const u=clamp(1.05/(sc||1),1,1.8),changed=nw!==W||nh!==H||port!==PORT;
 if(changed||Math.abs(u-UIS)>.02){W=nw;H=nh;PORT=port;UIS=u;sizeCanvas();KEYS.forEach(k=>GAMES[k].lay());if(run){if(cur.b&&cur.b.st==='ready')cur.ready()}else if(built){cur.init();S.left=cur.shots}}
 if(built)render();}
function lockScroll(on){const de=document.documentElement,b=document.body;if(on){de.dataset.mtaOv=de.style.overflow||'';b.dataset.mtaOv=b.style.overflow||'';de.style.overflow=b.style.overflow='hidden'}else{de.style.overflow=de.dataset.mtaOv||'';b.style.overflow=b.dataset.mtaOv||''}}
function openApp(){if(app)return;app=true;ph=document.createComment('mta');stage.before(ph);document.body.appendChild(stage);stage.classList.add('mta-app');lockScroll(true);
 const rq=stage.requestFullscreen||stage.webkitRequestFullscreen;if(rq){try{const p=rq.call(stage,{navigationUI:'hide'});if(p&&p.catch)p.catch(()=>{})}catch(e){}}
 try{history.pushState({mta:1},'');pushed=true}catch(e){}
 relayout();kick();}
function closeApp(fromPop){if(!app)return;app=false;run=false;bedOff();stage.classList.remove('mta-app','mta-port','mta-run');if(ph){ph.replaceWith(stage);ph=null}lockScroll(false);
 try{const fe=document.fullscreenElement||document.webkitFullscreenElement,ex=document.exitFullscreen||document.webkitExitFullscreen;if(fe&&ex){const p=ex.call(document);if(p&&p.catch)p.catch(()=>{})}}catch(e){}
 if(pushed&&!fromPop){pushed=false;try{history.back()}catch(e){}}pushed=false;relayout();select(key);}
function fmtScore(k,s){return k==='soccer'?`${s}/5 ${g.goals}`:`${s} pts`}
function overlay(mode){const e=EV[key];let mid,btn=g.play;
 if(mode==='start'){mid=`<span class="mta-how">${g.how[key]}</span><p class="mta-hint">${g.hint[key]}</p>`}
 else{const prev=best(key),nb=S.score>prev;if(nb){try{localStorage.setItem('mta-best-'+key,S.score)}catch(x){}}
  mid=`<div class="mta-res"><div><em>${g.score}</em>${fmtScore(key,S.score)}</div><div><em>${g.best}</em>${fmtScore(key,Math.max(prev,S.score))}</div></div><span class="mta-rec">${nb?g.newb:g.over}</span>`;btn=g.again}
 const sw=`<div class="mta-sw"><span>${g.others}</span>${KEYS.map(k=>`<button type="button" data-k="${k}" class="${k===key?'on':''}" aria-label="${g.tabs[k]}" title="${g.tabs[k]}">${EV[k].e}</button>`).join('')}</div>`;
 ov.innerHTML=`<div class="mta-pass"><div class="mta-pm"><span class="mta-emo" aria-hidden="true">${e.e}</span><small>${g.boarding} · ${g.gate} ${e.g}</small><div class="mta-route"><b>${e.from}</b><i>✈</i><b>${e.to}</b></div><strong class="mta-ev">${e.n[L]}</strong><span class="mta-meta">${e.v[L]} · ${fdate(e.d)}</span>${mid}${sw}</div>
 <div class="mta-stub"><button type="button" class="mta-btn mta-play">${btn}</button><a class="mta-btn mta-tix" href="${tixURL(key)}" rel="sponsored noopener">${g.tix}</a><a class="mta-btn mta-guide" href="${guideURL(key)}">${g.guide}</a></div></div>`;
 ov.hidden=false;ov.querySelector('.mta-play').onclick=start;ov.querySelectorAll('.mta-sw button').forEach(b=>b.onclick=()=>select(b.dataset.k));
 ov.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{if(app)closeApp()}));}
function start(){BEDV=cur===soccer?.55:.38;loadFiles();if(!app&&wantsApp())openApp();S.score=0;S.flash=null;cur.init();S.left=cur.shots;run=true;stage.classList.add('mta-run');ov.hidden=true;hud();kick();bedOn();}
function finish(){run=false;bedOff();stage.classList.remove('mta-run');render();overlay('end');}
function select(k){run=false;bedOff();stage.classList.remove('mta-run');key=k;cur=GAMES[k];gates.forEach(b=>b.setAttribute('aria-selected',String(b.dataset.k===k)));S.score=0;S.flash=null;cur.init();S.left=cur.shots;h1.textContent=h2.textContent='';render();overlay('start');}
const gw=root.querySelector('.mta-gates');
const gates=KEYS.map(k=>{const e=EV[k],b=document.createElement('button');b.type='button';b.className='mta-gate';b.dataset.k=k;b.setAttribute('role','tab');
 b.innerHTML=`<span class="mta-ball" aria-hidden="true">${e.e}</span><span class="mta-gt"><small>${g.gate} ${e.g} · ${e.from} → ${e.to}</small><b>${g.tabs[k]}</b><span>${fdate(e.d)}</span></span>`;b.onclick=()=>{mountTo(null);select(k)};gw.appendChild(b);return b});
/* toque e mouse: a área inteira do jogo recebe o gesto, então o dedo pode sair do canvas */
const pt=e=>{const r=cv.getBoundingClientRect();return{x:(e.clientX-r.left)*W/r.width,y:(e.clientY-r.top)*H/r.height}};
const skip=e=>e.target.closest&&e.target.closest('.mta-ov,.mta-x');
stage.addEventListener('pointerdown',e=>{if(!run||skip(e))return;if(!app&&e.target!==cv)return;try{stage.setPointerCapture(e.pointerId)}catch(x){}cur.down(pt(e));e.preventDefault()});
stage.addEventListener('pointermove',e=>{if(run)cur.move(pt(e),e.pointerType)});
stage.addEventListener('pointerup',e=>{if(run)cur.up(pt(e))});
stage.addEventListener('pointercancel',()=>{if(run&&cur.drag)cur.drag=null});
stage.addEventListener('touchmove',e=>{if((app||run)&&!(e.target.closest&&e.target.closest('.mta-pass')))e.preventDefault()},{passive:false});
stage.addEventListener('gesturestart',e=>e.preventDefault());
stage.addEventListener('contextmenu',e=>{if(app||run)e.preventDefault()});
xb.onclick=()=>closeApp();
fsb.onclick=()=>openApp();
addEventListener('keydown',e=>{if(e.key==='Escape'&&app)closeApp()});
addEventListener('popstate',()=>{if(app){pushed=false;closeApp(true)}});
['fullscreenchange','webkitfullscreenchange'].forEach(ev=>document.addEventListener(ev,()=>{const fe=document.fullscreenElement||document.webkitFullscreenElement;if(fe)fsOn=true;else if(fsOn){fsOn=false;if(app)closeApp()}setTimeout(relayout,80)}));
let rz=0;const onR=()=>{cancelAnimationFrame(rz);rz=requestAnimationFrame(relayout)};
addEventListener('resize',onR);addEventListener('orientationchange',()=>setTimeout(relayout,300));if(window.visualViewport)visualViewport.addEventListener('resize',onR);
/* MTArena.play("soccer") abre um jogo por código, se precisar */
/* ---------- quadros de jogo ao lado dos eventos ---------- */
const homeMark=document.createComment('mta-home');stage.before(homeMark);
const away=document.createElement('div');away.className='mta-away';away.innerHTML=`<button type="button">${g.here}</button>`;away.querySelector('button').onclick=()=>{mountTo(null);select(key)};
let mount=null;
function mountTo(slot){if(app||mount===slot)return;if(mount)mount.classList.remove('on');
 if(slot){if(!mount)homeMark.after(away);slot.appendChild(stage);slot.classList.add('on');stage.classList.add('mta-in-slot')}
 else{away.remove();homeMark.after(stage);stage.classList.remove('mta-in-slot')}
 mount=slot;relayout()}
function preview(slot){const k=slot.dataset.game,G=GAMES[k];if(!G||app||W!==960||H!==540)return;const c=slot.querySelector('canvas'),w=Math.max(240,c.clientWidth||480);c.width=Math.round(w*DPR);c.height=Math.round(w*9/16*DPR);
 const x=c.getContext('2d');x.setTransform(c.width/960,0,0,c.height/540,0,0);const keep=UIS;UIS=1;if(!(cur===G&&built))G.init();G.draw(x);UIS=keep;slot.dataset.drawn='1'}
function slotEvent(slot,k){const d=slot.dataset;if(!d.slug)return;const ymd=(d.data||'').split('-').map(Number),r=(d.rota||'').split('→').map(x=>x.trim());
 EV[k]=Object.assign({},EV[k],{slug:d.slug,n:{[L]:d.titulo||EV[k].n[L]},v:{[L]:d.local||EV[k].v[L]},d:ymd.length===3?ymd:EV[k].d,from:r[0]||EV[k].from,to:r[1]||EV[k].to,g:d.portao||EV[k].g})}
function playSlot(slot){const k=slot.dataset.game;if(!GAMES[k])return;slotEvent(slot,k);ensureBuilt();if(wantsApp()){openApp();select(k);start()}else{mountTo(slot);select(k);start()}}
const slots=[...document.querySelectorAll('.mta-slot')].filter(sl=>GAMES[sl.dataset.game]);
const sio=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting&&!en.target.dataset.drawn)preview(en.target)}),{rootMargin:'300px'});
slots.forEach(sl=>{const k=sl.dataset.game;sl.innerHTML=`<button type="button" class="mta-prev" aria-label="${g.play} ${g.tabs[k]}"><canvas></canvas><span class="mta-pk">${g.mini[k]}</span><span class="mta-pb"><b>${g.play}</b><i>${g.how[k]}</i></span></button>`;sl.querySelector('.mta-prev').onclick=()=>playSlot(sl);sio.observe(sl)});
function ensureBuilt(){if(!built){built=true;select('soccer');relayout()}}
function playGate(k){if(!GAMES[k])return;ensureBuilt();if(wantsApp()){openApp();select(k)}else{select(k);root.scrollIntoView({behavior:'smooth',block:'center'});setTimeout(()=>{const b=ov.querySelector('.mta-play');if(b)b.focus({preventScroll:true})},500)}}
document.addEventListener('click',e=>{const t=e.target.closest&&e.target.closest('[data-mta-play]');if(!t)return;e.preventDefault();playGate(t.dataset.mtaPlay)});
window.MTArena={play:playGate};
/* só monta e anima quando a seção está visível */
const io=new IntersectionObserver(es=>{vis=es[0].isIntersecting;if(vis&&!built&&root.dataset.view!=='slots'){built=true;select('soccer');relayout()}kick()},{rootMargin:'200px'});io.observe(stage);
document.addEventListener('visibilitychange',()=>{if(document.hidden)bedOff();else if(run)bedOn();kick()});
})();
