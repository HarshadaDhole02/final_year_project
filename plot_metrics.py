import os
import matplotlib.pyplot as plt
import numpy as np

def parse_classification_report(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    classes = []
    precision = []
    recall = []
    f1_score = []
    
    accuracy = 0.0
    
    for line in lines:
        parts = line.split()
        if len(parts) == 5 and parts[0] not in ['macro', 'weighted', 'accuracy']:
            try:
                classes.append(parts[0])
                precision.append(float(parts[1]))
                recall.append(float(parts[2]))
                f1_score.append(float(parts[3]))
            except ValueError:
                pass
        if "Test Accuracy:" in line:
            accuracy = float(line.split(":")[1].strip())
            
    return classes, precision, recall, f1_score, accuracy

def plot_bar(classes, values, title, ylabel, save_path, color):
    plt.figure(figsize=(10, 6))
    bars = plt.bar(classes, values, color=color)
    plt.title(title, fontsize=16)
    plt.ylabel(ylabel, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1.05)
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f'{yval:.2f}', ha='center', va='bottom', fontsize=10)
        
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def main():
    report_path = os.path.join('outputs', 'classification_report.txt')
    if not os.path.exists(report_path):
        print("Classification report not found!")
        return
        
    classes, precision, recall, f1_score, accuracy = parse_classification_report(report_path)
    
    output_dir = 'outputs'
    
    # Plot Precision
    plot_bar(classes, precision, 'Precision by Class', 'Precision', os.path.join(output_dir, 'precision.png'), 'skyblue')
    print("Saved precision.png")
    
    # Plot Recall
    plot_bar(classes, recall, 'Recall by Class', 'Recall', os.path.join(output_dir, 'recall.png'), 'lightgreen')
    print("Saved recall.png")
    
    # Plot F1 Score
    plot_bar(classes, f1_score, 'F1 Score by Class', 'F1 Score', os.path.join(output_dir, 'f1_score.png'), 'salmon')
    print("Saved f1_score.png")
    
    # Plot Accuracy
    plt.figure(figsize=(6, 8))
    bars = plt.bar(['Overall Accuracy'], [accuracy], color='mediumpurple', width=0.5)
    plt.title('Model Accuracy', fontsize=16)
    plt.ylabel('Accuracy', fontsize=12)
    plt.ylim(0, 1.05)
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f'{yval:.4f}', ha='center', va='bottom', fontsize=12)
        
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'accuracy.png'))
    plt.close()
    print("Saved accuracy.png")

if __name__ == '__main__':
    main()
