import os
from os import listdir
from os.path import isfile, join, exists
import re
import csv
import mysql.connector
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'extreme-unison-443418-e6-15c860136091.json'

def clean_and_transform(text):
    cleaned_text = re.sub(r'[^\d\n]', '', text)
    rows = cleaned_text.strip().split('\n')
    
    if len(rows) != 3:
        print("Skipping entry due to unexpected number of rows.")
        return None
    
    try:
        first_value = int(rows[0])
        if str(first_value).startswith('1'):
            first_value = first_value / 10
        else:
            first_value = first_value / 100

        # Process second value with additional conditions
        second_value = None
        if rows[1]:
            second_value = int(rows[1]) / 100
            # Check if first value is > 10 and adjust second value accordingly
            if first_value > 10.00:
                if second_value <= 10.00:
                    second_value *= 10

        # Process third value
        third_value = int(rows[2]) / 1000 if rows[2] else None

        if second_value is None or third_value is None:
            print("Skipping entry due to invalid second or third value.")
            return None
        
        rows[0] = f"{first_value:.3f}"
        rows[1] = f"{second_value:.3f}"
        rows[2] = f"{third_value:.3f}"

        return rows

    except ValueError as e:
        print(f"Error processing values: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def detect_text(path):
    client = vision.ImageAnnotatorClient()

    try:
        with open(path, "rb") as image_file:
            content = image_file.read()
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return None

    image = vision.Image(content=content)

    try:
        response = client.text_detection(image=image)
    except Exception as e:
        print(f"Error processing image {path}: {e}")
        return None
    
    if response.error.message:
        print(f"API error for image {path}: {response.error.message}")
        return None

    processed_values = clean_and_transform(response.text_annotations[0].description if response.text_annotations else "")
    
    return processed_values

def extract_timestamp(filename):
    if filename.startswith("capture_"):
        filename = filename[len("capture_"):]
    
    year = filename[0:4]
    month = filename[4:6]
    day = filename[6:8]
    hour = filename[9:11]
    minute = filename[11:13]
    second = filename[13:15]
    
    timestamp = f"{year}-{month}-{day} {hour}:{minute}:{second}"
    
    return timestamp

def main():
    mypath = "cropped_testing"
    only_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    
    output_csv = "output1.csv"
    file_exists = exists(output_csv)

    hostname = "powersight-nikhilchadha1534-9076.c.aivencloud.com"
    username = "avnadmin"
    password = "AVNS_U6onSK7r0jsSIvu5DIg"
    database = "defaultdb"
    port = 22162

    conn = mysql.connector.connect(
        host=hostname,
        user=username,
        password=password,
        database=database,
        port=port
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            Timestamps VARCHAR(255),
            ampere FLOAT,
            wattage_kwh FLOAT,
            pf FLOAT
        )
    """)
    
    with open(output_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write header only if file does not already exist
        if not file_exists:
            writer.writerow(["Timestamp", "Ampere", "Wattage (KwH)", "PF"])

        for image_path in only_files:
            processed_values = detect_text(join(mypath, image_path))
            if processed_values:
                timestamp = extract_timestamp(image_path.split('.')[0])
                writer.writerow([timestamp] + processed_values)
                cursor.execute("""
                INSERT INTO readings (Timestamps, ampere, wattage_kwh, pf) 
                VALUES (%s, %s, %s, %s)
                """, [timestamp] + processed_values)
                conn.commit()
        
            else:
                print(f"Skipping file {image_path} due to invalid data.")
            os.remove(join(mypath, image_path))
        cursor.close()
        conn.close()
    

if __name__ == "__main__":
    main()
