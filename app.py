from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pymysql
from flask_login import current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configuración de MySQL para SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dash_reports'
db = SQLAlchemy(app)

# Modelo de usuario
class User(db.Model):
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
            session['user_id'] = user.id
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
def dashboard():
    reports = Report.query.all()
    return render_template('dashboard.html', reports=reports)

# Crear un nuevo reporte
@app.route('/create_report', methods=['POST'])
def create_report():
    title = request.form.get('title')
    descripcion = request.form.get('descripcion')
    estado = request.form.get('estado')

    if not title or not descripcion or not estado:
        flash('Todos los campos son requeridos.', 'danger')
        return redirect(url_for('dashboard'))

    new_report = Report(title=title, descripcion=descripcion, estado=estado)
    db.session.add(new_report)
    db.session.commit()

    flash('Reporte creado exitosamente', 'success')
    return redirect(url_for('dashboard'))

# Ver todos los reportes
@app.route('/reportes')
def ver_reportes():
    # Actualizar el estado de los reportes y eliminar los que pasen los dos días
    actualizar_estado_reportes()

    reportes = Report.query.all()
    return render_template('ver_reportes.html', reports=reportes)

# Editar un reporte
@app.route('/report/update/<int:id>', methods=['GET', 'POST'])
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
def ver_detalle(id):
    reporte = Report.query.get_or_404(id)
    return render_template('detalle_reporte.html', reporte=reporte)

# Borrar un reporte
@app.route('/report/delete/<int:id>', methods=['POST'])
def eliminar_reporte(id):
    reporte = Report.query.get_or_404(id)

    db.session.delete(reporte)
    db.session.commit()
    flash('Reporte eliminado con éxito', 'success')
    return redirect(url_for('ver_reportes'))

# --- Sección adicional: Rutas para creación y visualización de reportes de usuarios ---

# Conexión a la base de datos para reportes de usuarios (pymysql)
def obtener_conexion():
    return pymysql.connect(host='localhost',
                           user='root',
                           password='',
                           db='dash_reports')

# Ruta para el formulario de creación de reportes (usuarios)
@app.route('/crear_reporte', methods=['GET', 'POST'])
def crear_reporte_usuario():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        estado = request.form['estado']  # Anteriormente "prioridad", ahora "estado" en tu DB
        usuario_id = current_user.id  # ID del usuario actual (asegúrate de que current_user esté disponible)

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # Insertar el reporte con el campo "usuario_id" y "creado_por" = 'Usuario'
            cursor.execute("""
                INSERT INTO reportes (titulo, descripcion, estado, creado_por, usuario_id)
                VALUES (%s, %s, %s, 'Usuario', %s)
            """, (titulo, descripcion, estado, usuario_id))
            conexion.commit()
        conexion.close()

        flash("¡Reporte enviado correctamente!", "success")
        return redirect(url_for('crear_reporte_usuario'))
    
    return render_template('crear_reporte.html')

# Ruta para ver reportes (solo admin)
@app.route('/ver_reportes_usuario')
def ver_reportes_usuario():
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        # Seleccionar todos los reportes creados por usuarios
        cursor.execute("""
            SELECT r.id, r.titulo, r.descripcion, r.estado, r.fecha_creacion, u.username 
            FROM reportes r 
            LEFT JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.creado_por = 'Usuario'
        """)
        reportes = cursor.fetchall()
    conexion.close()
    return render_template('ver_reportes.html', reportes=reportes)

# Inicializar la base de datos y ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
