import cv2
import pytesseract

def anonymize_image(image_path, output_path="anonymized.jpg"):
    img = cv2.imread(image_path)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6)
    for (x, y, w, h) in faces:
        face = img[y:y+h, x:x+w]
        img[y:y+h, x:x+w] = cv2.GaussianBlur(face, (99, 99), 30)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    n_boxes = len(data['level'])
    for i in range(n_boxes):
        (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        if w > 0 and h > 0:
            roi = img[y:y+h, x:x+w]
            img[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (25, 25), 10)

    cv2.imwrite(output_path, img)
