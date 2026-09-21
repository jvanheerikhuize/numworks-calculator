import gc
import kandinsky as kd
import ion
import math
import random as rd
import time
mc=math.cos
ms=math.sin
mt=math.tan
mq=math.sqrt
ma=math.atan2
mp=math.pi
mr=math.radians
MAP_STR="11111111111111111000000000000001100333300022200110000040000020011000004000002001100333300000000110000000000000011000400040000001111313111300311111111111130031111111111113003111113111111300311114000000000000013000000000000001100000000000000110020000034043011005000000303001100200000000000110000000000000013000000000000001140000004004000111330033133131111113003111111111133400433333333130000000000000033000000000000003300000000000000330050005000500033000000000000003300000000000000330000000000000033333333333333333"
ROWS=32
COLS=16
BSZ=ROWS*COLS
DIR_X=(1,-1,0,0)
DIR_Y=(0,0,1,-1)
def wall_at(x,y):
    if x<0 or y<0 or y>=ROWS or x>=COLS: return 1
    return int(MAP_STR[y*COLS+x])
WC1=kd.color(150,40,40)
WC2=kd.color(40,90,150)
WC3=kd.color(150,150,40)
WC4=kd.color(40,150,70)
WC5=kd.color(150,40,150)
DWC=kd.color(120,120,120)
CC=kd.color(15,15,35)
FC=kd.color(70,60,50)
SW=320
SH=220
NR=40
CW=SW//NR
FOV=mp/3
HF=FOV/2
MST=ROWS+COLS+8
PD=(SW/2)/mt(HF)
px=1.5
py=5.5
pa=0.0
av=0.0
MS=3.0
RS=1.8
RA=9.0
ME=8
SMD=6.5
ES=1.0
ETR=0.45
ED=10
WBE=5
WEI=2
WME=16
WSS=0.5
WMI=3
WBT_T=1.5
PRT=1.2
ESD=(0,30,-30,60,-60,90,-90,120,-120)
ESZ=0.5
PMH=100
PIT=0.5
SR=10.0
SF=mr(5)
EC=kd.color(210,40,40)
EO=kd.color(90,10,10)
HBG=kd.color(10,10,14)
HT=kd.color(230,230,230)
WBT_C=kd.color(255,220,100)
HBBG=kd.color(40,15,15)
HBFG=kd.color(90,200,90)
HBLO=kd.color(200,60,40)
CHC=kd.color(255,255,255)
MFC=kd.color(255,250,210)
HFC=kd.color(255,220,80)
HFT=0.15
HH=18
CSZ=16
CX0=SW//2-CSZ//2
CX1=CX0+CSZ
CY0=SH//2-CSZ//2
CY1=CY0+CSZ
RBG=kd.color(20,20,26)
RCS=11
RPX=8
RSZ=RCS*RPX
RM=4
RX0=SW-RSZ-RM
RY0=HH+RM
RX1=RX0+RSZ
RY1=RY0+RSZ
RDBG=kd.color(14,18,14)
RDW=kd.color(90,95,60)
RDP=kd.color(255,255,255)
RDE=kd.color(230,40,40)
RDB=kd.color(70,80,70)
ROF=None
RCO=None
RSO=None
DB=None
ESO=None
BD=None
BQX=None
BQY=None
EX=None
EY=None
EA=None
vd=None
vi=None
def init_tables():
    global ROF,RCO,RSO,DB,ESO,BD,BQX,BQY,EX,EY,EA,vd,vi
    if ROF is not None: return
    gc.collect()
    ROF=bytearray(NR*4)
    RCO=bytearray(NR*4)
    RSO=bytearray(NR*4)
    _rof=[-HF+FOV*r/NR for r in range(NR)]
    _rco=[mc(o) for o in _rof]
    _rso=[ms(o) for o in _rof]
    ROF=_rof
    RCO=_rco
    RSO=_rso
    gc.collect()
    DB=[999.0]*NR
    ESO=[mr(a) for a in ESD]
    BD=bytearray(BSZ)
    BQX=bytearray(BSZ)
    BQY=bytearray(BSZ)
    EX=[0.0]*ME
    EY=[0.0]*ME
    EA=bytearray(ME)
    vd=[0.0]*ME
    vi=bytearray(ME)
    gc.collect()
score=0
ph=PMH
pi=0.0
mf=0.0
hf_x=0.0
hf_time=0.0
wave=1
wrs=0
scd=0.0
sm=1
wbt=0.0
high_score=0
ptimer=0.0
DH=0
DS=0
DMX=0
DMY=0
DSX=0
DSY=0
DCA=0.0
DSA=0.0
def reset():
    global px,py,pa,av,score,ph,pi,mf,hf_time,wave,wrs,scd,sm,wbt,ptimer
    px=1.5
    py=5.5
    pa=0.0
    av=0.0
    for i in range(ME): EA[i]=0
    score=0
    ph=PMH
    pi=0.0
    mf=0.0
    hf_time=0.0
    wave=1
    wrs=0
    scd=0.0
    sm=1
    wbt=0.0
    ptimer=0.0
def upd_hs():
    global high_score
    if score>high_score: high_score=score
def dda(x0,y0,ca,sa):
    global DH,DS,DMX,DMY,DSX,DSY,DCA,DSA
    if -1e-6<sa<1e-6: sa=1e-6
    if -1e-6<ca<1e-6: ca=1e-6
    mx=int(x0)
    my=int(y0)
    dx=abs(1/ca)
    dy=abs(1/sa)
    if ca>0:
        sx=1
        sdx=(mx+1-x0)*dx
    else:
        sx=-1
        sdx=(x0-mx)*dx
    if sa>0:
        sy=1
        sdy=(my+1-y0)*dy
    else:
        sy=-1
        sdy=(y0-my)*dy
    h=0
    s=0
    for _ in range(MST):
        if sdx<sdy:
            sdx+=dx
            mx+=sx
            s=0
        else:
            sdy+=dy
            my+=sy
            s=1
        h=wall_at(mx,my)
        if h: break
    DH=h
    DS=s
    DMX=mx
    DMY=my
    DSX=sx
    DSY=sy
    DCA=ca
    DSA=sa
def dda_d(x0,y0):
    if DS==0: return (DMX-x0+(1-DSX)/2)/DCA
    return (DMY-y0+(1-DSY)/2)/DSA
def rd_depth(x0,y0,ang):
    dda(x0,y0,mc(ang),ms(ang))
    if not DH: return 1e9
    return dda_d(x0,y0)
def wc(h):
    if h==1: return WC1
    if h==2: return WC2
    if h==3: return WC3
    if h==4: return WC4
    if h==5: return WC5
    return DWC
def db(x,y,w,h,c):
    if w>0 and h>0: kd.fr(int(x),int(y),int(w),int(h),c)
def dwh(x,y,w,h,hx,hy,hw,hh,c,f):
    if w<=0 or h<=0: return
    if x>=hx+hw or x+w<=hx or y>=hy+hh or y+h<=hy:
        f(x,y,w,h,c)
        return
    if y<hy: f(x,y,w,hy-y,c)
    if y+h>hy+hh: f(x,hy+hh,w,y+h-(hy+hh),c)
    m0=max(y,hy)
    m1=min(y+h,hy+hh)
    if m1>m0:
        if x<hx: f(x,m0,hx-x,m1-m0,c)
        if x+w>hx+hw:
            lx=max(x,hx+hw)
            f(lx,m0,x+w-lx,m1-m0,c)
def ds1(x,y,w,h,c):
    dwh(x,y,w,h,RX0,RY0,RSZ,RSZ,c,db)
def frr(x,y,w,h,c):
    dwh(x,y,w,h,CX0,CY0,CSZ,CSZ,c,ds1)
def cast():
    cp=mc(pa)
    sp=ms(pa)
    for r in range(NR):
        co=RCO[r]
        so=RSO[r]
        ca=cp*co-sp*so
        sa=sp*co+cp*so
        dda(px,py,ca,sa)
        x=r*CW
        if not DH:
            frr(x,HH,CW,SH//2-HH,CC)
            frr(x,SH//2,CW,SH-SH//2,FC)
            DB[r]=999.0
            continue
        d=dda_d(px,py)
        d*=co
        if d<0.05: d=0.05
        DB[r]=d
        ph2=PD/d
        if ph2>SH*3: ph2=SH*3
        wt=int(SH/2-ph2/2)
        wh=int(ph2)
        if wt<HH:
            wh-=HH-wt
            wt=HH
        if wt+wh>SH: wh=SH-wt
        if wh<0: wh=0
        c=wc(DH)
        wb=wt+wh
        if wt>HH: frr(x,HH,CW,wt-HH,CC)
        if wh>0: frr(x,wt,CW,wh,c)
        if wb<SH: frr(x,wb,CW,SH-wb,FC)
def is_free(x,y):
    return wall_at(int(x),int(y))==0
def move(dt):
    global px,py,pa,av
    ti=0.0
    if ion.keydown(ion.KEY_LEFT): ti-=1.0
    if ion.keydown(ion.KEY_RIGHT): ti+=1.0
    tv=ti*RS
    if av<tv: av=min(av+RA*dt,tv)
    elif av>tv: av=max(av-RA*dt,tv)
    pa+=av*dt
    pa%=(2*mp)
    dx=0.0
    dy=0.0
    if ion.keydown(ion.KEY_UP):
        dx+=mc(pa)*MS*dt
        dy+=ms(pa)*MS*dt
    if ion.keydown(ion.KEY_DOWN):
        dx-=mc(pa)*MS*dt
        dy-=ms(pa)*MS*dt
    if is_free(px+dx,py): px+=dx
    if is_free(px,py+dy): py+=dy
def has_cp(x0,y0,x1,y1):
    dx=x1-x0
    dy=y1-y0
    d=mq(dx*dx+dy*dy)
    if d<1e-6: return True
    return rd_depth(x0,y0,ma(dy,dx))>=d
def upd_ff():
    for i in range(BSZ): BD[i]=255
    cx=int(px)
    cy=int(py)
    if cx<0 or cx>=COLS or cy<0 or cy>=ROWS: return
    BD[cy*COLS+cx]=0
    BQX[0]=cx
    BQY[0]=cy
    qi=0
    ql=1
    while qi<ql:
        cx=BQX[qi]
        cy=BQY[qi]
        cur=cy*COLS+cx
        qi+=1
        for _d in range(4):
            nx=cx+DIR_X[_d]
            ny=cy+DIR_Y[_d]
            if nx<0 or nx>=COLS or ny<0 or ny>=ROWS: continue
            ni=ny*COLS+nx
            if MAP_STR[ni]!='0': continue
            if BD[ni]==255:
                BD[ni]=BD[cur]+1
                BQX[ql]=nx
                BQY[ql]=ny
                ql+=1
def spawn():
    for _ in range(20):
        cx=rd.randint(0,COLS-1)
        cy=rd.randint(0,ROWS-1)
        if MAP_STR[cy*COLS+cx]!='0': continue
        sx=cx+0.5
        sy=cy+0.5
        if (sx-px)**2+(sy-py)**2<SMD**2: continue
        if has_cp(px,py,sx,sy): continue
        for i in range(ME):
            if not EA[i]:
                EX[i]=sx
                EY[i]=sy
                EA[i]=1
                return
def start_wave():
    global wrs,scd,sm,wbt
    wrs=min(WBE+(wave-1)*WEI,WME)
    scd=0.0
    sm=2**(wave//WMI)
    wbt=WBT_T
def upd_enemies(dt):
    global ph,pi,wave,wrs,scd,ptimer
    ptimer-=dt
    if ptimer<=0:
        ptimer=PRT
        upd_ff()
    for i in range(ME):
        if not EA[i]: continue
        ex=EX[i]
        ey=EY[i]
        dx=px-ex
        dy=py-ey
        d=mq(dx*dx+dy*dy)
        if d<=ETR:
            if pi<=0:
                ph-=ED
                pi=PIT
            EA[i]=0
            continue
        bd=255
        tdx=dx
        tdy=dy
        cx=int(ex)
        cy=int(ey)
        for _d in range(4):
            nx=cx+DIR_X[_d]
            ny=cy+DIR_Y[_d]
            if nx>=0 and nx<COLS and ny>=0 and ny<ROWS:
                v=BD[ny*COLS+nx]
                if v<bd:
                    bd=v
                    tdx=nx+0.5-ex
                    tdy=ny+0.5-ey
        st=ES*dt
        ba=ma(tdy,tdx)
        for offset in ESO:
            ang=ba+offset
            nx=ex+mc(ang)*st
            ny=ey+ms(ang)*st
            if is_free(nx,ny):
                EX[i]=nx
                EY[i]=ny
                break
        else:
            if d>0.001:
                if is_free(ex+dx/d*st,ey): EX[i]+=dx/d*st
                if is_free(ex,ey+dy/d*st): EY[i]+=dy/d*st
    if wrs>0:
        al=0
        for i in range(ME):
            if EA[i]: al+=1
        if al<ME:
            scd-=dt
            if scd<=0:
                scd=WSS
                spawn()
                wrs-=1
    else:
        aa=0
        for i in range(ME):
            if EA[i]:
                aa=1
                break
        if not aa:
            wave+=1
            start_wave()
def shoot():
    global score,mf,hf_x,hf_time
    mf=0.12
    bi=-1
    bd=SR+1
    for i in range(ME):
        if not EA[i]: continue
        dx=EX[i]-px
        dy=EY[i]-py
        d=mq(dx*dx+dy*dy)
        if d<1e-4 or d>SR: continue
        at=ma(dy,dx)-pa
        at=(at+mp)%(2*mp)-mp
        if abs(at)>SF: continue
        if d<bd:
            bd=d
            bi=i
    if bi<0: return
    if rd_depth(px,py,pa)<bd: return
    dx=EX[bi]-px
    dy=EY[bi]-py
    at=ma(dy,dx)-pa
    at=(at+mp)%(2*mp)-mp
    hf_x=SW/2+mt(at)*PD
    hf_time=HFT
    score+=sm
    EA[bi]=0
def draw_en():
    vc=0
    for i in range(ME):
        if not EA[i]: continue
        dx=EX[i]-px
        dy=EY[i]-py
        d=mq(dx*dx+dy*dy)
        if d<0.2: continue
        at=ma(dy,dx)-pa
        at=(at+mp)%(2*mp)-mp
        if abs(at)>HF: continue
        dp=d*mc(at)
        if dp<0.1: continue
        vd[vc]=dp
        vi[vc]=i
        vc+=1
    for i in range(1,vc):
        d=vd[i]
        ix=vi[i]
        j=i-1
        while j>=0 and vd[j]<d:
            vd[j+1]=vd[j]
            vi[j+1]=vi[j]
            j-=1
        vd[j+1]=d
        vi[j+1]=ix
    for i in range(vc):
        ix=vi[i]
        dx=EX[ix]-px
        dy=EY[ix]-py
        at=ma(dy,dx)-pa
        at=(at+mp)%(2*mp)-mp
        sx=SW/2+mt(at)*PD
        dp=vd[i]
        sz=PD*ESZ/dp
        cl=int(sx//CW)
        if cl<0 or cl>=NR: continue
        if dp>DB[cl]-0.05: continue
        s=max(2,int(sz))
        l=int(sx-s/2)
        t=int(SH/2-s/2)
        if l<-s or l>SW or t<-s or t>SH: continue
        frr(l,t,s,s,EO)
        ins=min(max(1,s//6),(s-1)//2)
        inn=s-ins*2
        frr(l+ins,t+ins,inn,inn,EC)
def draw_hud():
    kd.fr(0,0,SW,HH,HBG)
    if wbt>0:
        kd.ds("Wave "+str(wave),4,1,WBT_C,HBG)
    else:
        t="Score "+str(score)
        if sm>1: t+=" x"+str(sm)
        kd.ds(t,4,1,HT,HBG)
    bw=70
    bh=10
    bx=SW-bw-6
    by=(HH-bh)//2
    kd.fr(bx,by,bw,bh,HBBG)
    fr=max(0,ph)/PMH
    fw=int(bw*fr)
    if fw>0:
        fc=HBFG if fr>0.3 else HBLO
        kd.fr(bx,by,fw,bh,fc)
    draw_ch()
def draw_ch():
    kd.fr(CX0,CY0,CX1-CX0,CY1-CY0,RBG)
    cx=SW//2
    cy=SH//2
    c=MFC if mf>0 else CHC
    kd.fr(cx-1,cy-7,2,4,c)
    kd.fr(cx-1,cy+3,2,4,c)
    kd.fr(cx-7,cy-1,4,2,c)
    kd.fr(cx+3,cy-1,4,2,c)
def draw_radar():
    ccx=RX0+RSZ//2
    ccy=RY0+RSZ//2
    hl=RCS//2
    cpx=int(px)
    cpy=int(py)
    for row in range(-hl-1,hl+2):
        my=cpy+row
        for col in range(-hl-1,hl+2):
            mx=cpx+col
            c=RDW if 0<=mx<COLS and 0<=my<ROWS and MAP_STR[my*COLS+mx]!='0' else RDBG
            pxv=round(ccx+(mx-px)*RPX)
            pyv=round(ccy+(my-py)*RPX)
            x0=max(pxv,RX0)
            y0=max(pyv,RY0)
            x1=min(pxv+RPX,RX1)
            y1=min(pyv+RPX,RY1)
            if x1>x0 and y1>y0:
                kd.fr(x0,y0,x1-x0,y1-y0,c)
    hs=RSZ/2
    for i in range(ME):
        if not EA[i]: continue
        rx=(EX[i]-px)*RPX
        ry=(EY[i]-py)*RPX
        if -hs<=rx<=hs and -hs<=ry<=hs:
            kd.fr(int(ccx+rx)-1,int(ccy+ry)-1,3,3,RDE)
    kd.fr(ccx-2,ccy-2,4,4,RDP)
    kd.fr(RX0,RY0,RSZ,1,RDB)
    kd.fr(RX0,RY1-1,RSZ,1,RDB)
    kd.fr(RX0,RY0,1,RSZ,RDB)
    kd.fr(RX1-1,RY0,1,RSZ,RDB)
def draw_hf():
    if hf_time<=0: return
    sx=hf_x
    ty=SH//2
    gx=SW//2
    gy=SH-4
    for s in range(1,5):
        t=s/5
        kd.fr(int(gx+(sx-gx)*t)-1,int(gy+(ty-gy)*t)-1,3,3,HFC)
    bx=int(sx)
    kd.fr(bx-5,ty-1,11,2,HFC)
    kd.fr(bx-1,ty-5,2,11,HFC)
IBG=kd.color(10,10,20)
IR=(75,40,5,40,90,40,5,40,80,40,10,10,105,40,5,40,120,40,5,40,105,40,20,5,105,55,20,5,135,40,20,5,142,40,6,40,165,40,20,5,172,40,6,40,165,75,20,5,195,40,5,40,195,40,20,5,195,57,15,5,195,75,20,5,225,40,20,5,225,40,5,20,225,57,20,5,240,60,5,20,225,75,20,5)
def intro():
    kd.fr(0,0,SW,SH,IBG)
    fc=(255,0,0)
    for i in range(0,len(IR),4):
        kd.fr(IR[i],IR[i+1],IR[i+2],IR[i+3],fc)
    kd.ds("by legendary noobs gaming, 2026",10,105,(150,150,150),IBG)
    kd.ds("Press OK to Start",85,140,(255,255,255),IBG)
    kd.ds("Press CLEAR to Menu",70,170,(150,150,150),IBG)
    while ion.keydown(ion.KEY_OK) or ion.keydown(ion.KEY_EXE): pass
    while not (ion.keydown(ion.KEY_OK) or ion.keydown(ion.KEY_EXE)): pass
GOBG=kd.color(20,6,6)
GOTX=kd.color(230,60,60)
def gameover():
    kd.fr(0,0,SW,SH,GOBG)
    tx="Game Over"
    x=SW//2-len(tx)*10//2
    kd.ds(tx,x,60,GOTX,GOBG)
    kd.ds(tx,x+1,60,GOTX,GOBG)
    kd.ds("Score: "+str(score),120,112,HT,GOBG)
    while ion.keydown(ion.KEY_OK) or ion.keydown(ion.KEY_EXE): pass
    while not (ion.keydown(ion.KEY_OK) or ion.keydown(ion.KEY_EXE)): pass
def play():
    init_tables()
    while True:
        reset()
        start_wave()
        intro()
        try: last=time.monotonic()
        except: last=None
        global mf,pi,wbt,hf_time
        pok=False
        while True:
            gc.collect()
            if ion.keydown(ion.KEY_BACKSPACE) or ion.keydown(ion.KEY_EXE):
                upd_hs()
                break
            if last is not None:
                try:
                    now=time.monotonic()
                    dt=now-last
                    last=now
                    if dt<=0 or dt>0.5: dt=0.08
                except: dt=0.08
            else: dt=0.08
            move(dt)
            ok=ion.keydown(ion.KEY_OK)
            if ok and not pok: shoot()
            pok=ok
            upd_enemies(dt)
            if mf>0:
                mf-=dt
                if mf<0: mf=0
            if pi>0:
                pi-=dt
                if pi<0: pi=0
            if hf_time>0: hf_time-=dt
            if wbt>0:
                wbt-=dt
                if wbt<0: wbt=0
            cast()
            draw_en()
            draw_hf()
            draw_hud()
            draw_radar()
            if ph<=0:
                upd_hs()
                gameover()
                break
play()