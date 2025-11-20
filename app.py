from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Notebook, Cell, Job, JobExecution
from spark_executor import SparkExecutor
from scheduler import JobScheduler
from datetime import datetime
import json

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Spark executor and scheduler
spark_executor = SparkExecutor(app.config)
job_scheduler = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Authentication routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            return redirect(url_for('dashboard'))
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        flash('Invalid username or password')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            flash('Username already exists')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    notebooks = Notebook.query.filter_by(user_id=current_user.id).order_by(Notebook.updated_at.desc()).all()
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.updated_at.desc()).all()
    return render_template('dashboard.html', notebooks=notebooks, jobs=jobs)


# Notebook routes
@app.route('/notebooks')
@login_required
def notebooks():
    notebooks = Notebook.query.filter_by(user_id=current_user.id).order_by(Notebook.updated_at.desc()).all()
    return render_template('notebooks.html', notebooks=notebooks)


@app.route('/notebooks/create', methods=['POST'])
@login_required
def create_notebook():
    data = request.get_json()
    name = data.get('name', 'Untitled Notebook')
    
    notebook = Notebook(
        name=name,
        user_id=current_user.id,
        content='# Welcome to your notebook\n\n# You can use Spark here\nprint("Hello, World!")\n'
    )
    db.session.add(notebook)
    db.session.flush()  # Get notebook ID
    
    # Create a default cell
    default_cell = Cell(
        notebook_id=notebook.id,
        cell_type='code',
        content='# Welcome to your notebook\n\n# You can use Spark here\nprint("Hello, World!")',
        position=0
    )
    db.session.add(default_cell)
    db.session.commit()
    
    return jsonify({'success': True, 'notebook_id': notebook.id})


@app.route('/notebooks/<int:notebook_id>')
@login_required
def notebook_view(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return "Unauthorized", 403
    return render_template('notebook_jupyter.html', notebook=notebook)


@app.route('/notebooks/<int:notebook_id>/get')
@login_required
def get_notebook(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all cells ordered by position
    cells = Cell.query.filter_by(notebook_id=notebook_id).order_by(Cell.position).all()
    
    # If no cells exist (legacy notebook), create one from content
    if not cells and notebook.content:
        cell = Cell(
            notebook_id=notebook.id,
            cell_type='code',
            content=notebook.content,
            position=0
        )
        db.session.add(cell)
        db.session.commit()
        cells = [cell]
    
    return jsonify({
        'id': notebook.id,
        'name': notebook.name,
        'language': notebook.language,
        'cells': [{
            'id': cell.id,
            'cell_type': cell.cell_type,
            'content': cell.content,
            'position': cell.position,
            'output': cell.output,
            'error': cell.error,
            'execution_count': cell.execution_count
        } for cell in cells]
    })


@app.route('/notebooks/<int:notebook_id>/save', methods=['POST'])
@login_required
def save_notebook(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    notebook.name = data.get('name', notebook.name)
    notebook.content = data.get('content', notebook.content)
    notebook.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/notebooks/<int:notebook_id>/execute', methods=['POST'])
@login_required
def execute_notebook(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    code = data.get('code', notebook.content)
    
    result = spark_executor.execute_code(code, notebook.language)
    return jsonify(result)


@app.route('/notebooks/<int:notebook_id>/delete', methods=['POST'])
@login_required
def delete_notebook(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(notebook)
    db.session.commit()
    
    return jsonify({'success': True})


# Cell routes
@app.route('/notebooks/<int:notebook_id>/cells/create', methods=['POST'])
@login_required
def create_cell(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    cell_type = data.get('cell_type', 'code')
    position = data.get('position')
    
    # If position not specified, add at end
    if position is None:
        max_position = db.session.query(db.func.max(Cell.position)).filter_by(notebook_id=notebook_id).scalar()
        position = (max_position or -1) + 1
    else:
        # Shift cells down to make room
        cells_to_shift = Cell.query.filter(
            Cell.notebook_id == notebook_id,
            Cell.position >= position
        ).all()
        for cell in cells_to_shift:
            cell.position += 1
    
    cell = Cell(
        notebook_id=notebook_id,
        cell_type=cell_type,
        content=data.get('content', ''),
        position=position
    )
    db.session.add(cell)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'cell': {
            'id': cell.id,
            'cell_type': cell.cell_type,
            'content': cell.content,
            'position': cell.position,
            'output': cell.output,
            'error': cell.error,
            'execution_count': cell.execution_count
        }
    })


@app.route('/cells/<int:cell_id>/update', methods=['POST'])
@login_required
def update_cell(cell_id):
    cell = Cell.query.get_or_404(cell_id)
    notebook = Notebook.query.get_or_404(cell.notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if 'content' in data:
        cell.content = data['content']
    if 'cell_type' in data:
        cell.cell_type = data['cell_type']
    
    cell.updated_at = datetime.utcnow()
    notebook.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/cells/<int:cell_id>/execute', methods=['POST'])
@login_required
def execute_cell(cell_id):
    cell = Cell.query.get_or_404(cell_id)
    notebook = Notebook.query.get_or_404(cell.notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if cell.cell_type != 'code':
        return jsonify({'success': True, 'output': '', 'error': ''})
    
    result = spark_executor.execute_code(cell.content, notebook.language)
    
    # Update cell with execution results
    cell.output = result.get('output', '')
    cell.error = result.get('error', '')
    if result.get('success'):
        cell.execution_count = (cell.execution_count or 0) + 1
    cell.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': result.get('success', False),
        'output': cell.output,
        'error': cell.error,
        'execution_count': cell.execution_count
    })


@app.route('/cells/<int:cell_id>/delete', methods=['POST'])
@login_required
def delete_cell(cell_id):
    cell = Cell.query.get_or_404(cell_id)
    notebook = Notebook.query.get_or_404(cell.notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    position = cell.position
    db.session.delete(cell)
    
    # Shift remaining cells up
    cells_to_shift = Cell.query.filter(
        Cell.notebook_id == cell.notebook_id,
        Cell.position > position
    ).all()
    for c in cells_to_shift:
        c.position -= 1
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/cells/<int:cell_id>/move', methods=['POST'])
@login_required
def move_cell(cell_id):
    cell = Cell.query.get_or_404(cell_id)
    notebook = Notebook.query.get_or_404(cell.notebook_id)
    if notebook.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    direction = data.get('direction')  # 'up' or 'down'
    
    if direction == 'up' and cell.position > 0:
        # Swap with cell above
        cell_above = Cell.query.filter_by(
            notebook_id=cell.notebook_id,
            position=cell.position - 1
        ).first()
        if cell_above:
            cell.position, cell_above.position = cell_above.position, cell.position
            db.session.commit()
            return jsonify({'success': True})
    elif direction == 'down':
        # Swap with cell below
        cell_below = Cell.query.filter_by(
            notebook_id=cell.notebook_id,
            position=cell.position + 1
        ).first()
        if cell_below:
            cell.position, cell_below.position = cell_below.position, cell.position
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Cannot move cell in that direction'})


# Job routes
@app.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.updated_at.desc()).all()
    notebooks = Notebook.query.filter_by(user_id=current_user.id).all()
    return render_template('jobs.html', jobs=jobs, notebooks=notebooks)


@app.route('/jobs/create', methods=['POST'])
@login_required
def create_job():
    data = request.get_json()
    name = data.get('name')
    notebook_id = data.get('notebook_id')
    schedule = data.get('schedule')
    
    job = Job(
        name=name,
        notebook_id=notebook_id,
        schedule=schedule,
        user_id=current_user.id,
        status='inactive'
    )
    db.session.add(job)
    db.session.commit()
    
    return jsonify({'success': True, 'job_id': job.id})


@app.route('/jobs/<int:job_id>/activate', methods=['POST'])
@login_required
def activate_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    job.status = 'active'
    db.session.commit()
    
    if job_scheduler:
        job_scheduler.add_job(job)
    
    return jsonify({'success': True})


@app.route('/jobs/<int:job_id>/deactivate', methods=['POST'])
@login_required
def deactivate_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    job.status = 'inactive'
    db.session.commit()
    
    if job_scheduler:
        job_scheduler.remove_job(job_id)
    
    return jsonify({'success': True})


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if job_scheduler:
        job_scheduler.remove_job(job_id)
    
    db.session.delete(job)
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/jobs/<int:job_id>/executions')
@login_required
def job_executions(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    executions = JobExecution.query.filter_by(job_id=job_id).order_by(JobExecution.started_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': e.id,
        'status': e.status,
        'output': e.output,
        'error': e.error,
        'started_at': e.started_at.isoformat() if e.started_at else None,
        'completed_at': e.completed_at.isoformat() if e.completed_at else None
    } for e in executions])


def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        
        # Create demo user if not exists
        if not User.query.filter_by(username='demo').first():
            demo_user = User(username='demo', email='demo@example.com')
            demo_user.set_password('demo')
            db.session.add(demo_user)
            db.session.commit()
            print("Created demo user (username: demo, password: demo)")


if __name__ == '__main__':
    init_db()
    
    # Initialize job scheduler
    job_scheduler = JobScheduler(app, app.config)
    job_scheduler.start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        job_scheduler.stop()
        spark_executor.close()
