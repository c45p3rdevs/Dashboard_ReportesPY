from flask import Flask, render_template, redirect, url_for, flash, session, request 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pymysql
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_login import UserMixin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configuración de MySQL para SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dash_reports'
db = SQLAlchemy(app)

# Inicializar LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirige a login si no está autenticado

# Modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Modelo de reporte
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), nullable=False)  # Activo, Medio, Crítico
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Cambiar a 'user'

    # Relación con la tabla User
    usuario = db.relationship('User', backref='reportes', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Función para actualizar el estado de los reportes
def actualizar_estado_reportes():
    now = datetime.utcnow()
    two_days_ago = now - timedelta(days=2)
    one_day_ago = now - timedelta(days=1)
    
    # Obtener todos los reportes
    reportes = Report.query.all()

    for reporte in reportes:
        # Si el reporte tiene más de 2 días, se elimina
        if reporte.created_at < two_days_ago:
            db.session.delete(reporte)
        # Si el reporte tiene entre 1 y 2 días, su estado cambia a "Crítico"
        elif reporte.created_at < one_day_ago:
            reporte.estado = "Crítico"
        # Si el reporte tiene menos de 1 día, su estado cambia a "Medio"
        else:
            reporte.estado = "Medio"
    
    # Aplicar los cambios a la base de datos
    db.session.commit()

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

# Ruta para registrar un usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso', 'danger')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Cuenta creada exitosamente', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Ruta del dashboard
@app.route('/dashboard')
@login_required  # Proteger la ruta con autenticación
def dashboard():
    reports = Report.query.all()
    return render_template('dashboard.html', reports=reports)

# Nueva ruta para el new_dashboard
@app.route('/new_dashboard')
@login_required  # Proteger la ruta con autenticación
def new_dashboard():
    reports = Report.query.all()
    return render_template('new_dashboard.html', reports=reports)

# Crear un nuevo reporte
@app.route('/create_report', methods=['POST'])
@login_required  # Proteger la ruta con autenticación
def create_report():
    title = request.form.get('title')
    descripcion = request.form.get('descripcion')
    estado = request.form.get('estado')

    if not title or not descripcion or not estado:
        flash('Todos los campos son requeridos.', 'danger')
        return redirect(url_for('dashboard'))

    # Verificar que el usuario actual existe
    if not User.query.get(current_user.id):
        flash('Usuario no encontrado. No se puede crear el reporte.', 'danger')
        return redirect(url_for('dashboard'))

    new_report = Report(title=title, descripcion=descripcion, estado=estado, usuario_id=current_user.id)
    db.session.add(new_report)
    db.session.commit()

    flash('Reporte creado exitosamente', 'success')
    return redirect(url_for('dashboard'))

# Ver todos los reportes
@app.route('/reportes')
@login_required  # Proteger la ruta con autenticación
def ver_reportes():
    # Actualizar el estado de los reportes y eliminar los que pasen los dos días
    actualizar_estado_reportes()

    reportes = Report.query.all()
    return render_template('ver_reportes.html', reports=reportes)

# Editar un reporte
@app.route('/report/update/<int:id>', methods=['GET', 'POST'])
@login_required  # Proteger la ruta con autenticación
def editar_reporte(id):
    reporte = Report.query.get_or_404(id)

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado')

        if not titulo or not descripcion or not estado:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(request.url)

        reporte.title = titulo
        reporte.descripcion = descripcion
        reporte.estado = estado

        db.session.commit()
        flash('Reporte actualizado con éxito', 'success')
        return redirect(url_for('ver_reportes'))

    return render_template('editar_reporte.html', reporte=reporte)

# Ver el detalle de un reporte
@app.route('/report/<int:id>', methods=['GET'])
@login_required  # Proteger la ruta con autenticación
def ver_detalle(id):
    reporte = Report.query.get_or_404(id)
    return render_template('detalle_reporte.html', reporte=reporte)

# Borrar un reporte
@app.route('/report/delete/<int:id>', methods=['POST'])
@login_required  # Proteger la ruta con autenticación
def eliminar_reporte(id):
    reporte = Report.query.get_or_404(id)

    db.session.delete(reporte)
    db.session.commit()
    flash('Reporte eliminado con éxito', 'success')
    return redirect(url_for('ver_reportes'))

# --- Sección adicional: Rutas para creación y visualización de reportes de usuarios ---

# Ruta para el formulario de creación de reportes (usuarios)
@app.route('/crear_reporte', methods=['GET', 'POST'])
@login_required  # Proteger la ruta con autenticación
def crear_reporte_usuario():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        estado = request.form['estado']  # El estado del reporte
        usuario_id = current_user.id  # ID del usuario actual

        new_report = Report(title=titulo, descripcion=descripcion, estado=estado, usuario_id=usuario_id)
        db.session.add(new_report)
        db.session.commit()

        flash("¡Reporte enviado correctamente!", "success")
        return redirect(url_for('crear_reporte_usuario'))
    
    return render_template('crear_reporte.html')

# Ruta para ver los reportes creados por los usuarios
@app.route('/ver_reportes_usuario')
@login_required  # Proteger la ruta con autenticación
def ver_reportes_usuario():
    reportes = Report.query.filter_by(usuario_id=current_user.id).all()
    return render_template('ver_reportes.html', reportes=reportes)

# Inicializar la base de datos y ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Esto creará todas las tablas si no existen
    app.run(debug=True)
