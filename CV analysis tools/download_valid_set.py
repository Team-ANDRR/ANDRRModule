import fiftyone.zoo as foz

# Load the COCO dataset
dataset = foz.load_zoo_dataset(
    "coco-2017",             # The COCO 2017 dataset
    split="validation",           # Options: "train", "validation", or "test"
    label_types=["detections"],  # Load object detection annotations
    dataset_name="coco-valid"  # Optional: give your dataset a name
)

# Print dataset summary
print(dataset)