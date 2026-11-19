/* Monochrome, self-contained teaching animations. Geometry and timing are schematic. */
(() => {
  'use strict';
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const still = /static/.test(location.search);
  const TAU = Math.PI * 2, ink='#111111', grey='#777777', faint='#DDDDDD';
  const clamp=v=>Math.max(0,Math.min(1,v));
  const ease=v=>{v=clamp(v);return v*v*(3-2*v);};
  function line(c,x,y,X,Y,color=ink,width=1.5,dash=[]){c.beginPath();c.strokeStyle=color;c.lineWidth=width;c.setLineDash(dash);c.moveTo(x,y);c.lineTo(X,Y);c.stroke();c.setLineDash([]);}
  function path(c,pts,color=ink,width=2){c.beginPath();c.strokeStyle=color;c.lineWidth=width;pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.stroke();}
  function text(c,t,x,y,size=15,color=ink,align='left',weight=500){c.fillStyle=color;c.font=`${weight} ${size}px Inter, sans-serif`;c.textAlign=align;c.textBaseline='middle';c.fillText(t,x,y);}
  function serif(c,t,x,y,size=28,color=ink,align='left'){c.fillStyle=color;c.font=`500 ${size}px 'Source Serif 4', Georgia, serif`;c.textAlign=align;c.textBaseline='middle';c.fillText(t,x,y);}
  function dot(c,x,y,r=4,fill=ink,stroke){c.beginPath();c.arc(x,y,r,0,TAU);c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=1.5;c.stroke();}}
  function arrow(c,x,y,X,Y,color=ink,width=1.4){line(c,x,y,X,Y,color,width);let a=Math.atan2(Y-y,X-x);line(c,X,Y,X-6*Math.cos(a-.45),Y-6*Math.sin(a-.45),color,width);line(c,X,Y,X-6*Math.cos(a+.45),Y-6*Math.sin(a+.45),color,width);}
  function plane(c,x,y,scale=1){c.save();c.translate(x,y);c.scale(scale,scale);c.beginPath();c.moveTo(25,0);c.lineTo(3,-4);c.lineTo(-9,-22);c.lineTo(-14,-22);c.lineTo(-9,-4);c.lineTo(-23,-2);c.lineTo(-28,-9);c.lineTo(-32,-9);c.lineTo(-29,0);c.lineTo(-32,9);c.lineTo(-28,9);c.lineTo(-23,2);c.lineTo(-9,4);c.lineTo(-14,22);c.lineTo(-9,22);c.lineTo(3,4);c.closePath();c.fillStyle=ink;c.fill();c.restore();}
  function wash(c,points,alpha=.04){c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=`rgba(0,0,0,${alpha})`;c.fill();}
  function ring(c,x,y,r,alpha=1,ry=r){c.save();c.globalAlpha=alpha;c.beginPath();c.ellipse(x,y,r,ry,0,0,TAU);c.strokeStyle=ink;c.lineWidth=1;c.stroke();c.restore();}
  function base(c,w,h,kicker,title){c.fillStyle='#FFFFFF';c.fillRect(0,0,w,h);text(c,kicker,22,24,11,grey,'left',600);if(title)serif(c,title,22,51,w<330?22:27);}
  function bracket(c,x,y,X,Y,caption){line(c,x,y,X,Y,'#999999');line(c,x,y-4,x,y+4,'#999999');line(c,X,Y-4,X,Y+4,'#999999');if(caption)text(c,caption,(x+X)/2,y+17,12,grey,'center');}
  function packet(c,x,y,X,Y,u,returning=false){let dx=X-x,dy=Y-y,len=Math.hypot(dx,dy),a=Math.atan2(dy,dx),pos=returning?1-u:u;
    c.save();c.translate(x+dx*pos,y+dy*pos);c.rotate(a);for(let i=0;i<3;i++){c.beginPath();c.globalAlpha=(1-i*.25)*Math.sin(Math.PI*clamp(u));c.strokeStyle=ink;c.lineWidth=2;c.ellipse((returning?1:-1)*i*8,0,4,8+i*3,0,-Math.PI*.5,Math.PI*.5);c.stroke();}c.restore();
  }
  function geometry(c,w,h,t){
    const q=(t%10)/10, x=145+ease(q)*100,y=142,ground=h*.68,target=[w*.68,ground+28];
    base(c,w,h,'01 / SIDE-LOOKING RADAR','A pulse out. An echo back.');
    const A=[58,ground-44],B=[w-185,ground-44],D=[190,h-95],C=[w-45,h-95];wash(c,[A,B,C,D],.025);
    for(let i=0;i<=7;i++){let u=i/7;line(c,A[0]+(B[0]-A[0])*u,A[1],D[0]+(C[0]-D[0])*u,D[1],'#E9E9E9');}
    for(let i=0;i<=4;i++){let u=i/4;line(c,A[0]+(D[0]-A[0])*u,A[1]+(D[1]-A[1])*u,B[0]+(C[0]-B[0])*u,B[1]+(C[1]-B[1])*u,'#E9E9E9');}
    arrow(c,83,y,w-90,y,'#C6C6C6',1);text(c,'Flight direction',w-90,y-19,12,grey,'right');
    wash(c,[[x,y+12],[target[0]-68,target[1]-8],[target[0]+68,target[1]+8]],.055);
    line(c,x,y+10,x,ground-7,'#BBBBBB',1,[3,6]);line(c,x,y+10,...target,'#999999',1.1);plane(c,x,y,.88);
    text(c,'Nadir',x-12,ground-12,12,grey,'right');text(c,'Slant range R',(x+target[0])/2-3,(y+target[1])/2-24,14,ink);
    let phase=(q*2)%1,going=phase<.4,receiving=phase>=.4&&phase<.8;
    if(going)packet(c,x,y+12,...target,phase/.4);if(receiving)packet(c,x,y+12,...target,(phase-.4)/.4,true);
    const hit=ease((phase-.33)/.08)*(1-ease((phase-.67)/.15));ring(c,...target,13+hit*20,.15+hit*.5,5+hit*8);dot(c,...target,5);
    text(c,'Ground target',target[0]+28,target[1]+27,13);text(c,going?'TRANSMIT':receiving?'RECEIVE':'MEASURE DELAY',w-24,91,11,grey,'right',600);
    line(c,24,h-65,w-24,h-65,'#E8E8E8');serif(c,'R = cΔt / 2',24,h-36,29);text(c,'Range from two-way travel time',w-24,h-35,13,grey,'right');
  }
  function range(c,w,h,t){
    c.save();c.scale(w/650,h/330);c.fillStyle='#FFFFFF';c.fillRect(0,0,650,330);
    const A=250,B=330,phase=(t%12)/12;
    text(c,'SIDE VIEW: RANGE FOLLOWS THE INCLINED LINE OF SIGHT',22,20,11,grey,'left',600);
    // End-on aircraft: its flight direction is perpendicular to this section.
    line(c,50,47,100,47,ink,2.5);line(c,75,26,75,44,ink,2);
    dot(c,75,47,7,'#FFFFFF',ink);dot(c,75,47,2);
    text(c,'Radar',75,73,11,grey,'center');
    text(c,'Flight into page',111,40,10,grey);
    line(c,185,85,424,85,'#CCCCCC');
    [A,B].forEach((x,i)=>{line(c,82,50,x,85,'#BBBBBB',1);dot(c,x,85,5);text(c,i?'B: farther':'A: nearer',x,103,12,ink,'center',600);});
    packet(c,82,50,B,85,(t%3)/3);
    text(c,'Slant range',450,58,12,ink);
    text(c,'Ground range',450,85,12,grey);
    function echoes(y,short){
      const sigma=short?14:44,amp=short?38:34;
      text(c,short?'SHORT PULSE':'LONG PULSE',22,y-38,12,ink,'left',600);
      text(c,'Received echoes',22,y-18,11,grey);
      [A,B].forEach(x=>line(c,x,y-50,x,y+5,'#DDDDDD',1,[2,4]));
      line(c,147,y,430,y,'#D7D7D7');let pts=[];
      for(let i=0;i<=300;i++){let x=147+i/300*283,v=Math.exp(-.5*((x-A)/sigma)**2)+Math.exp(-.5*((x-B)/sigma)**2);pts.push([x,y-v*amp]);}
      wash(c,[[147,y],...pts,[430,y]],.055);path(c,pts,ink,2.2);
      const x=147+((phase+(short?.13:0))%1)*283;
      let v=Math.exp(-.5*((x-A)/sigma)**2)+Math.exp(-.5*((x-B)/sigma)**2);dot(c,x,y-v*amp,3.5);
      text(c,short?'2 separate returns':'1 merged return',461,y-32,17,ink,'left',600);
      text(c,short?'A and B are distinguishable':'A and B blend together',461,y-10,12,grey);
      bracket(c,short?A-14:A-44,y+15,short?A+14:A+44,y+15,short?'Short echo':'Long echo');
    }
    echoes(169,false);echoes(279,true);
    c.restore();
  }
  function azimuth(c,w,h,t){
    c.save();c.scale(w/650,h/330);c.fillStyle='#FFFFFF';c.fillRect(0,0,650,330);
    const A=282,B=362,u=(t%12)/12;
    text(c,'TOP VIEW: AZIMUTH IS PARALLEL TO FLIGHT',22,20,11,grey,'left',600);
    function beam(y,narrow){
      const start=180,end=445,px=start+(end-start)*ease((u%0.5)*2),half=narrow?23:103,ground=y+75;
      text(c,narrow?'NARROW BEAM':'WIDE BEAM',22,y+5,12,ink,'left',600);
      text(c,narrow?'Smaller footprint':'Larger footprint',22,y+25,11,grey);
      arrow(c,162,y,end+12,y,'#D0D0D0');plane(c,px,y,.45);
      text(c,'Flight / azimuth',end+12,y-13,10,grey,'right');
      wash(c,[[px,y+7],[px-half,ground],[px+half,ground]],.06);
      line(c,px,y+7,px-half,ground,'#AAAAAA',1);line(c,px,y+7,px+half,ground,'#AAAAAA',1);
      line(c,165,ground,450,ground,'#CCCCCC');
      line(c,px-half,ground,px+half,ground,ink,3);
      [A,B].forEach((x,i)=>{const lit=Math.abs(x-px)<=half;dot(c,x,ground,6,lit?ink:'#FFFFFF',ink);if(lit)ring(c,x,ground,12,.4);text(c,i?'B':'A',x,ground+21,13,ink,'center',600);});
      text(c,narrow?'A, then B':'A + B together',480,y+36,17,ink,'left',600);
      text(c,narrow?'Two targets can be separated':'One broad illuminated patch',480,y+58,12,grey);
    }
    beam(65,false);beam(213,true);
    // Flight and target separation are parallel; the radar looks to the side.
    c.restore();
  }
  function compression(c,w,h,t,chirp){
    c.fillStyle='#FFFFFF';c.fillRect(0,0,w,h);
    const starts=[25,w*.356,w*.69],cw=w*.28,cy=h*.52,q=(t%11)/11;
    ['TRANSMIT','DELAYED RETURNS','MATCHED FILTER'].forEach((s,i)=>{text(c,String(i+1).padStart(2,'0'),starts[i],24,11,grey);text(c,s,starts[i]+27,24,12,ink,'left',600);line(c,starts[i],cy,starts[i]+cw,cy,'#E2E2E2');});
    function signal(x,width,centre,greyLine=false){let pts=[];for(let i=0;i<=280;i++){let u=i/280,xx=x+width*u,v=(u-centre),env=Math.abs(v)<.42?1:0,ph=TAU*(chirp?2*(v+.5)+9*(v+.5)**2:9*v);pts.push([xx,cy-Math.sin(ph-t*1.8)*env*32]);}path(c,pts,greyLine?'#AAAAAA':ink,greyLine?1.3:1.9);}
    signal(starts[0],cw,.5);signal(starts[1],cw,.39);signal(starts[1],cw,.60,true);
    let out=starts[2],a=out+cw*.39,b=out+cw*.60,sigma=cw*(chirp?.027:.14),pts=[];
    for(let i=0;i<=330;i++){let x=out+cw*i/330,v=Math.exp(-.5*((x-a)/sigma)**2)+Math.exp(-.5*((x-b)/sigma)**2);pts.push([x,cy-48*v]);}
    wash(c,[[out,cy],...pts,[out+cw,cy]],.045);path(c,pts,ink,2.4);
    [a,b].forEach(x=>{dot(c,x,cy+14,3);line(c,x,cy+23,x,cy+31,'#BBBBBB');});
    const scan=out+cw*((q*1.7)%1);line(c,scan,cy-70,scan,cy+4,'#AAAAAA',1,[2,5]);
    bracket(c,starts[0]+cw*.08,cy+48,starts[0]+cw*.92,cy+48,'Long pulse duration τ');
    text(c,'Identical target separation',starts[1]+cw*.5,h-28,13,grey,'center');serif(c,chirp?'Two distinct peaks':'One merged response',out+cw*.5,h-28,25,ink,'center');
    for(let i=0;i<2;i++){let x=starts[i]+cw+10,X=starts[i+1]-16;arrow(c,x,cy,X,cy,'#BBBBBB');let u=(q*2+i*.35)%1;dot(c,x+(X-x)*u,cy,2.5,'#777777');}
  }
  function aperture(c,w,h,t){
    c.save();c.scale(w/900,h/550);c.fillStyle='#FFFFFF';c.fillRect(0,0,900,550);
    const cycle=t%18,collect=clamp(cycle/12),focus=ease((cycle-12)/3),left=100,right=800,cx=450,flightY=91,targetY=213;
    const px=left+(right-left)*collect,dx=(px-cx)/350,doppler=-dx/Math.sqrt(dx*dx+1.2*1.2);
    text(c,'1  OBSERVE ONE FIXED TARGET THROUGHOUT THE APERTURE',24,25,12,grey,'left',600);
    text(c,'Approaching: + Doppler',left,57,13,ink);text(c,'Closest approach: 0',cx,57,13,ink,'center');text(c,'Receding: − Doppler',right,57,13,ink,'right');
    arrow(c,left-30,flightY,right+24,flightY,'#CCCCCC');text(c,'Flight / azimuth',right+24,flightY+23,12,grey,'right');
    for(let i=0;i<11;i++){const x=left+i*(right-left)/10,seen=x<=px;dot(c,x,flightY,seen?3:2,seen?ink:'#DDDDDD');if(seen)line(c,x,flightY+9,cx,targetY,'#DDDDDD',1,[3,5]);}
    line(c,cx,flightY+10,cx,targetY,'#BBBBBB',1,[3,5]);line(c,px,flightY+10,cx,targetY,ink,1.8);plane(c,px,flightY,.65);dot(c,cx,targetY,6);ring(c,cx,targetY,14,.3,7);text(c,'Fixed ground target',cx+27,targetY+2,14,ink);
    text(c,collect<.46?'Range decreases':collect>.54?'Range increases':'Minimum slant range',115,178,14,grey);
    bracket(c,left,255,right,255,'Synthetic aperture length Lsa: distance travelled while this target remains illuminated');
    text(c,'2  THE TARGET HAS A PREDICTABLE DOPPLER HISTORY',24,306,12,grey,'left',600);
    const zero=375,amp=58;
    line(c,left,zero,right,zero,'#D0D0D0');line(c,cx,zero-60,cx,zero+65,'#D0D0D0',1,[3,5]);
    text(c,'+',left-25,zero-43,16,grey,'center');text(c,'0',left-25,zero,12,grey,'center');text(c,'−',left-25,zero+43,16,grey,'center');
    let points=[];for(let i=0;i<=240;i++){let u=i/240,x=left+(right-left)*u,d=(x-cx)/350,f=-d/Math.sqrt(d*d+1.2*1.2);points.push([x,zero-f*amp]);}path(c,points,'#DDDDDD',1.5);
    path(c,points.slice(0,Math.max(2,Math.floor(collect*240)+1)),ink,2.5);dot(c,px,zero-doppler*amp,5);
    line(c,px,zero-65,px,zero+65,'#AAAAAA',1,[2,5]);text(c,'Slow time / aircraft position',right,zero+62,12,grey,'right');
    text(c,'fD = −(2 / λ) dR / dt',left,zero+62,15,ink);
    line(c,24,464,876,464,'#E5E5E5');
    text(c,'3  MATCH THE PHASE HISTORY, THEN SUM COHERENTLY',24,484,12,grey,'left',600);
    for(let i=0;i<9;i++){let x=40+i*37,y=521,a=(-7*(Math.sqrt(1+((i-4)/4)**2)-1))*(1-focus);ring(c,x,y,11,.15);arrow(c,x,y,x+11*Math.cos(a),y-11*Math.sin(a),i===4?ink:'#777777',1.5);}
    text(c,focus>.8?'Phase-corrected echoes reinforce':'Different echo phases before focusing',390,520,12,grey);
    const centre=775,baseY=544,sigma=42-35*focus;let response=[];for(let i=0;i<=120;i++){let x=680+i/120*188;response.push([x,baseY-42*Math.exp(-.5*((x-centre)/sigma)**2)]);}path(c,response,ink,2);text(c,focus>.8?'Focused target':'Azimuth response',centre,484,12,ink,'center',600);
    c.restore();
  }
  function multilook(c,w,h,t){
    c.save();c.scale(w/760,h/320);c.fillStyle='#FFFFFF';c.fillRect(0,0,760,320);
    text(c,'SPATIAL MULTILOOKING: AVERAGE LINEAR INTENSITIES',20,22,12,grey,'left',600);
    const cols=12,rows=16,cell=13,left=70,top=65;
    function val(r,col){let u=Math.sin((r+1)*91.217+(col+1)*37.389)*43758.5453;u-=Math.floor(u);return -Math.log(Math.max(.005,1-u))*(col>=6?.75:.40);}
    const tones=[];for(let r=0;r<rows;r++){tones[r]=[];for(let col=0;col<cols;col++){let intensity=val(r,col);tones[r][col]=intensity;c.fillStyle=`rgb(${255-Math.round(Math.min(1,intensity)*230)},${255-Math.round(Math.min(1,intensity)*230)},${255-Math.round(Math.min(1,intensity)*230)})`;c.fillRect(left+col*cell,top+r*cell,cell,cell);}}
    text(c,'Fine samples: speckled',left,top-16,13,ink,'left',600);text(c,'Same scene boundary',left,top+rows*cell+18,11,grey);
    const group=Math.floor(t/2)%24,gr=Math.floor(group/12),gc=group%12,bx=left+gc*cell,by=top+gr*8*cell;
    c.strokeStyle=ink;c.lineWidth=3;c.strokeRect(bx-1,by-1,cell+2,8*cell+2);
    const zoomX=315,zoomY=67,size=19;let mean=0;
    for(let r=0;r<8;r++)for(let col=0;col<1;col++){let v=tones[gr*8+r][gc+col];mean+=v;let shade=255-Math.round(Math.min(1,v)*230);c.fillStyle=`rgb(${shade},${shade},${shade})`;c.fillRect(zoomX+col*size,zoomY+r*size,size-1,size-1);}
    mean/=8;
    text(c,'Selected block',zoomX-7,zoomY-18,13,ink,'left',600);text(c,'1 range × 8 azimuth',zoomX-16,zoomY+170,12,grey);text(c,'8 intensity samples',zoomX-16,zoomY+189,12,grey);
    arrow(c,left+cols*cell+20,165,zoomX-24,165,'#999999');
    arrow(c,zoomX+size+20,165,524,165,ink);text(c,'Mean',454,143,13,ink,'center',600);
    const outX=552,outY=141,s=13;
    for(let r=0;r<2;r++)for(let col=0;col<12;col++){let sum=0;for(let a=0;a<8;a++)sum+=tones[r*8+a][col];sum/=8;let shade=255-Math.round(Math.min(1,sum)*230);c.fillStyle=`rgb(${shade},${shade},${shade})`;c.fillRect(outX+col*s,outY+r*s,s-1,s-1);}
    c.strokeStyle=ink;c.lineWidth=3;c.strokeRect(outX+gc*s-1,outY+gr*s-1,s+1,s+1);
    text(c,'Coarser output grid',outX,top-16,13,ink,'left',600);text(c,'One output pixel per block',outX-10,209,12,grey);
    const u=(t%2)/2;dot(c,390+u*133,165,4);
    line(c,280,278,734,278,'#E5E5E5');text(c,'Less speckle and steadier brightness',280,295,14,ink,'left',600);text(c,'Fine spatial detail is averaged away',280,313,12,grey);
    text(c,'Illustration, not measured data',20,309,10,grey);
    c.restore();
  }
  function ellipse(c,w,h,t){
    c.save();c.fillStyle='#FFFFFF';c.fillRect(0,0,w,h);const scale=Math.min(w/650,h/245);c.translate((w-650*scale)/2,(h-245*scale)/2);c.scale(scale,scale);
    const phase=t*1.5;
    const cases=[{name:'Linear',delta:0,amp:1,condition:'In phase: Δ = 0°'},
      {name:'Circular',delta:Math.PI/2,amp:1,condition:'Equal amplitudes, Δ = 90°'},
      {name:'Elliptical',delta:Math.PI/3,amp:.6,condition:'Unequal amplitudes, Δ = 60°'}];
    cases.forEach((mode,i)=>{
      const cx=108+i*217,cy=132,r=49;
      serif(c,mode.name,cx,23,24,ink,'center');text(c,mode.condition,cx,48,10,grey,'center');
      arrow(c,cx-65,cy,cx+67,cy,'#CCCCCC');arrow(c,cx,cy+62,cx,cy-64,'#CCCCCC');
      text(c,'H',cx+65,cy+14,11,grey,'center');text(c,'V',cx+13,cy-62,11,grey);
      const point=a=>[cx+r*Math.cos(a),cy-r*mode.amp*Math.cos(a+mode.delta)];
      let full=[];for(let j=0;j<=180;j++)full.push(point(j/180*TAU));path(c,full,'#CFCFCF',1.2);
      // The recent field-tip trail makes the locus visible even before a full cycle.
      for(let j=55;j>0;j--){let a=phase-j*.04,b=phase-(j-1)*.04;path(c,[point(a),point(b)],`rgba(0,0,0,${.15+.65*(1-j/55)})`,2.4);}
      const [x,y]=point(phase);
      arrow(c,cx,cy,x,cy,'#999999',1.3);arrow(c,x,cy,x,y,'#999999',1.3);
      line(c,cx,y,x,y,'#BBBBBB',1,[2,4]);
      arrow(c,cx,cy,x,y,ink,2.7);dot(c,x,y,4.5);
      text(c,'E',x+(x>=cx?12:-12),y+(y<cy?-10:13),14,ink,x>=cx?'left':'right',600);
      text(c,['Straight-line locus','Circular locus','Elliptical locus'][i],cx,211,12,ink,'center',600);
    });
    text(c,'Thin arrows: H and V components. Bold arrow: resultant electric field E.',325,235,11,grey,'center');
    c.restore();
  }
  function propagation(c,w,h,t){
    c.save();c.fillStyle='#FFFFFF';c.fillRect(0,0,w,h);const scale=Math.min(w/650,h/200);c.translate((w-650*scale)/2,(h-200*scale)/2);c.scale(scale,scale);
    text(c,'THE SAME CIRCULAR WAVE, VIEWED ACROSS SPACE',20,19,11,grey,'left',600);
    const phase=t*1.5,x0=84,y0=105,length=451;
    const project=(z,a)=>[x0+z*length+38*Math.cos(a),y0+z*10-14*Math.cos(a)-46*Math.sin(a)];
    arrow(c,x0-45,y0,x0+length+40,y0+10,'#BBBBBB');
    // Each faint ellipse is one transverse plane at a fixed position z.
    for(let z of [0,.25,.5,.75,1]){let pts=[];for(let j=0;j<=90;j++)pts.push(project(z,j/90*TAU));path(c,pts,'#E1E1E1',1);}
    // E(z,t) = [cos(ωt-kz), sin(ωt-kz)]; the spatial locus is a helix.
    let points=[];for(let j=0;j<=420;j++){let z=j/420,a=phase-TAU*2.5*z;points.push(project(z,a));}
    for(let j=0;j<points.length-1;j++){let a=phase-TAU*2.5*j/420;path(c,[points[j],points[j+1]],Math.cos(a)>0?ink:'#AAAAAA',Math.cos(a)>0?2.2:1.4);}
    const [x,y]=project(0,phase);arrow(c,x0,y0,x,y,ink,2.5);dot(c,x,y,4.5);
    text(c,'Fixed position',x0,166,11,grey,'center');
    arrow(c,405,171,581,171,ink);text(c,'Propagation z',493,190,11,grey,'center');
    c.restore();
  }
  function channels(c,w,h,t){
    base(c,w,h,'QUAD-POLARIZATION','One pulse fills one matrix column');const q=(t%12)/12,isV=q>=.5,u=(q%.5)*2,y=h*.48,x0=62,tx=w*.43,rx=w*.70;
    plane(c,x0,y,.65);line(c,x0+30,y,tx-15,y,'#D0D0D0');dot(c,tx,y,7);text(c,'Target',tx,y+28,12,grey,'center');
    [y-35,y+35].forEach((Y,i)=>{arrow(c,tx+16,y,rx,Y,'#BBBBBB');text(c,i?'V receive':'H receive',rx+12,Y,12,grey);});
    if(u<.40)packet(c,x0+30,y,tx-15,y,u/.4);else if(u<.8)[y-35,y+35].forEach(Y=>packet(c,tx+16,y,rx,Y,(u-.4)/.4));
    text(c,isV?'V TRANSMIT':'H TRANSMIT',24,85,11,ink,'left',600);
    let xx=w-134,yy=h-77;[['HH','HV'],['VH','VV']].forEach((row,r)=>row.forEach((v,col)=>{let active=col===Number(isV),arrived=u>.68;c.fillStyle=active&&arrived?ink:'#F0F0F0';c.fillRect(xx+col*53,yy+r*26,47,22);text(c,v,xx+col*53+23,yy+r*26+11,11,active&&arrived?'#FFFFFF':grey,'center',600);}));
    text(c,'H pulse: HH + VH',24,h-42,12,isV?'#AAAAAA':ink);text(c,'V pulse: HV + VV',24,h-22,12,isV?ink:'#AAAAAA');
  }
  // Canvas has no HTML subscript support: lay out base glyphs and lowered suffixes explicitly.
  function mathLabel(c,parts,x,y,size=14,color=ink,align='left'){
    const font=n=>`500 ${n}px 'Source Serif 4', Georgia, serif`;
    const runs=parts.flatMap(part=>Array.isArray(part)?[{text:part[0],sub:false},{text:part[1],sub:true}]:[{text:part,sub:false}]);
    let width=0;for(const run of runs){c.font=font(run.sub?size*.7:size);run.width=c.measureText(run.text).width;width+=run.width;}
    let cursor=x-(align==='center'?width/2:align==='right'?width:0);
    c.save();c.fillStyle=color;c.textAlign='left';c.textBaseline='alphabetic';
    for(const run of runs){c.font=font(run.sub?size*.7:size);c.fillText(run.text,cursor,y+size*.3+(run.sub?size*.25:0));cursor+=run.width;}
    c.restore();
  }
  function calibrationChain(c,w,h,t,mode='amplitude'){
    c.save();const scale=Math.min(w/900,h/510);c.fillStyle='#FFFFFF';c.fillRect(0,0,w,h);c.translate((w-900*scale)/2,(h-510*scale)/2);c.scale(scale,scale);
    const stage=({amplitude:0,phase:1,crosstalk:2})[mode] ?? 0,phase=t*2.8;
    const names=['Amplitude imbalance','Phase imbalance','Cross-talk between H and V'];
    text(c,'H / V TRANSMIT–RECEIVE CHAINS',24,22,12,grey,'left',600);serif(c,names[stage],24,53,29);
    text(c,stage===2?'H-only reference input':stage===1?'Same target response; unequal electrical paths':'Equal, in-phase reference inputs',875,52,12,grey,'right');
    const H=122,V=292,rxX=83,rxW=146,switchX=651,antX=807,couple=473;
    const hardwareFront=[];
    function block(x,y,width,height,title,fill='#FFFFFF',stroke=ink){
      const draw=()=>{c.fillStyle=fill;c.fillRect(x,y,width,height);c.strokeStyle=stroke;c.lineWidth=1.4;c.strokeRect(x,y,width,height);text(c,title,x+width/2,y+height/2,15,fill===ink?'#FFFFFF':ink,'center',500);};
      hardwareFront.push(draw);draw();
    }
    function selector(x,y){c.fillStyle='#FFFFFF';c.fillRect(x,y,26,26);c.strokeStyle='#999999';c.lineWidth=1.3;c.strokeRect(x,y,26,26);line(c,x+3,y+23,x+23,y+3,'#999999');}
    function circulator(y,color=ink){dot(c,couple,y,10,'#FFFFFF',color);c.beginPath();c.arc(couple,y,5,.2,Math.PI*1.55);c.strokeStyle=color;c.lineWidth=1.2;c.stroke();}

    // Desired receive paths run from the antenna at right toward each receiver.
    [H,V].forEach((y,i)=>{
      const active=stage!==2||i===0,color=active?ink:'#BBBBBB';
      arrow(c,rxX,y,38,y,color,1.5);block(rxX,y-24,rxW,48,i?'V receiver':'H receiver');
      arrow(c,switchX,y,rxX+rxW,y,color,1.6);line(c,switchX+86,y,antX-15,y,color,1.6);
      block(switchX,y-19,86,38,'T/R switch');
      c.beginPath();c.ellipse(antX,y,15,34,0,0,TAU);c.strokeStyle=color;c.lineWidth=2;c.stroke();line(c,antX+4,y-28,antX+4,y+28,color,1);
      text(c,i?'V antenna':'H antenna',antX+28,y,13,grey);
      circulator(y,color);
      text(c,i?(stage===0?'Lower gain; same phase':stage===1?'Same gain; extra phase delay':''):'Reference gain and phase',rxX+rxW/2,y-42,12,grey,'center');
      if(active&&stage!==1){let u=(t*.26+i*.16)%1;dot(c,635-u*390,y,i===1&&stage===0?3:5,color);}
    });
    // Fig. 4-10: the selector feeds the two circulators, not a parasitic H/V link.
    block(284,188,133,42,'Transmitter','#F1F1F1','#999999');arrow(c,417,209,460,209,'#999999');
    selector(460,196);
    arrow(c,473,196,473,H+10,'#999999');arrow(c,473,222,473,V-10,'#999999');
    text(c,'Pol. switch',431,244,11,grey,'center');
    // Intentional common-tone reference feed through a splitter and the T/R switches.
    block(735,190,131,37,'Cal. reference','#FFFFFF','#AAAAAA');
    arrow(c,735,209,664,209,'#999999');selector(638,196);
    arrow(c,651,196,651,H+19,'#999999');arrow(c,651,222,651,V-19,'#999999');
    text(c,'Splitter',679,235,11,grey);text(c,'Known common tone',800,246,11,grey,'center');
    // The labels are phase-path contributions, not separate cross-talk coefficients.
    mathLabel(c,[['R','h']],335,H-17,14,grey,'center');mathLabel(c,[['R','v']],335,stage===1?V-18:V+20,14,grey,'center');
    mathLabel(c,[['A','h']],765,H-27,14,grey,'center');mathLabel(c,[['A','v']],765,V+28,14,grey,'center');
    mathLabel(c,[['T','h']],494,162,14,grey);mathLabel(c,[['T','v']],494,256,14,grey);
    mathLabel(c,[['C','h']],670,164,14,grey);mathLabel(c,[['C','v']],670,253,14,grey);
    if(stage===1){
      // Example differential RECEIVE path: V includes an explicit extra cable length.
      // This detour illustrates the mechanism; Fig. 4-10 does not specify which path is longer.
      c.strokeStyle='#FFFFFF';c.lineWidth=6;c.beginPath();c.moveTo(307,V);c.lineTo(363,V);c.stroke();
      line(c,310,V,360,V,'#BBBBBB',1,[3,4]);
      const hReceive=[[couple,H],[rxX+rxW,H]];
      const vReceive=[[couple,V],[360,V],[360,V+28],[310,V+28],[310,V],[rxX+rxW,V]];
      path(c,vReceive,ink,1.8);
      mathLabel(c,['Illustrative extra length ',['Δℓ','V']],335,V+49,12,ink,'center');
      const s=t%12,step=s<2?0:s<4?1:s<6?2:3;
      const descriptions=['1  Transmit path T','2  Antenna path A: outward','3  Antenna path A: return','4  Receive path R: compare arrival'];
      text(c,descriptions[step],875,79,12,ink,'right',600);
      function length(points){return points.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-points[i][0],p[1]-points[i][1]),0);}
      function moving(points,distance,isV){
        const total=length(points);let remaining=Math.max(0,Math.min(total,distance));
        path(c,points,isV?'#666666':ink,2.3);
        for(let i=1;i<points.length;i++){let a=points[i-1],b=points[i],n=Math.hypot(b[0]-a[0],b[1]-a[1]);if(remaining<=n||i===points.length-1){let q=n?Math.min(remaining/n,1):0;dot(c,a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,5,isV?'#FFFFFF':ink,isV?ink:null);break;}remaining-=n;}
      }
      for(let isV of [false,true]){
        const y=isV?V:H;
        if(step===0){let points=[[417,209],[couple,209],[couple,y]];moving(points,(s/2)*length(points),isV);}
        if(step===1){let points=[[couple,y],[antX-17,y]];moving(points,((s-2)/2)*length(points),isV);}
        if(step===2){let points=[[antX-17,y],[couple,y]];moving(points,((s-4)/2)*length(points),isV);}
        if(step===3){moving(isV?vReceive:hReceive,(s-6)*80,isV);}
      }
      const hArrived=step===3&&(s-6)*80>=length(hReceive),vArrived=step===3&&(s-6)*80>=length(vReceive);
      c.canvas.dataset.phasePathStep=String(step);
      c.canvas.dataset.phaseArrival=hArrived&&!vArrived?'H first; V still travelling':vArrived?'Both received; V arrived later':'Travelling';
    }
    // This optional leakage overlay is NOT a connection shown in textbook Fig. 4-10.
    if(stage===2){
      const leakX=548;
      line(c,leakX,H,leakX,V,ink,1.8,[4,5]);arrow(c,leakX,V-18,leakX,V,ink,1.8);dot(c,leakX,H,2.5);dot(c,leakX,V,2.5);
      text(c,'Leakage',leakX+12,170,12,ink);dot(c,leakX,H+4+((t*.36)%1)*(V-H-12),3.5);
      dot(c,leakX-((t*.36+.4)%1)*(leakX-rxX-rxW),V,3.2);
    }
    // Paint components after animated wire highlights, so paths never cross component labels.
    hardwareFront.forEach(draw=>draw());selector(460,196);selector(638,196);
    circulator(H);circulator(V,stage===2?'#BBBBBB':ink);
    if(stage===1){
      const step=Number(c.canvas.dataset.phasePathStep);
      if(step===1||step===2)for(const y of [H,V]){
        const color=y===H?ink:'#666666';
        if(step===1){arrow(c,579,y,618,y,color,1.8);arrow(c,752,y,781,y,color,1.8);}
        else{arrow(c,618,y,579,y,color,1.8);arrow(c,781,y,752,y,color,1.8);}
      }
    }
    line(c,24,358,876,358,'#E5E5E5');
    text(c,stage===2?'RECEIVER OUTPUTS: H-ONLY REFERENCE':'RECEIVER OUTPUTS: EQUAL H/V REFERENCES',24,382,11,grey,'left',600);
    if(stage===2)text(c,'Only H was injected',875,382,12,ink,'right',600);
    const x0=140,length=400;
    function trace(y,amp,offset,dashed){let pts=[];for(let i=0;i<=260;i++){let u=i/260;pts.push([x0+u*length,y-amp*Math.sin(u*TAU*3-phase+offset)]);}line(c,x0,y,x0+length,y,'#DDDDDD');c.setLineDash(dashed?[4,4]:[]);path(c,pts,ink,2);c.setLineDash([]);}
    text(c,'H',99,417,15,ink,'center',600);text(c,'V',99,470,15,ink,'center',600);
    trace(417,18,0,false);trace(470,stage===0?9:stage===1?18:5,stage===1?-Math.PI/3:0,true);
    if(stage===0){text(c,'Unequal amplitudes only',593,414,16,ink,'left',600);text(c,'V is weaker; the H/V peaks stay aligned',593,439,12,grey);line(c,340,395,340,491,'#BBBBBB',1,[3,5]);}
    if(stage===1){text(c,'Same amplitude; different phase',570,413,15,ink,'left',600);text(c,c.canvas.dataset.phaseArrival==='H first; V still travelling'?'H has arrived; V is still travelling':'The V detour adds a relative delay',570,439,12,grey);mathLabel(c,[['Δφ','co'],' = ',['φ','T'],' + 2',['φ','A'],' + ',['φ','R']],570,464,15,ink);line(c,340,395,340,491,'#BBBBBB',1,[3,5]);}
    if(stage===2){text(c,'Unwanted V response',593,413,16,ink,'left',600);text(c,'Ideal V output is zero for this H-only test',593,439,12,grey);text(c,'Leakage is not real target cross-polarization',593,463,11,grey);}
    if(stage===2)text(c,'Parasitic leakage is an illustrative overlay, not a connection in Fig. 4-10.',24,500,10,grey);
    else mathLabel(c,['HH: ',['φ','Th'],' + 2',['φ','Ah'],' + ',['φ','Rh'],';    VV: ',['φ','Tv'],' + 2',['φ','Av'],' + ',['φ','Rv'],'   (A is travelled twice)'],24,500,12,grey);
    c.restore();
  }
  function faraday(c,w,h,t){
    c.save();const k=Math.min(w/760,h/300);c.translate((w-760*k)/2,(h-300*k)/2);c.scale(k,k);
    c.fillStyle='#F3F3F3';c.fillRect(0,0,760,300);
    const cycle=t%12, ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);};
    const omega=20*Math.PI/180*ease(cycle/3),angles=[0,omega,2*omega,0];
    const xs=[90,280,470,660],labels=['Launch H','After outward pass','After return pass','After correction'];
    text(c,'TWO IONOSPHERE CROSSINGS · IDEAL TRIHEDRAL',24,24,12,grey,'left',600);
    xs.forEach((x,i)=>{
      if(i<3)arrow(c,x+64,131,x+124,131,'#999',1.5);
      c.beginPath();c.arc(x,131,51,0,Math.PI*2);c.strokeStyle='#CCC';c.lineWidth=1.2;c.stroke();
      line(c,x-55,131,x+55,131,'#DDD',1);line(c,x,76,x,186,'#DDD',1);
      text(c,'H',x+59,131,11,grey);text(c,'V',x,68,11,grey);
      const a=angles[i];line(c,x-43*Math.cos(a),131-43*Math.sin(a),x+43*Math.cos(a),131+43*Math.sin(a),'#111',4);arrow(c,x,131,x+45*Math.cos(a),131+45*Math.sin(a),'#111',2.5);
      if(a>.005){c.beginPath();c.arc(x,131,32,0,a);c.strokeStyle='#777';c.lineWidth=1.7;c.stroke();}
      text(c,labels[i],x,211,13,'#111','center',600);
      text(c,Math.round(a*180/Math.PI)+'°',x,236,18,'#111','center',500);
    });
    text(c,'F(Ω)',185,109,16,grey);text(c,'F(Ω)',375,109,16,grey);text(c,'inverse on both sides',565,101,11,grey);
    text(c,'Illustrative Ω sweep: 0° → 20°; clockwise follows the matrix convention.',380,278,12,grey,'center');c.restore();
  }
  const renderers={faraday,geometry,range,azimuth,rect:(...args)=>compression(...args,false),chirp:(...args)=>compression(...args,true),aperture,multilook,ellipse,propagation,channels,calibrationChain};
  const scenes=[];
  document.querySelectorAll('[data-sar-animation]').forEach(host=>{
    const draw=renderers[host.dataset.sarAnimation];if(!draw)return;host.classList.add('sar-animation');
    const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',host.dataset.label||'Animated radar working diagram');host.appendChild(canvas);
    const parents=[];for(let el=host;el&&!el.classList.contains('slide');el=el.parentElement)if(el.hasAttribute('data-a'))parents.push(el);
    const slide=host.closest('.slide');let elapsed=0,wasVisible=false,width=0,height=0,dpr=0;
    function paint(time){let w=host.clientWidth||600,h=host.clientHeight||300,pixelRatio=Math.min(devicePixelRatio||1,2);if(w!==width||h!==height||pixelRatio!==dpr){width=w;height=h;dpr=pixelRatio;canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}const c=canvas.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.lineCap='round';c.lineJoin='round';draw(c,w,h,time,host.dataset.calibrationMode);}
    if(host.dataset.sarAnimation==='calibrationChain'){
      const controls=host.closest('.calibration-circuit-animation').querySelector('.calibration-mode-controls');
      const buttons=[...controls.querySelectorAll('[data-calibration-select]')];
      buttons.forEach(button=>{
        button.addEventListener('click',event=>{
          event.stopPropagation();host.dataset.calibrationMode=button.dataset.calibrationSelect;elapsed=0;
          buttons.forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
          canvas.setAttribute('aria-label',button.textContent+': '+({amplitude:'Unequal output amplitudes with aligned phases.',phase:'Equal output amplitudes with a relative phase delay.',crosstalk:'An H-only reference creates an unwanted V output through channel leakage.'})[host.dataset.calibrationMode]);
          paint(still||motion.matches?5.5:0);
        });
        button.addEventListener('keydown',event=>{if(event.key===' '||event.key==='Enter')event.stopPropagation();});
      });
    }
    function tick(dt){const visible=slide.classList.contains('active')&&parents.every(e=>e.classList.contains('on'));if(visible){if(!wasVisible)elapsed=0;else elapsed+=dt;paint(motion.matches?5.5:elapsed);}wasVisible=visible;}
    paint(5.5);if(!still)scenes.push(tick);document.fonts.ready.then(()=>paint(5.5));new ResizeObserver(()=>paint(still||motion.matches?5.5:elapsed)).observe(host);
  });
  let last=null;function frame(now){let dt=last===null?0:Math.min((now-last)/1000,.075);last=now;scenes.forEach(tick=>tick(dt));requestAnimationFrame(frame);}if(!still)requestAnimationFrame(frame);
})();
