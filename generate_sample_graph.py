import os
import matplotlib.pyplot as plt
import numpy as np

def plot_training_history_synthetic(save_path):
    epochs = 47
    epochs_range = range(epochs)
    
    # Synthetic data resembling the image
    np.random.seed(42)
    
    # Accuracy
    acc = 0.25 + 0.45 * (1 - np.exp(-np.array(epochs_range) / 10.0)) + np.random.normal(0, 0.015, epochs)
    val_acc = 0.35 + 0.38 * (1 - np.exp(-np.array(epochs_range) / 6.0)) + np.random.normal(0, 0.01, epochs)
    
    # Loss
    loss = 1.65 - 0.9 * (1 - np.exp(-np.array(epochs_range) / 15.0)) + np.random.normal(0, 0.015, epochs)
    val_loss = 1.3 - 0.55 * (1 - np.exp(-np.array(epochs_range) / 12.0)) + np.random.normal(0, 0.005, epochs)

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
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    plot_training_history_synthetic('outputs/sample_styled_graph_new.png')
    print("Graph generated at outputs/sample_styled_graph_new.png")
