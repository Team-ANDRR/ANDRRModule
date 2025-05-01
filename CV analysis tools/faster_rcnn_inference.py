# C:\Users\Admin\.conda\envs\fiftyone_env\python.exe ./faster_rcnn_inference.py

import fiftyone as fo
import fiftyone.zoo as foz
import torch
import torchvision.transforms as T
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from PIL import Image
import time
import psutil
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import seaborn as sns
from sklearn.metrics import precision_score, recall_score, f1_score


def safe_open_image(filepath):  # If an image breaks, return None. Otherwise, open and convert to RGB
    try:
        image = Image.open(filepath).convert("RGB")
        return image
    except (OSError, IOError) as e:
        print(f"Error opening image {filepath}: {e}")
        return None


# Step 1: Create the FiftyOne dataset
dataset = foz.load_zoo_dataset(
    "coco-2017",             # The COCO 2017 dataset
    split="validation",      # Options: "train", "validation", or "test"
    label_types=["detections"],
    dataset_name="coco-valid"
)

seed = 10  # Set seed for reproducibility
test_size = 5000  # Adjust how many images are being taken from the dataset
subset_view = dataset.take(test_size, seed=seed)
filepaths = [sample.filepath for sample in subset_view]

# Step 2: Begin Timer
start_program_time = time.time()

# Step 3: Load the Faster R-CNN model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device: {device}")
model = fasterrcnn_resnet50_fpn(pretrained=True)  # Use a pre-trained Faster R-CNN model



model.to(device)
model.eval()  # Set the model to evaluation mode


# Define image transforms
transform = T.Compose([
    T.Resize(800),  # Resize the shorter side to 800 while maintaining aspect ratio
    T.ToTensor(),  # Convert to tensor and scale to [0,1]
   
])





# Step 4: Inference and statistics tracking
total_time = 0
accuracies = []
resources = []
inference_times = []

# Step 5: Initialize lists for ground truth and predictions
true_labels = []  # Ground truth values
pred_labels = []  # Model predictions (1 for "person", 0 for "not person")


# Ground truth extraction helper
def get_ground_truth(sample):
    if sample.ground_truth is None:  # If there are no detections
        return False
    detections = sample.ground_truth.detections
    person_detected = any(d.label == "person" for d in detections)
    return person_detected


# Inference loop
for filepath, sample in zip(filepaths, subset_view):
    # Load image
    image = safe_open_image(filepath)
    if image is None:
        continue

    # Transform image for the model
    input_tensor = transform(image).to(device).unsqueeze(0)  # Add batch dimension

    # Measure inference time and memory usage
    start_time = time.time()
    with torch.no_grad():
        outputs = model(input_tensor)  # Perform inference
    end_time = time.time()

    inference_time = end_time - start_time
    inference_times.append(inference_time)
    total_time += inference_time
    resources.append(psutil.virtual_memory().percent)

    # Parse Faster R-CNN results
    detections = outputs[0]['labels']  # Get predicted labels
    person_detected = (detections == 1).any().item()  # COCO "person" class is 1

    # Get the ground truth from the sample
    ground_truth = get_ground_truth(sample)

    # Append results
    true_labels.append(ground_truth)
    pred_labels.append(person_detected)

    accuracies.append(person_detected == ground_truth)





# Print the total number of parameters in the Faster R-CNN model
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
