import requests
import streamlit as st
from segmind import SDXL


url = "https://api.segmind.com/v1/sdxl1.0-colossus-lightning"
added_prompt = """
                8k, soft lighting, highly detailed, digital painting by \
                Android Jones'
                """


def get_segmind_image_requests(prompt):
    api_key = st.secrets.segmind.api_key
    url = "https://api.segmind.com/v1/sdxl1.0-colossus-lightning"
    data = {
            "prompt": prompt + added_prompt,
            "samples": 1,
            "scheduler": "DPM++ SDE",
            "num_inference_steps": 9,
            "guidance_scale": 1,
            "seed": 902448,
            "img_width": 1024,
            "img_height": 1024,
            "base64": False
          }

    response = requests.post(url, json=data, headers={'x-api-key': api_key})
    return response

def _get_segmind_creds():
    segmind_creds = st.secrets.segmind.api_key
    return segmind_creds

def get_segmind_image(prompt, api_key=None, model='SDXL'):
    if api_key is None:
        api_key = _get_segmind_creds()
    if model == 'SDXL':
        model = SDXL(api_key=api_key)
    else:
        ValueError(f'{model} not recognized')
    image = model.generate(prompt)
    return image

