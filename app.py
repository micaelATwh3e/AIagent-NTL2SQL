from flask import Flask, render_template, request, jsonify
import io, base64
from engine import run_query

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

@app.route('/', methods=['GET'])
def index():
    return render_template('source.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.form.get('user_query')
    description, fig, typen = run_query(user_query)
    if typen.lower() == 'table':
        table_html = fig
        img_data = None
    else:
        buf = io.BytesIO()
        buf.write(fig)
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        table_html = None
    return jsonify({
        'user_query': user_query,
        'description': description.replace('\n', '<br>'),
        'table_html': table_html,
        'img_data': img_data
    })

if __name__ == '__main__':
    app.run(debug=True)