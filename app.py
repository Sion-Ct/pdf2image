from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for
from pdf2image import convert_from_path
import os
import zipfile
import uuid

app = Flask(__name__)

# 设置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 首页路由
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 检查是否有文件部分
        if 'file' not in request.files:
            return '没有选择文件'

        file = request.files['file']

        if file.filename == '':
            return '没有选择文件'

        if file:
            # 为每个上传创建唯一的文件夹
            session_id = str(uuid.uuid4())
            session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
            os.makedirs(session_folder)

            # 保存上传的PDF
            pdf_path = os.path.join(session_folder, file.filename)
            file.save(pdf_path)

            # 转换PDF为JPG
            images = convert_from_path(pdf_path)
            image_paths = []

            for i, image in enumerate(images):
                image_filename = f'page_{i + 1}.jpg'
                image_path = os.path.join(session_folder, image_filename)
                image.save(image_path, 'JPEG')
                image_paths.append(image_filename)

            return redirect(url_for('display_images', session_id=session_id))

    return render_template('index.html')

# 显示图片页面
@app.route('/images/<session_id>')
def display_images(session_id):
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    if not os.path.exists(session_folder):
        return '会话已过期或不存在'

    images = [f for f in os.listdir(session_folder) if f.endswith('.jpg')]
    return render_template('images.html', images=images, session_id=session_id)

# 提供单个图片下载
@app.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    return send_from_directory(session_folder, filename, as_attachment=True)

# 提供ZIP下载
@app.route('/download_zip/<session_id>')
def download_zip(session_id):
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    zip_path = os.path.join(session_folder, 'images.zip')

    # 创建ZIP文件
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(session_folder):
            for file in files:
                if file.endswith('.jpg'):
                    zipf.write(os.path.join(root, file), arcname=file)

    return send_file(zip_path, as_attachment=True)

# 提供图片预览
@app.route('/uploads/<session_id>/<filename>')
def uploaded_file(session_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], session_id), filename)

# 启动服务器
if __name__ == '__main__':
    app.run(debug=True)
