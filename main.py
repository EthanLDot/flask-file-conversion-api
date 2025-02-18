from flask import Flask, request, jsonify, send_file, send_from_directory
from fpdf import FPDF
import os, time
from flasgger import Swagger
import awsgi

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3
}

swagger = Swagger(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def index():
    """
    API home
    ---
    responses:
      200:
        description: Welcome message
    """
    return 'Welcome to the File Conversion API!'


@app.route('/txtpdf', methods=['POST'])
def text_to_pdf():
    """
    Convert uploaded text files to PDFs
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: files
        in: formData
        type: file
        required: true
        description: Upload one or more .txt files
    responses:
      200:
        description: Upload successful, returns processing time
      400:
        description: Bad request (e.g., no files provided, invalid file type)
    """
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in request'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    start_time = time.time()
    for file in files:
        if file.filename == '' or not file.filename.endswith('.txt'):
            continue
        file_start_time = time.time()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        pdf = FPDF(orientation="p", format="A4")
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        
        for line in lines:
            pdf.multi_cell(200, 10, txt=line.strip().encode('latin-1', 'replace').decode('latin-1'))
        
        pdf_filename = file.filename.rsplit('.', 1)[0] + ".pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf.output(pdf_path)
        print(str(time.time() - file_start_time) + 's')
    time_elapsed = time.time() - start_time
    print("Request complete")
    print(str(time_elapsed) + 's')
    return jsonify({'message': 'Upload successful', 'time_elapsed': time_elapsed}), 200

def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png"})

if __name__ == '__main__':
    app.run(debug=True)