import os
import random
import string
import base64
from io import BytesIO
from flask import Flask, render_template, request, session
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = os.urandom(24)


def generate_captcha():
    """Создает CAPTCHA и возвращает base64 изображение"""
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    session['captcha'] = text

    img = Image.new('RGB', (150, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    for i, char in enumerate(text):
        draw.text((10 + i * 25, 10), char, fill=(0, 0, 0))

    for _ in range(100):
        x = random.randint(0, 149)
        y = random.randint(0, 49)
        draw.point((x, y), fill=(random.randint(0,255),random.randint(0,255),random.randint(0,255)))

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def image_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def create_color_histogram(image):
    img = image.convert('RGB')
    np_img = np.array(img)

    fig, ax = plt.subplots(figsize=(8, 4))

    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        ax.hist(np_img[:, :, i].ravel(), bins=256, color=color, alpha=0.6, label=color.capitalize())

    ax.set_title('Распределение цветов')
    ax.set_xlabel('Яркость')
    ax.set_ylabel('Количество пикселей')
    ax.legend()

    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig)

    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@app.route('/')
def index():
    captcha_img = generate_captcha()
    return render_template('index.html', captcha_image=captcha_img)


@app.route('/process', methods=['POST'])
def process():
    user_captcha = request.form.get('captcha', '').upper()
    if user_captcha != session.get('captcha', ''):
        return render_template('index.html', error='Неверная CAPTCHA', captcha_image=generate_captcha())

    file = request.files.get('image')
    if not file:
        return render_template('index.html', error='Файл не выбран', captcha_image=generate_captcha())

    try:
        border_size = int(request.form.get('border_size', 10))
        border_size = max(1, min(100, border_size))

        border_color = request.form.get('border_color', '#000000')  # <-- получаем цвет из формы

        img = Image.open(file).convert('RGB')
        bordered_img = ImageOps.expand(img, border=border_size, fill=border_color)

        return render_template('result.html',
                               bordered_image=image_to_base64(bordered_img),
                               histogram=create_color_histogram(img))

    except Exception as e:
        return render_template('index.html', error=str(e), captcha_image=generate_captcha())

if __name__ == '__main__':
    app.run(debug=True)