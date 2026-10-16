import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def ensure_dir(directory):
    """Ensures that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def plot_training_history(history, save_path=None):
    """Plots training and validation accuracy/loss in the requested format."""
    acc = history.history.get('accuracy', [])
    val_acc = history.history.get('val_accuracy', [])
    loss = history.history.get('loss', [])
    val_loss = history.history.get('val_loss', [])

    epochs_range = range(len(acc))

    # Revert to standard style as requested
    plt.style.use('default')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # Plot Accuracy
    ax1.plot(epochs_range, acc, label='Training Accuracy', linewidth=2)
    ax1.plot(epochs_range, val_acc, label='Validation Accuracy', linewidth=2)
    ax1.legend(loc='upper left')
    ax1.set_title('Model Accuracy')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.grid(True, linestyle='-', alpha=0.3)

    # Plot Loss
    ax2.plot(epochs_range, loss, label='Training Loss', linewidth=2)
    ax2.plot(epochs_range, val_loss, label='Validation Loss', linewidth=2)
    ax2.legend(loc='upper right')
    ax2.set_title('Model Loss')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.grid(True, linestyle='-', alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def plot_confusion_matrix(cm, class_names, save_path=None):
    """Plots a confusion matrix using seaborn."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()
