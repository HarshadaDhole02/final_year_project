import os
import sys
import json
import numpy as np
import tensorflow as tf

def load_model_and_classes(model_dir='models'):
    model_path = os.path.join(model_dir, 'model.h5')
    class_path = os.path.join(model_dir, 'class_indices.json')
    
    if not os.path.exists(model_path) or not os.path.exists(class_path):
        print("[ERROR] Model or class indices not found. Please train the model first.")
        sys.exit(1)
        
    try:
        import tf_keras
        model = tf_keras.models.load_model(model_path)
    except Exception:
        model = tf.keras.models.load_model(model_path)
    with open(class_path, 'r') as f:
        class_names = json.load(f)
        
    return model, class_names

def predict_image(image_path, model, class_names):
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return None, None
        
    try:
        # Load and preprocess image
        img = tf.keras.utils.load_img(image_path, target_size=(224, 224))
        img_array = tf.keras.utils.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0) # Create batch axis
        
        # Predict
        predictions = model.predict(img_array, verbose=0)
        score = tf.nn.softmax(predictions[0]) if not tf.is_tensor(predictions) else predictions[0]
        
        # Get top class
        predicted_index = np.argmax(score)
        predicted_class = class_names[predicted_index]
        confidence = float(score[predicted_index]) * 100
        
        return predicted_class, confidence
    except Exception as e:
        print(f"[ERROR] Failed to process image: {str(e)}")
        return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python predict.py <path_to_image>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    model, class_names = load_model_and_classes()
    
    predicted_class, confidence = predict_image(image_path, model, class_names)
    
    if predicted_class:
        print(f"\n--- Prediction Results ---")
        print(f"File: {image_path}")
        print(f"Predicted Class: {predicted_class}")
        print(f"Confidence: {confidence:.2f}%")
        print("--------------------------\n")

if __name__ == "__main__":
    main()
