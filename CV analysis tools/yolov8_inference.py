import fiftyone as fo
import fiftyone.zoo as foz
import torch
from ultralytics import YOLO  # For YOLOv8
from PIL import Image
import time
import psutil
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import torchvision.transforms as T
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
import os

# Define preprocessing transformations
transform = T.Compose([
    T.Resize((640, 640)),  # Resize image to 640x640 (YOLOv8 input size)
    T.ToTensor(),          # Convert image to tensor
])

def safe_open_image(filepath):
    try:
        image = Image.open(filepath).convert("RGB")
        return transform(image)  # Apply transformations
    except (OSError, IOError) as e:
        print(f"Error opening image {filepath}: {e}")
        return None

# Load COCO dataset
dataset = foz.load_zoo_dataset("coco-2017", split="validation", label_types=["detections"], dataset_name="coco-valid")

seed = 10  # Set seed for reproducibility
test_size = 5000  # Adjust how many images are taken from the dataset
subset_view = dataset.take(test_size, seed=seed)  # Fix seed for reproducibility
filepaths = [sample.filepath for sample in subset_view]

start_program_time = time.time()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO("yolov8n.pt").to(device)  # Load YOLO model onto appropriate device
# yolov8x.pt, yolov8m.pt, yolov8n.pt


total_time = 0
accuracies = []
resources = []
inference_times = []
true_labels = []
pred_labels = []
curr_image_counter = 0

# Ground truth extraction helper
def get_ground_truth(sample):
    if sample.ground_truth is None:
        return False
    detections = sample.ground_truth.detections
    return any(d.label == "person" for d in detections)

# Inference loop
for filepath, sample in zip(filepaths, subset_view):
    image = safe_open_image(filepath)
    if image is None:
        continue
    image = image.unsqueeze(0).to(device)  # Add batch dimension and move to device
    
    start_time = time.time()
    results = model(image)
    end_time = time.time()
    
    inference_time = end_time - start_time
    inference_times.append(inference_time)
    total_time += inference_time
    resources.append(psutil.virtual_memory().percent)
    
    detections = results[0].boxes.data
    predicted_is_person = any(int(det[5]) == 0 for det in detections)
    
    ground_truth = get_ground_truth(sample)
    true_labels.append(ground_truth)
    pred_labels.append(predicted_is_person)
    accuracies.append(predicted_is_person == ground_truth)
    
    #print("Curr Image: ", curr_image_counter)
    curr_image_counter += 1
    
    
# Print the total number of parameters in the YOLOv8 model
total_params = sum(p.numel() for p in model.parameters())
print(f"Total number of parameters: {total_params}")

# Estimate the size of the model in MB
model_size = total_params * 4 / (1024 ** 2)  # Each parameter is 4 bytes (32-bit float)
print(f"Estimated model size: {model_size:.2f} MB")


# Results summary
print(f"Total inference time: {total_time:.2f} seconds")
print(f"Average accuracy: {sum(accuracies) / len(accuracies):.2%}")
print(f"Average memory usage: {sum(resources) / len(resources):.2f}%")

detection_rate = sum(accuracies) / len(accuracies)
print(f"Human Detection Rate: {detection_rate:.2%}")
print(f"Max Inference Time: {max(inference_times):.2f} seconds")
print(f"Min Inference Time: {min(inference_times):.2f} seconds")
print(f"Average Inference Time Per Image: {total_time / len(filepaths):.2f} seconds")


# Calculate precision, recall, and F1 score
precision = precision_score(true_labels, pred_labels)
recall = recall_score(true_labels, pred_labels)
f1 = f1_score(true_labels, pred_labels)

# Print additional metrics
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1 Score: {f1:.2f}")


# Confusion Matrix
cm = confusion_matrix(true_labels, pred_labels)
print("Confusion Matrix:")
print(cm)




# Visualization

# Memory usage plot
plt.plot(resources)
plt.title("Memory Usage Over Time")
plt.xlabel("Inference Iteration")
plt.ylabel("Memory Usage (%)")
plt.show()

# Inference time distribution
plt.hist(inference_times, bins=30, edgecolor='black')
plt.title("Inference Time Distribution")
plt.xlabel("Inference Time (seconds)")
plt.ylabel("Frequency")
plt.show()

# Confusion matrix heatmap
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Not Person", "Person"], yticklabels=["Not Person", "Person"])
plt.title("Confusion Matrix Heatmap")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()
