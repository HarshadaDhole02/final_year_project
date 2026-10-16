import os
import cv2
import json
import shutil
import numpy as np
import imagehash
from PIL import Image
import matplotlib.pyplot as plt
from utils import ensure_dir

RAW_DIR = 'dataset/raw'
CLEAN_DIR = 'clean_dataset'
OUTPUT_DIR = 'outputs'

# Thresholds
BLUR_THRESHOLD = 50.0  # Images with variance of laplacian below this are considered blurry
MIN_IMAGE_DIM = 64     # Minimum width/height

def is_blurry(image_cv):
    """Calculates variance of Laplacian to determine blurriness."""
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < BLUR_THRESHOLD

def clean_dataset():
    ensure_dir(CLEAN_DIR)
    ensure_dir(OUTPUT_DIR)
    
    stats = {
        'total_scanned': 0,
        'corrupted': 0,
        'blurry': 0,
        'duplicates': 0,
        'too_small': 0,
        'valid': 0,
        'classes': {}
    }
    
    seen_hashes = set()
    sample_images = {} # To store one sample per class for visualization
    
    if not os.path.exists(RAW_DIR):
        print(f"[ERROR] Raw directory '{RAW_DIR}' not found.")
        return

    classes = [d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))]
    
    for cls in classes:
        print(f"Processing class: {cls}")
        cls_raw_path = os.path.join(RAW_DIR, cls)
        cls_clean_path = os.path.join(CLEAN_DIR, cls)
        ensure_dir(cls_clean_path)
        
        stats['classes'][cls] = {'scanned': 0, 'valid': 0}
        
        for filename in os.listdir(cls_raw_path):
            stats['total_scanned'] += 1
            stats['classes'][cls]['scanned'] += 1
            
            file_path = os.path.join(cls_raw_path, filename)
            
            # Check file size (0 byte)
            if os.path.getsize(file_path) == 0:
                stats['corrupted'] += 1
                continue
                
            try:
                # Use PIL to open and convert to RGB
                with Image.open(file_path) as img:
                    img = img.convert('RGB')
                    width, height = img.size
                    
                    if width < MIN_IMAGE_DIM or height < MIN_IMAGE_DIM:
                        stats['too_small'] += 1
                        continue
                    
                    # Compute perceptual hash to find exact/near duplicates
                    img_hash = str(imagehash.phash(img))
                    if img_hash in seen_hashes:
                        stats['duplicates'] += 1
                        continue
                    seen_hashes.add(img_hash)
                    
                    # Convert to cv2 format for blur check
                    img_cv = np.array(img) 
                    img_cv = img_cv[:, :, ::-1].copy() # RGB to BGR
                    
                    if is_blurry(img_cv):
                        stats['blurry'] += 1
                        continue
                    
                    # Passed all checks, save to clean directory
                    # Save uniformly as JPG
                    clean_filename = f"{os.path.splitext(filename)[0]}.jpg"
                    clean_path = os.path.join(cls_clean_path, clean_filename)
                    img.save(clean_path, format='JPEG', quality=95)
                    
                    stats['valid'] += 1
                    stats['classes'][cls]['valid'] += 1
                    
                    if cls not in sample_images:
                        sample_images[cls] = clean_path
                        
            except Exception as e:
                # Image is corrupted or unreadable
                stats['corrupted'] += 1
                continue

    # Save log
    with open(os.path.join(OUTPUT_DIR, 'cleaning_log.json'), 'w') as f:
        json.dump(stats, f, indent=4)
        
    print("\n--- Cleaning Summary ---")
    print(f"Total Scanned: {stats['total_scanned']}")
    print(f"Valid (Saved): {stats['valid']}")
    print(f"Removed (Corrupted): {stats['corrupted']}")
    print(f"Removed (Blurry): {stats['blurry']}")
    print(f"Removed (Duplicates): {stats['duplicates']}")
    print(f"Removed (Too Small): {stats['too_small']}")
    print("------------------------\n")

    # Plot Class Distribution
    plot_distribution(stats['classes'])
    
    # Plot Samples
    plot_samples(sample_images)


def plot_distribution(class_stats):
    classes = list(class_stats.keys())
    valid_counts = [class_stats[c]['valid'] for c in classes]
    
    plt.figure(figsize=(12, 6))
    plt.bar(classes, valid_counts, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.title('Cleaned Dataset Class Distribution')
    plt.xlabel('Classes')
    plt.ylabel('Number of Valid Images')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'class_distribution.png'))
    plt.close()

def plot_samples(sample_images):
    if not sample_images:
        return
    n_classes = len(sample_images)
    cols = min(4, n_classes)
    rows = (n_classes + cols - 1) // cols
    
    plt.figure(figsize=(cols*3, rows*3))
    for i, (cls, path) in enumerate(sample_images.items()):
        img = Image.open(path)
        plt.subplot(rows, cols, i+1)
        plt.imshow(img)
        plt.title(cls)
        plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'sample_images.png'))
    plt.close()

if __name__ == "__main__":
    print("Starting dataset cleaning and filtering pipeline...")
    clean_dataset()
