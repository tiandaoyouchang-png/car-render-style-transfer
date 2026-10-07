# Same method as bltest/chair/simc.py (SheenChair case): GrabCut seeded from the Blender mask,
# IoU vs Blender mask, outer-contour distance, interior-edge distance, bbox offsets.
# usage: python3 sim.py <base.png> <mask_bin.png> <overlay_out_dir> scene1.png ...
import numpy as np, cv2, sys, os, json
base=cv2.imread(sys.argv[1]); H,W=base.shape[:2]
bm=(cv2.imread(sys.argv[2],0)>0).astype(np.uint8)
cnts,_=cv2.findContours(bm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); bm=np.zeros_like(bm); cv2.drawContours(bm,cnts,-1,1,-1)
ys,xs=np.nonzero(bm)
def grab(im):
    gc=np.full((H,W),cv2.GC_BGD,np.uint8)
    dil=cv2.dilate(bm,np.ones((41,41),np.uint8)); ero=cv2.erode(bm,np.ones((21,21),np.uint8))
    gc[dil>0]=cv2.GC_PR_BGD; gc[bm>0]=cv2.GC_PR_FGD; gc[ero>0]=cv2.GC_FGD
    b=np.zeros((1,65)); f=np.zeros((1,65))
    cv2.grabCut(im,gc,None,b,f,6,cv2.GC_INIT_WITH_MASK)
    g=((gc==1)|(gc==3)).astype(np.uint8)
    n,l,s,_=cv2.connectedComponentsWithStats(g); k=np.argmax(s[1:,4])+1; g=(l==k).astype(np.uint8)
    return g
def edges(im): return cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),(3,3),0),60,150)
x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
inner=cv2.erode(bm,np.ones((5,5),np.uint8))
be=edges(base)*inner
bc=cv2.Canny(bm*255,50,150)
res={}
for nm in sys.argv[4:]:
    im=cv2.resize(cv2.imread(nm),(W,H),interpolation=cv2.INTER_AREA)
    g=grab(im)
    iou=(bm&g).sum()/(bm|g).sum()
    gc_=cv2.Canny(g*255,50,150)
    dc=cv2.distanceTransform((gc_==0).astype(np.uint8),cv2.DIST_L2,3)[bc>0]
    ge=edges(im)
    di=cv2.distanceTransform((ge==0).astype(np.uint8),cv2.DIST_L2,3)[be>0]
    gy,gx=np.nonzero(g)
    r=dict(iou=float(iou),c3=float(np.mean(dc<=3)),c6=float(np.mean(dc<=6)),i3=float(np.mean(di<=3)),i6=float(np.mean(di<=6)),
           L=int(gx.min()-x0),R=int(gx.max()-x1),T=int(gy.min()-y0),B=int(gy.max()-y1))
    r['pass']=bool(r['iou']>0.95 and abs(r['B'])<5 and r['c3']>=0.80)
    res[os.path.basename(nm)]=r
    print(os.path.basename(nm),f"IoU={iou:.3f} 轮廓<=3px={r['c3']:.2f} <=6px={r['c6']:.2f} 内部线<=3={r['i3']:.2f} bbox L{r['L']:+d} R{r['R']:+d} T{r['T']:+d} B{r['B']:+d}", 'PASS' if r['pass'] else 'FAIL')
    # overlay: blender contour red, detected green
    ov=im.copy(); cv2.drawContours(ov,cnts,-1,(0,0,255),1)
    c2,_=cv2.findContours(g,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); cv2.drawContours(ov,c2,-1,(0,255,0),1)
    os.makedirs(sys.argv[3],exist_ok=True); cv2.imwrite(os.path.join(sys.argv[3],'chk_'+os.path.basename(nm)),ov)
json.dump(res,open(os.path.join(sys.argv[3],'metrics.json'),'a'),ensure_ascii=False); open(os.path.join(sys.argv[3],'metrics.json'),'a').write('\n')
