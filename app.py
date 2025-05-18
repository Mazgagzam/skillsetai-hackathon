import os
import markdown
from flask import Flask, render_template, request, jsonify, send_from_directory

from models.model import anonymize_data
from PIL import Image
from google.cloud import vision
from werkzeug.utils import secure_filename

from gemini import call_gemini_api, ocr_image, gemini_model

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_docx_to_txt(docx_path):
    from docx import Document
    doc = Document(docx_path)
    txt_path = docx_path.rsplit('.', 1)[0] + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        for p in doc.paragraphs:
            f.write(p.text + '\n')
    return txt_path


@app.route('/')
def index():
    return render_template('index.html')




UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/send_message', methods=['POST'])
def send_message_route():
    files = request.files.getlist('file')
    text = request.form.get('text', '')

    if not files and not text.strip():
        return jsonify({'reply': 'Пожалуйста, отправьте текст или файлы.'}), 400

    results = []
    blurred_image_url = None  

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                ext = filename.rsplit('.', 1)[1].lower()
            except:
                ext = filename.lower()

            try:
                if ext == 'docx':
                    txt_path = convert_docx_to_txt(filepath)
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    anon_result = anonymize_data('text', content)

                elif ext in {'txt', 'md'}:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    anon_result = anonymize_data('text', content)

                elif ext in {'png', 'jpg', 'jpeg'}:
                    anon_result = anonymize_data(ext, filepath)

                    image = Image.open(filepath)
                
                    upload_dir = './uploads'
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    image.save(filepath)

                    blurred_image_url = f'./uploads/{filename}'
                    ocr_text = ocr_image(filepath)

                elif ext == 'pdf':
                    anon_result = "[Обработка PDF с OCR не реализована]"
                else:
                    anon_result = f"[Файл {filename} загружен, но обработка не реализована]"

                results.append(f"Файл {filename} (анонимизирован): {anon_result[:200]}...")
            except Exception as e:
                results.append(f"Ошибка при обработке файла {filename}: {str(e)}")
        else:
            results.append(f"Файл {file.filename} — недопустимый формат")

    if text.strip():
        try:
            anon_text = anonymize_data('text', text)
            results.append(f"Текст (анонимизирован): {anon_text[:200]}...")
        except Exception as e:
            results.append(f"Ошибка при обработке текста: {str(e)}")

    full_text = "\n\n".join(results)

    if not gemini_model:
        return jsonify({'reply': 'Gemini API не настроен.', 'success': False}), 500

    try:
        response = gemini_model.generate_content([ full_text ])
        gemini_markdown = response.text
        gemini_html = markdown.markdown(gemini_markdown)
    except Exception as e:
        return jsonify({'reply': f'Ошибка при вызове Gemini API: {str(e)}', 'success': False}), 500

    final_reply = (
        f"Анонимизированные данные:\n{full_text}\n\n"
        f"Ответ от Gemini:\n{gemini_html}"
    )

    return jsonify({
        'anonymizedHtml': markdown.markdown(full_text.replace('\n\n', '\n\n')), 
        'replyHtml': gemini_html,
        'blurredImageUrl': blurred_image_url,
        'success': True
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
