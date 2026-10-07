# Supplementary, segmentation-free check: share of Blender silhouette contour pixels that have a
# generated-image edge (Canny 30/90) within 3 px. Not part of the acceptance bar.
import numpy as np, cv2, sys, os
base=cv2.imread(sys.argv[1]); H,W=base.shape[:2]
bm=(cv2.imread(sys.argv[2],0)>0).astype(np.uint8)
bc=cv2.Canny(bm*255,50,150)
def ed(im): return cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),(3,3),0),30,90)
for nm in sys.argv[3:]:
    im=cv2.resize(cv2.imread(nm),(W,H),interpolation=cv2.INTER_AREA)
    d=cv2.distanceTransform((ed(im)==0).astype(np.uint8),cv2.DIST_L2,3)[bc>0]
    print(os.path.basename(nm), f"edge3={np.mean(d<=3):.2f}")
