import os
import requests
import keras
from keras.models import load_model
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
class_names = ['fake', 'real']
os.environ["HUGGINGFACE_TOKEN"] = "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"

image_size = (128, 128)


POLICE = 'TypoSlab Irregular Demo.otf'


def download_file(url, local_path):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

def load_keras_model_from_hub(model_id):
    model_url = f"https://huggingface.co/Nielzac/Midjourney_image_detector/resolve/main/MIDJOURNEY_DETECT.h5"
    local_path = "MIDJOURNEY_DETECT.h5"
    download_file(model_url, local_path)
def apply_fake_filter(image, fake_score, additional_text):
    # Convert the image to a NumPy array
    image_array = np.array(image)

    # Determine the image dimensions
    height, width, _ = image_array.shape

    # Convert the fake score to text
    text = f"{int(fake_score*100)}%"

    font_size = int(height * 0.15)  # adjust the percentage as needed

    # Create a mask image with the color filter and apply it to the entire image
    mask_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask_image)
    if additional_text == 'fake':
        mask_draw.rectangle([(0, 0), (width, height)], fill=(255, 0, 0, int(255*0.7)))
    else:
        mask_draw.rectangle([(0, 0), (width, height)], fill=(0, 0, 255, int(255*0.7)))

    # Create a composite image that includes the original image and the filter
    filtered_image = Image.alpha_composite(image.convert("RGBA"), mask_image)

    # Specify the font and size
    font = ImageFont.truetype(POLICE, size=font_size)

    # Create an ImageDraw object
    draw = ImageDraw.Draw(filtered_image)

    # Specify the coordinates of the text in the middle of the image
    text_width, text_height = draw.textsize(text, font)
    text_x = (width - text_width) // 2
    text_y = height // 2 - text_height

    # Draw the text on the image in white
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

    # Calculate the additional text's coordinates
    additional_text_width, additional_text_height = draw.textsize(additional_text, font)
    additional_text_x = (width - additional_text_width) // 2
    additional_text_y = height // 2 

    # Draw the additional text on the image in white
    draw.text((additional_text_x, additional_text_y), additional_text, font=font, fill=(255, 255, 255))

    return filtered_image
def prepare_image(image_path):
    return np.array(convert_to_ela_image(image_path, 90).resize(image_size)).flatten() / 255.0

def convert_to_ela_image(path, quality):
    temp_filename = 'temp_file_name.jpg'
    ela_filename = 'temp_ela.png'
    
    image = Image.open(path).convert('RGB')
    image.save(temp_filename, 'JPEG', quality=quality)
    temp_image = Image.open(temp_filename)
    
    ela_image = ImageChops.difference(image, temp_image)
    
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    return ela_image

st.set_page_config(page_title="Fake Photo Identifier", layout="wide")

st.title("Fake Photo Identifier (Beta) - StendhalGPT Gogh")

# Charger l'image
uploaded_file = st.file_uploader("Choisissez une image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        model = load_model('MIDJOURNEY_DETECT.h5')
        model.compile(optimizer="adam", loss='categorical_crossentropy', metrics=['accuracy'])

    except:
        load_keras_model_from_hub('Midjourney_image_detector')

    image3 = Image.open(uploaded_file)
    image = image3
    #st.image(image, caption="Image originale", use_column_width=True)

    image.save("chemin_de_sauvegarde.jpg")
    print('#################OK')
    model = load_model('MIDJOURNEY_DETECT.h5', compile=False)
    model.compile(optimizer="adam", loss='categorical_crossentropy', metrics=['accuracy'])
    #filtered_image = filtered_image.convert("RGB")
    #filtered_image.save("filtered_image.jpg", "JPEG")
    image = prepare_image("chemin_de_sauvegarde.jpg")
    print(image.shape)
    #image = image.reshape(-1, 128, 128, 3)
    image2 = np.reshape(image, (-1, 128, 128, 3))
    print(image2.shape)
    y_pred = model.predict(image2)
    # Prédiction

    y_pred_class = np.argmax(y_pred, axis = 1)[0]
    st.write(f'Class: {class_names[y_pred_class]} Confidence: {np.amax(y_pred) * 100:0.2f}')

    # Appliquer le hachurage

    hatched_image = apply_fake_filter(image3,np.amax(y_pred), class_names[y_pred_class])

    # Display the image
    st.image(hatched_image, use_column_width=False)

    
    
    st.markdown("""
    ## Source des données
    Les données utilisées pour l'entraînement de ce modèle proviennent de l'ensemble de données CASIA disponible sur Kaggle, 
    qui a été partagé par Sophatvathana. L'ensemble de données peut être consulté à l'adresse suivante : 
    [CASIA Dataset](https://www.kaggle.com/datasets/sophatvathana/casia-dataset)
    """)
