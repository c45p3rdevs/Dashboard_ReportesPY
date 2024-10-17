from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configuración de MySQL
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
    descripcion = request.form.get('descripcion')  # asegúrate de tener este campo en tu formulario
    estado = request.form.get('estado')  # Recibe el valor del estado desde el formulario

    if not title or not descripcion or not estado:
        flash('Todos los campos son requeridos.', 'danger')
        return redirect(url_for('dashboard'))

    # Crear el nuevo reporte con los datos recibidos
    new_report = Report(title=title, descripcion=descripcion, estado=estado)

    # Agregar el nuevo reporte a la base de datos
    db.session.add(new_report)
    db.session.commit()

    flash('Reporte creado exitosamente', 'success')
    return redirect(url_for('dashboard'))


# Ver todos los reportes
@app.route('/reportes')
def ver_reportes():
    reportes = Report.query.all()
    return render_template('ver_reportes.html', reports=reportes)

# Editar un reporte
@app.route('/report/update/<int:id>', methods=['GET', 'POST'])
def editar_reporte(id):
    reporte = Report.query.get_or_404(id)  # Obtener el reporte

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado')

        if not titulo or not descripcion or not estado:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(request.url)

        # Actualizamos los valores del reporte
        reporte.title = titulo
        reporte.descripcion = descripcion
        reporte.estado = estado

        db.session.commit()
        flash('Reporte actualizado con éxito', 'success')
        return redirect(url_for('ver_reportes'))

    return render_template('editar_reporte.html', reporte=reporte)  # Pasamos "reporte" a la plantilla


@app.route('/report/<int:id>', methods=['GET'])
def ver_detalle(id):
    reporte = Report.query.get_or_404(id)  # Obtener el reporte
    return render_template('detalle_reporte.html', reporte=reporte)  # Asegúrate de pasar "reporte"

    
    # Renderizar una plantilla para mostrar los detalles del reporte
    return render_template('detalle_reporte.html', reporte=reporte)




# Borrar un reporte
@app.route('/report/delete/<int:id>', methods=['POST'])
def borrar_reporte(id):
    reporte = Report.query.get_or_404(id)
    db.session.delete(reporte)
    db.session.commit()
    flash('Reporte eliminado con éxito', 'success')
    return redirect(url_for('dashboard'))

@app.route('/report/delete/<int:id>', methods=['POST'])
def eliminar_reporte(id):
    # Obtener el reporte por ID
    reporte = Report.query.get_or_404(id)
    
    try:
        # Eliminar el reporte de la base de datos
        db.session.delete(reporte)
        db.session.commit()
        flash('Reporte eliminado con éxito', 'success')
    except Exception as e:
        flash(f'Error al eliminar el reporte: {str(e)}', 'danger')
    
    return redirect(url_for('ver_reportes'))


# Inicializar la base de datos y ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
      db.create_all()  # Crea las tablas si no existen
    app.run(debug=True)
