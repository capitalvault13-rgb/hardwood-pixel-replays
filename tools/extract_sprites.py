import os
from PIL import Image; import numpy as np
from scipy import ndimage
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
im=np.array(Image.open(os.path.join(ROOT,'sprites','source','hawks-chibi-v2-sheet.webp')).convert('RGB')).astype(float)
g=np.zeros(im.shape[:2])
g[:,1:]+=np.abs(np.diff(im,axis=1)).sum(2); g[1:,:]+=np.abs(np.diff(im,axis=0)).sum(2)
bg=(im.min(axis=2)>232)
rowr=[(42,223),(254,433),(465,644),(692,872),(904,1083),(1115,1294),(1341,1522),(1553,1733),(1764,1943)]
colr=[(14,138),(140,272),(291,409),(429,547),(567,685),(705,823),(842,962),(980,1098)]
names=['naw','mccollum','johnson','okongwu','ejjofor','flemings','daniels','wiggins','kuminga','dort','newell','veesaar','nembhard','hield','kispert','gilbert','landale','dennis','gueye']
kits=['home','away','statement']
def fit(r0,r1,c0,c1):
  best=None
  for p in np.arange(4.80,5.06,0.01):
    for ox in np.arange(0,p,0.5):
      xs=np.arange(c0+ox+p/2,c1,p)
      for oy in np.arange(0,p,0.5):
        ys=np.arange(r0+oy+p/2,r1,p)
        s=g[np.ix_(ys.astype(int),xs.astype(int))].mean()
        if best is None or s<best[0]: best=(s,p,ox,oy)
  return best
P=None
for ki,kit in enumerate(kits):
  for ri in range(3):
    r0,r1=rowr[ki*3+ri]
    for ci in range(8):
      n=ri*8+ci
      if n>=19: break
      c0,c1=colr[ci]; c0-=4; c1+=4; r0b=r0-6; r1b=r1+4
      s,p,ox,oy=fit(r0b,r1b,c0,c1)
      xs=np.arange(c0+ox+p/2,c1,p).astype(int); ys=np.arange(r0b+oy+p/2,r1b,p).astype(int)
      a=np.zeros((len(ys),len(xs),4),np.uint8)
      for j,yy in enumerate(ys):
        for i,xx in enumerate(xs):
          a[j,i,:3]=np.median(im[yy-1:yy+2,xx-1:xx+2].reshape(-1,3),axis=0); a[j,i,3]=255
      wh=a[:,:,:3].min(2)>228
      lab,_=ndimage.label(wh)
      edge=set(lab[0])|set(lab[-1])|set(lab[:,0])|set(lab[:,-1]); edge.discard(0)
      a[np.isin(lab,list(edge)),3]=0
      lab2,nl=ndimage.label(a[:,:,3]>0)
      if nl>1:
        sz=ndimage.sum(np.ones_like(lab2),lab2,range(1,nl+1)); keep=np.argmax(sz)+1
        a[lab2!=keep,3]=0
      al=a[:,:,3]>0
      yy,xx=np.where(al)
      a=a[yy.min():yy.max()+1, xx.min():xx.max()+1]
      # drop tiny disconnected components (label residue): remove rows at top separated by empty row
      Image.fromarray(a).save(os.path.join(ROOT,'sprites',f'{names[n]}_{kit}.png'))
      if kit=='away' and names[n] in('kuminga','landale'): print(names[n],p,a.shape)
