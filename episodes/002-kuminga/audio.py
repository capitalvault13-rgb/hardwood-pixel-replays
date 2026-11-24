import numpy as np, wave, os
SR=48000; D=15.0; N=int(SR*D); out=np.zeros(N)
rng=np.random.default_rng(3)
def sq(f,dur,duty=0.5):
    t=np.arange(int(SR*dur))/SR; return np.where((t*f)%1<duty,1.0,-1.0)
def env(n,a=0.005,r=0.08):
    e=np.ones(n); na=int(a*SR); nr=min(int(r*SR),n)
    if na: e[:na]=np.linspace(0,1,na)
    e[-nr:]*=np.linspace(1,0,nr); return e
def add(sig,t,g):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def lp(x,a): 
    y=np.zeros_like(x); s=0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
note=lambda m:440*2**((m-69)/12)
# music bed: 120 bpm, bass + arp in A minor, tension until the make, brighter after
bpm=120; beat=60/bpm; step=beat/2
prog=[(45,[57,60,64]),(41,[53,57,60]),(43,[55,59,62]),(40,[52,56,59])]
t=0.0; k=0
while t<D-0.3:
    bar=int(t/(beat*4))%4; root,ch=prog[bar]
    if t>=6.5: root+=0  # keep
    g=0.16 if t<12.2 else 0.09
    if k%2==0: s=sq(note(root),step*0.9,0.5); add(s*env(len(s),0.003,0.05),t,g*0.9)
    m=ch[k%3]+12+(12 if (t>=6.5 and k%4==3) else 0)
    s=sq(note(m),step*0.6,0.25); add(s*env(len(s),0.002,0.06),t,g*0.45)
    t+=step; k+=1
# hi-hat ticks
t=0
while t<D-0.2:
    n=rng.standard_normal(int(0.03*SR)); n=n-lp(n,0.3); add(n*env(len(n),0.001,0.025),t,0.05); t+=step
# rebound thud 0.75
s=np.sin(2*np.pi*np.cumsum(np.linspace(140,60,int(0.18*SR)))/SR); add(s*env(len(s),0.002,0.15),0.72,0.5)
# caption blips
for tc in [0.05,2.8,6.5,9.2,9.85,12.2]:
    s=np.concatenate([sq(note(84),0.05,0.5),sq(note(91),0.07,0.5)]); add(s*env(len(s),0.002,0.03),tc,0.12)
# release whoosh 3.5
n=rng.standard_normal(int(0.7*SR)); n=lp(n,0.08)*np.sin(np.linspace(0,np.pi,len(n))); add(n,3.45,0.9)
# buzzer 4.4
t_=np.arange(int(0.9*SR))/SR; b=((t_*180)%1*2-1)+0.5*((t_*361)%1*2-1); add(np.tanh(2*b)*env(len(b),0.01,0.08),4.4,0.18)
# swish + crowd at 6.5
n=rng.standard_normal(int(0.35*SR)); sw=n-lp(n,0.2); add(sw*env(len(sw),0.003,0.3),6.48,0.35)
n=rng.standard_normal(int(4.2*SR)); cr=lp(n,0.05); e=np.minimum(1,np.arange(len(cr))/(0.25*SR))*np.exp(-np.arange(len(cr))/SR/1.6)
add(cr*e,6.5,2.2)
# score chime
for i,m in enumerate([72,76,79,84]):
    s=sq(note(m),0.09,0.5); add(s*env(len(s),0.002,0.05),6.55+i*0.07,0.14)
# count ticks 10.0-11.2 (11 steps, 63 -> 74 ft)
for i in range(11):
    s=sq(note(76+i),0.04,0.5); add(s*env(len(s),0.002,0.02),10.0+i*1.2/11,0.1)
# arena murmur under the court shots (cut with the picture at the 9.2 card)
n=rng.standard_normal(int(9.2*SR)); mb=lp(n,0.03); mb*=np.minimum(1,np.arange(len(mb))/(0.3*SR))
mb[-int(0.05*SR):]*=np.linspace(1,0,int(0.05*SR)); add(mb,0.0,0.35)
# end-card two-note sting
for i,m in enumerate([79,84]):
    s=sq(note(m),0.12,0.5); add(s*env(len(s),0.002,0.08),12.25+i*0.12,0.14)
out[-int(0.4*SR):]*=np.linspace(1,0,int(0.4*SR))
out/=np.abs(out).max()*1.12
w=wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'audio.wav'),'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
