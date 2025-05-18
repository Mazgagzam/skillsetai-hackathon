from googleapiclient.discovery import build
from google.oauth2 import service_account
import base64

from config import GEMINI_API_KEY
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-pro-latest")

def call_gemini_api(text_prompt, filepaths=None):
    if not gemini_model:
        return "Gemini API не настроен."
    
    parts = [text_prompt]
    if filepaths:
        try:
            uploaded_files = [genai.upload_file(path) for path in filepaths]
            parts += uploaded_files
        except Exception as e:
            return f"Ошибка при загрузке файлов в Gemini: {str(e)}"
    
    response = gemini_model.generate_content(parts)
    return response.text


def ocr_image(image_path):
    creds = service_account.Credentials.from_service_account_file("test.json")
    vision = build('vision', 'v1', credentials=creds)

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    request_body = {
        "requests": [{
            "image": {"content": img_b64},
            "features": [
                {"type": "TEXT_DETECTION"},
                {"type": "LABEL_DETECTION", "maxResults": 5}
            ]
        }]
    }

    response = vision.images().annotate(body=request_body).execute()
    res = response['responses'][0]

    text = res.get("textAnnotations", [{}])[0].get("description", "")
    labels = [label['description'] for label in res.get("labelAnnotations", [])]
    labels_text = "Описание: " + ", ".join(labels)

    result = f"Текст картинки:\n{text}\n\n{labels_text}"
    return result
