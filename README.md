# Animal Disease Classification System 🧬

A complete, end-to-end deep learning image classification system built to detect various animal diseases from image data. 
This project utilizes **EfficientNetB0** (via Transfer Learning), an automated data cleaning pipeline, and features a premium **Streamlit** web application for real-time inference.

## 📁 Project Structure

```
animal_disease_classifier/
│
├── dataset/
│   └── raw/               # Place raw, uncleaned class folders here
├── clean_dataset/         # Automatically generated cleaned dataset
├── models/                # Saved models and class indices
├── outputs/               # Training logs, graphs, confusion matrix
│
├── app.py                 # Streamlit web application
├── train.py               # Model training script
├── predict.py             # Single image prediction script
├── clean_dataset.py       # Automated data filtering and cleaning script
├── utils.py               # Helper utilities for plotting and setup
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## 📋 Dataset Requirements

1. **Folder Structure**: Your raw images should be placed in `dataset/raw/` with one sub-folder per class (e.g., `dataset/raw/healthy/`, `dataset/raw/mastitis/`).
2. **Formats**: The cleaning script will accept common image formats and convert them uniformly to `.jpg`.
3. **Quality Control**: The `clean_dataset.py` pipeline will automatically remove:
   - 0-byte or corrupted files
   - Exact or near duplicates (using perceptual hashing)
   - Extremely blurry images (using Laplacian variance)
   - Extremely small images (<64x64)

## 🚀 How to Run

### 1. Installation

Ensure you have Python 3.10+ installed. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Automated Data Cleaning (Optional, auto-runs during training)

If you wish to clean the data and view the statistics without training, run:
```bash
python clean_dataset.py
```
*This will generate `clean_dataset/` and save analysis graphs in `outputs/`.*

### 3. Model Training

Train the EfficientNetB0 model. The script automatically handles splitting (70% Train, 15% Val, 15% Test) and applies augmentation.
```bash
python train.py
```
*Outputs: `models/model.h5`, `models/class_indices.json`, and evaluation graphs in `outputs/`.*

### 4. Test Predictions

Test the model on a single image via the command line:
```bash
python predict.py path/to/your/image.jpg
```

### 5. Launch Web Application

Run the premium Streamlit dashboard to interact with your model:
```bash
streamlit run app.py
```

## ⚡ Optimization Tips for Low-End GPUs

If you encounter Out-Of-Memory (OOM) errors or slow training speeds on lower-end hardware, consider these adjustments in `train.py`:
1. **Reduce Batch Size**: Change `BATCH_SIZE = 32` to `16` or `8`.
2. **Reduce Image Size**: Change `IMG_SIZE = (224, 224)` to `(128, 128)` (this will reduce accuracy slightly but improve speed significantly).
3. **Use Mixed Precision**: Add this at the top of `train.py` to use 16-bit floats:
   ```python
   from tensorflow.keras import mixed_precision
   mixed_precision.set_global_policy('mixed_float16')
   ```
4. **Cache Wisely**: If your dataset is huge, `train_ds.cache()` might fill up your RAM. Remove `.cache()` if system memory (RAM) maxes out.
