import os
import sys
import logging
from PIL import Image
from ultralytics import YOLO

# Setup logging
logging.basicConfig(filename='/home/ec2-user/meter_detection.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
MODEL_PATH = "/home/ec2-user/best.pt"
INPUT_DIR = "/home/ec2-user/uploaded_images"
OUTPUT_DIR = "/home/ec2-user/cropped_images"

try:
    # Load the YOLO model
    infer = YOLO(MODEL_PATH)
    logging.info("Model loaded successfully.")

    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Output directory ensured: {OUTPUT_DIR}")

    # Function to get the index of the class named 'meter'
    def get_meter_class_index(model):
        for idx, class_name in model.names.items():
            if class_name.lower() == 'meter':
                return idx
        return None

    # Get the class index for 'meter'
    meter_class_index = get_meter_class_index(infer)
    if meter_class_index is None:
        raise ValueError("Class 'meter' not found in model class names")
    logging.info(f"Meter class index: {meter_class_index}")

    # Function to crop and save an image
    def crop_and_save(image, box, save_dir, file_name):
        cropped_image = image.crop(box)
        save_path = os.path.join(save_dir, file_name)
        cropped_image.save(save_path)
        logging.info(f"Saved cropped image: {save_path}")

    # Predict on images in the input directory
    results = infer.predict(INPUT_DIR, save=True)
    logging.info(f"Prediction completed on images in {INPUT_DIR}")

    # Iterate over results and save crops for the 'meter' class
    for result in results:
        img_path = result.path
        image = Image.open(img_path)
        
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        
        meter_count = 0
        for box in result.boxes:
            if int(box.cls) == meter_class_index:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                if meter_count == 0:
                    new_filename = f"{base_name}.jpg"
                else:
                    new_filename = f"{base_name}_{meter_count}.jpg"
                
                crop_and_save(image, (x1, y1, x2, y2), OUTPUT_DIR, new_filename)
                meter_count += 1
        
        logging.info(f"Processed {meter_count} meters in {img_path}")

        # Delete the input image after processing
        os.remove(img_path)
        logging.info(f"Deleted input image: {img_path}")

    print(f'Cropped images saved to {OUTPUT_DIR}')
    logging.info(f'Script completed successfully. Cropped images saved to {OUTPUT_DIR}')

except Exception as e:
    logging.error(f"An error occurred: {str(e)}")
    print(f"An error occurred. Check the log file for details.")
    sys.exit(1)