from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from charge_analyzer import process_csv, generate_video_html, compute_stats

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data')
REPORT_FOLDER = os.path.join(BASE_DIR, 'reports')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'csv' not in request.files:
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    csv_file = request.files['csv']
    device_model = request.form.get('model', 'Unknown').strip()

    if csv_file.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'}), 400

    if not csv_file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'error': '请上传 CSV 文件'}), 400

    filename = secure_filename(csv_file.filename)
    csv_path = os.path.join(UPLOAD_FOLDER, filename)
    csv_file.save(csv_path)

    try:
        data = process_csv(csv_path)

        if not data['timestamps']:
            return jsonify({'success': False, 'error': 'CSV 文件解析失败，未找到数据'}), 400

        stats = compute_stats(data)

        safe_model = ''.join(c for c in device_model if c.isalnum() or c in ' _-')

        report_name = f"{safe_model}_video.html"
        report_path = os.path.join(REPORT_FOLDER, report_name)
        generate_video_html(data, report_path, device_model, stats)

        return jsonify({
            'success': True,
            'report': report_name,
            'stats': {
                'data_points': len(data['timestamps']),
                'max_power': f"{stats['max_power']:.2f} W",
                'max_voltage': f"{stats['max_voltage']:.2f} V",
                'max_current': f"{stats['max_current']:.2f} A",
                'avg_voltage': f"{stats['avg_voltage']:.2f} V",
                'avg_current': f"{stats['avg_current']:.2f} A",
                'avg_power': f"{stats['avg_power']:.2f} W",
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/reports/<path:filename>')
def serve_report(filename):
    return send_from_directory(REPORT_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
