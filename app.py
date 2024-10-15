from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


#hastaaqui


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'




# Configuración de MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dash_reports'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso', 'danger')
        else:
            # Crear un nuevo usuario con un hash de contraseña seguro
            new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Cuenta creada exitosamente', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    reports = Report.query.all()  # Obtener todos los reportes
    return render_template('dashboard.html', reports=reports)

@app.route('/create_report', methods=['POST'])
def create_report():
    title = request.form['title']
    new_report = Report(title=title)
    db.session.add(new_report)
    db.session.commit()
    flash('Reporte creado exitosamente', 'success')
    return redirect(url_for('dashboard'))

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Modelo de reporte
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Nuevo')  # Nuevo, En progreso, Fuera de tiempo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Rutas de la aplicación (login, dashboard, etc.)

# Inicialización de la base de datos al iniciar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    app.run(debug=True)
