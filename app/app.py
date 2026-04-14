import os
import time
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Подключение к PostgreSQL
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'postgres')
db_pass = os.environ.get('DB_PASSWORD', 'password')
db_name = os.environ.get('DB_NAME', 'todos')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель для задачи
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }

# Создание таблиц
with app.app_context():
    db.create_all()

# Счётчик запросов (для метрик)
request_counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    global request_counter
    request_counter += 1
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    return jsonify([todo.to_dict() for todo in todos])

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    todo = Todo(title=data['title'])
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    
    if 'completed' in data:
        todo.completed = data['completed']
    if 'title' in data:
        todo.title = data['title']
    
    db.session.commit()
    return jsonify(todo.to_dict())

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted'})

@app.route('/metrics')
def metrics():
    return jsonify({
        'requests_total': request_counter,
        'todos_count': Todo.query.count(),
        'status': 'healthy'
    })

@app.route('/health')
def health():
    # Проверка соединения с БД
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)