import os
from os import listdir
from os.path import isfile, join
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/purusachdeva/Desktop/capstone/powersight-432911-de03b31692a5.json'
from google.cloud import vision
import re

def clean_and_transform(text):
    # Remove all characters except numbers and newlines
    cleaned_text = re.sub(r'[^\d\n]', '', text)
    
    # Split the cleaned text by newlines into rows
    rows = cleaned_text.strip().split('\n')
    
    # Ensure we have at least 3 rows for processing
    if len(rows) >= 3:
        # First row processing
        first_value = int(rows[0])
        if str(first_value).startswith('1'):
            first_value = first_value / 10
        else:
            first_value = first_value / 100

        # Second row processing
        second_value = int(rows[1]) / 100

        # Third row processing (power factor)
        third_value = int(rows[2]) / 1000
        
        # Format the values back into strings with proper decimal places
        rows[0] = f"{first_value:.3f}"
        rows[1] = f"{second_value:.3f}"
        rows[2] = f"{third_value:.3f}"

    return '\n'.join(rows)

def detect_text(path):
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    ocr_text = []

    for text in texts:
        ocr_text.append(f"\r\n{text.description}")
    
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    # Post-processing the text to clean and transform it
    processed_text = clean_and_transform(texts[0].description)
    
    return processed_text

def main():
    # mypath = "/Users/purusachdeva/Desktop/capstone/cropped_images/test/"
    # only_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    # for image_path in only_files:
    #     text = detect_text(mypath + image_path)
    #     print(image_path)
    #     print(text)
    #     print("\n\n")

    text = detect_text('/Users/purusachdeva/Desktop/capstone/cropped_images/capture_20240821_174146.jpg')
    print(text)

if __name__ == "__main__":
    main()
