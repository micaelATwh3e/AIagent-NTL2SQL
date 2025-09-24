from flask import Flask, render_template, request, session
import io, base64
from engine import run_query

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'chat_history' not in session:
        session['chat_history'] = []
    chat_history = session['chat_history']

    if request.method == 'POST':
        user_query = request.form.get('user_query')
        if user_query:
            # Append user message
            chat_history.append({
                'is_user': True,
                'user_query': user_query,
                'description': '',
                'table_html': None,
                'img_data': None
            })
            # AI response
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
            # Append AI message
            chat_history.append({
                'is_user': False,
                'user_query': user_query,
                'description': description.replace('\n', '<br>'),
                'table_html': table_html,
                'img_data': img_data
            })
            session['chat_history'] = chat_history  # Update session

    return render_template('source.html', chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)
