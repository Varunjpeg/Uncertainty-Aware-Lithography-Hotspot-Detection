import os
import time
from pathlib import Path
from PIL import Image
import numpy as np
from concurrent.futures import ProcessPoolExecutor

def load_img(path_str):
    with Image.open(path_str) as img:
        return np.array(img.convert('L').resize((64, 64), Image.Resampling.BILINEAR), dtype=np.uint8)

def process_benchmark(b_name, root, out_dir, max_workers=8):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ['train', 'test']:
        target_file = out_dir / f'{b_name}_{split}.npz'
        if target_file.exists():
            print(f"Skipping {b_name} {split}, {target_file} already exists.")
            continue
            
        sp = Path(root) / b_name / split
        hs_dir = sp / f'{split}_hs'
        nhs_dir = sp / f'{split}_nhs'
        hs_files = [str(hs_dir / f) for f in os.listdir(hs_dir) if f.lower().endswith(('.png', '.jpg', '.bmp'))]
        nhs_files = [str(nhs_dir / f) for f in os.listdir(nhs_dir) if f.lower().endswith(('.png', '.jpg', '.bmp'))]
        
        all_files = hs_files + nhs_files
        all_labels = np.array([1]*len(hs_files) + [0]*len(nhs_files), dtype=np.int64)
        
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            imgs = list(ex.map(load_img, all_files, chunksize=128))
        img_arr = np.stack(imgs, axis=0)
        np.savez_compressed(target_file, images=img_arr, labels=all_labels)
        t1 = time.time()
        print(f'{b_name} {split}: {len(all_files)} images (HS: {len(hs_files)}, NHS: {len(nhs_files)}) cached in {t1-t0:.2f}s -> {target_file.name}')

if __name__ == '__main__':
    root = r'e:\aiml\dataset'
    out = r'e:\aiml\cache'
    for b in ['iccad1', 'iccad2', 'iccad3', 'iccad4', 'iccad5']:
        process_benchmark(b, root, out)
