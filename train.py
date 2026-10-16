import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

from clean_dataset import clean_dataset
from utils import ensure_dir, plot_training_history, plot_confusion_matrix

# Configuration
CLEAN_DIR = 'clean_dataset'
MODELS_DIR = 'models'
OUTPUT_DIR = 'outputs'

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
INITIAL_EPOCHS = 10
FINE_TUNE_EPOCHS = 15

def get_class_weights(train_ds):
    print("Calculating class weights (this may take a moment)...")
    y_train = []
    for images, labels in train_ds.unbatch():
        y_train.append(np.argmax(labels.numpy()))
    
    classes = np.unique(y_train)
    weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
    class_weights = dict(zip(classes, weights))
    return class_weights

def prepare_datasets():
    print("Loading datasets from directory...")
    # Load 70% Train, 30% Validation/Test
    train_ds = tf.keras.utils.image_dataset_from_directory(
        CLEAN_DIR,
        validation_split=0.3,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='categorical'
    )
    
    val_test_ds = tf.keras.utils.image_dataset_from_directory(
        CLEAN_DIR,
        validation_split=0.3,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='categorical'
    )
    
    # Split the 30% val_test_ds into 15% Validation and 15% Test
    val_batches = tf.data.experimental.cardinality(val_test_ds)
    test_ds = val_test_ds.take(val_batches // 2)
    val_ds = val_test_ds.skip(val_batches // 2)

    class_names = train_ds.class_names
    print(f"Classes found: {class_names}")

    # Save class indices for inference
    ensure_dir(MODELS_DIR)
    with open(os.path.join(MODELS_DIR, 'class_indices.json'), 'w') as f:
        json.dump(class_names, f)

    # Autotune for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    return train_ds, val_ds, test_ds, class_names

def build_model(num_classes):
    # Data Augmentation layer
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.2),
        layers.RandomBrightness(0.2)
    ], name="data_augmentation")

    # Load EfficientNetB0 Base
    # Note: EfficientNet includes normalization internally, but we can rely on standard TF prep
    base_model = EfficientNetB0(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')
    base_model.trainable = False # Freeze base for initial training

    # Build top layers
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = data_augmentation(inputs)
    # EfficientNet in TF2 expects inputs in [0, 255] or handled by its specific preprocess_input.
    # However, keras.applications.efficientnet.EfficientNetB0 handles scaling automatically inside the model layer if using default inputs.
    
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = models.Model(inputs, outputs)
    
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    return model

def main():
    ensure_dir(MODELS_DIR)
    ensure_dir(OUTPUT_DIR)
    
    # Check if cleaned dataset exists
    if not os.path.exists(CLEAN_DIR) or len(os.listdir(CLEAN_DIR)) == 0:
        print("Clean dataset not found. Running cleaning pipeline...")
        clean_dataset()
    else:
        print("Clean dataset found. Skipping cleaning pipeline.")

    train_ds, val_ds, test_ds, class_names = prepare_datasets()
    
    model = build_model(len(class_names))
    model.summary()
    
    class_weights = get_class_weights(train_ds)
    print(f"Class weights applied: {class_weights}")
    
    # Callbacks for Phase 1
    callbacks_initial = [
        EarlyStopping(patience=5, restore_best_weights=True, monitor='val_loss'),
        ModelCheckpoint(os.path.join(MODELS_DIR, 'model_initial.h5'), save_best_only=True, monitor='val_loss')
    ]
    
    print(f"\nStarting initial training (Base Model Frozen) for {INITIAL_EPOCHS} epochs...")
    history_initial = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=INITIAL_EPOCHS,
        class_weight=class_weights,
        callbacks=callbacks_initial
    )
    
    # --- Fine Tuning Phase ---
    print("\nStarting fine-tuning...")
    # Unfreeze the base model
    base_model = model.layers[2] # EfficientNetB0 is the 3rd layer (Input, Augmentation, EfficientNetB0)
    base_model.trainable = True
    
    # Freeze bottom layers and unfreeze top 30 layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False
        
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
                  
    # Callbacks for Phase 2
    callbacks_fine = [
        EarlyStopping(patience=5, restore_best_weights=True, monitor='val_loss'),
        ModelCheckpoint(os.path.join(MODELS_DIR, 'model_finetuned.h5'), save_best_only=True, monitor='val_loss'),
        ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-7)
    ]
    
    total_epochs = INITIAL_EPOCHS + FINE_TUNE_EPOCHS
    print(f"\nFine-tuning for {FINE_TUNE_EPOCHS} additional epochs...")
    history_fine = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=total_epochs,
        initial_epoch=history_initial.epoch[-1],
        class_weight=class_weights,
        callbacks=callbacks_fine
    )
    
    # Merge histories for plotting
    acc = history_initial.history['accuracy'] + history_fine.history['accuracy']
    val_acc = history_initial.history['val_accuracy'] + history_fine.history['val_accuracy']
    loss = history_initial.history['loss'] + history_fine.history['loss']
    val_loss = history_initial.history['val_loss'] + history_fine.history['val_loss']
    
    class MergedHistory:
        def __init__(self, d):
            self.history = d
            
    merged_history = MergedHistory({
        'accuracy': acc, 'val_accuracy': val_acc,
        'loss': loss, 'val_loss': val_loss
    })
    
    # Save training graphs
    plot_training_history(merged_history, save_path=os.path.join(OUTPUT_DIR, 'training_history.png'))
    
    # Evaluate on test set
    print("\nEvaluating on test dataset...")
    test_loss, test_acc = model.evaluate(test_ds)
    print(f"Test Accuracy: {test_acc:.4f}, Test Loss: {test_loss:.4f}")
    
    # Predictions for Confusion Matrix and Classification Report
    print("Generating Classification Report and Confusion Matrix...")
    y_true = []
    y_pred = []
    
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_pred.extend(np.argmax(preds, axis=1))
        y_true.extend(np.argmax(labels.numpy(), axis=1))
        
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix(cm, class_names, save_path=os.path.join(OUTPUT_DIR, 'confusion_matrix.png'))
    
    report = classification_report(y_true, y_pred, target_names=class_names)
    print("\nClassification Report:\n", report)
    
    with open(os.path.join(OUTPUT_DIR, 'classification_report.txt'), 'w') as f:
        f.write(report)
        f.write(f"\nTest Accuracy: {test_acc:.4f}\nTest Loss: {test_loss:.4f}")

    print("\nTraining pipeline complete. Model and outputs saved.")

if __name__ == "__main__":
    main()
