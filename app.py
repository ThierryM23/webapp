from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

import os
import inspect
import logging
import datetime as dt

__author__ = "ThierryM23"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'B!1w8NAt1T^%kvhUI*S^'
# The absolute path of the directory containing images for users to download
app.config["CLIENT_IMAGES"] = APP_ROOT + "/static/images/gallery"
# The absolute path of the directory containing CSV files for users to download
app.config["CLIENT_CSV"] = APP_ROOT + "/static/csv"
# The absolute path of the directory containing PDF files for users to download
app.config["CLIENT_PDF"] = APP_ROOT + "/static/pdf"
# the absolute path para las fotos de los platos
app.config['UPLOAD_FOLDER'] = APP_ROOT + "/static/images/photos"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file_images(filename):
    # Define una función para verificar la extensión del archivo si es necesario
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGES

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Configurar el nivel de registro y el archivo de registro
log_level = logging.INFO  # Puedes ajustar el nivel según tus necesidades
log_file = 'app.log'  # Nombre del archivo de registro

# Crear un manejador de registro para escribir en el archivo
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(log_level)

# Crear un formato para el registro
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)

# Agregar el manejador de registro a la aplicación Flask
app.logger.addHandler(file_handler)
app.logger.setLevel(log_level)


# Definición de la tabla User
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.Integer)

    def __repr__(self):
        return '<Cliente: %r %r>' % (self.username, self.email)
    
    @staticmethod
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    @staticmethod
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Definición de la tabla Product
# Definir la clase "Product" que representa la tabla de productos
class Categorie(Enum):
    VALOR1 = 'Entrées'
    VALOR2 = 'Plats'
    VALOR3 = 'Fromages & Planches'
    VALOR4 = 'Desserts'
    VALOR5 = 'Coupes de glaces'

# Valores permitidos en el campo
categories = ['Entrées','Plats','Fromages & Planches', 'Desserts', 'Coupes de glaces']
# class TuModelo(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     campo_con_valores_definidos = db.Column(db.Enum(Categorie))

class Product(db.Model):
    __tablename__ = 'product'
    id          = db.Column(db.Integer, primary_key=True)
    idcat       = db.Column(db.Integer, nullable=False)
    titre       = db.Column(db.String(124), nullable=False)
    description = db.Column(db.String(256))
    prix        = db.Column(db.Numeric, nullable=False)
    image       = db.Column(db.String(128))
    categorie   = db.Column(db.String(128))
    ordercat    = db.Column(db.Integer)
        
    def __init__(self, idcat, titre, prix, description=None, image='fondo.png', categorie=None, ordercat=None ):
        self.idcat = idcat
        self.titre = titre
        self.prix = prix      
        self.description = description
        self.image = image
        self.categorie = categorie
        self.ordercat =  ordercat        

    # Función para guardar un nuevo producto en la base de datos
    def save(self):
        app.logger.info(self.id)
        if not self.id:
            db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def read(cls, product_id):
        return cls.query.get(product_id)
    
    # Función para leer todos los productos de la base de datos
    @classmethod
    def read_all(cls):
        return cls.query.all()
        
    @staticmethod
    def get_by_id(id):
        return Product.query.get(id)
    @staticmethod
    def get_by_categorie(categorie):
        return Product.query.filter_by(categorie=categorie).all()

class Menudia(db.Model):
    __tablename__ = "menu_dia" 
    id                  = db.Column(db.Integer, primary_key=True)
    titre               = db.Column(db.String(124), nullable=False)
    description         = db.Column(db.String(256))
    prix                = db.Column(db.Numeric, nullable=False)
    image               = db.Column(db.String(128))
    categorie           = db.Column(db.String(128))
    ordercat            = db.Column(db.Integer)
    fecha_created       = db.Column(db.String(80))
    fecha_presentacion  = db.Column(db.String(80))
    fecha_fin           = db.Column(db.String(80))
    
    def __init__(self,  titre, prix, description=None, image='fondo.png', categorie=None, ordercat=None, fecha_created=dt.datetime.today(), fecha_presentacion='', fecha_fin='' ):
        self.titre = titre
        self.prix = prix      
        self.description = description
        self.image = image
        self.categorie = categorie
        self.ordercat =  ordercat
        self.fecha_created = fecha_created
        self.fecha_presentacion = fecha_presentacion
        self.fecha_fin = fecha_fin
    
    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
        
    @staticmethod
    def entrefecha(fecha):
        
        return Product.query.get(id)

#busca en la tabla menu del dia los platos entre fecha_presentacion y fecha_fin
def listamenudia():
    fecha_actual = dt.datetime.today()
    app.logger.info(fecha_actual)
    resultados = Menudia.query.filter(db.and_(Menudia.fecha_presentacion <= fecha_actual, Menudia.fecha_fin >= fecha_actual)).all()
    app.logger.info(len(resultados))
    # Imprimir los resultados
    #for resultado in resultados:
    #    app.logger.info(f"ID: {resultado.id},Titre: {resultado.titre}, Descrip: {resultado.description}, Fecha Presentación: {resultado.fecha_presentacion}, Fecha Fin: {resultado.fecha_fin}")
        #flash(f"ID: {resultado.id},Titre: {resultado.titre}, Descrip: {resultado.description}, Fecha Presentación: {resultado.fecha_presentacion}, Fecha Fin: {resultado.fecha_fin}", "alert-success")
    return resultados

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form.to_dict()
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        app.logger.info(user)        
        #if user and user.check_password(password):
        if user and user.password_hash == data['password']:
            login_user(user)
            app.logger.info("login Success")
            flash('Vous êtes connecté!','alert-success')
            return redirect(url_for('home'))
        flash('vous n''êtes pas autorisé!','alert-success')
        app.logger.info("login failed")
        return redirect(url_for('home'))
    return redirect(url_for('home'))        

@app.route('/logout')
@login_required
def logout():
    logout_user()
    app.logger.info("logout")
    return redirect(url_for('home')) #render_template("home.html", titulo="Bienvenue")

@app.route('/products')
@login_required
def products():
    user_id = current_user.id
    user_products = Product.query.filter_by(user_id=user_id).all()
    return render_template('products.html', products=user_products)

@app.route('/')
def home():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    registros = listamenudia()
    if len(registros) == 0:
        registro = Menudia("Menu du jour á ", 16, "Consultez nos serveuses, elles se feront un plaisir de vous renseigner")
        registros.append(registro)
    #return "Bienvenue"
    return render_template("home.html", titulo="Bienvenue", registros=registros)

@app.route('/about')
def about():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    titulo: str = "About Page"
    return render_template('about.html', titulo="Le mot du chef", bg_image="modif-2.jpeg")

@app.route('/location')
def locate():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    return render_template("location.html", titulo="Bienvenue", bg_image="stEtienne1.jpg")

@app.route('/upload/<filename>')
def send_image(filename):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion send_image")
    app.logger.info(filename)
    #filename = filename.replace(" ","_")
    #filename = filename.replace("'","_")
    #app.logger.info(filename)
    try:
        return send_from_directory(app.config["CLIENT_IMAGES"], filename)
    except FileNotFoundError:
        abort(404)

@app.route('/upload', methods=['POST'])
def upload():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion upload")
    target = app.config["CLIENT_IMAGES"]
    app.logger.info(target)
    
    if not os.path.isdir(target):
        os.mkdir(target)
    app.logger.info(request.files.getlist("file"))
    for upload in request.files.getlist("file"):
        print(upload)
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        # This is to verify files are supported
        ext = os.path.splitext(filename)[1]
        if (ext == ".jpg") or (ext == ".png") or (ext == ".jpeg"):
            app.logger.info("File supported moving on...")
           
            destination = "/".join([target, filename])            
            app.logger.info("Accept incoming file:", filename)
            app.logger.info("Save it to:", destination)
            upload.save(destination)
        else:
            app.logger.info("Files uploaded are not supported...")

    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("gallery.html", func='upload', image_name=filename)

@app.route('/gallery')
def get_gallery():
    # Directorio de imágenes
    image_directory = os.path.join(app.root_path, 'static/images/gallery')
    # Obtener la lista de archivos en el directorio
    images = [os.path.join('/static/images/gallery', file) for file in os.listdir(image_directory) if file.endswith(('.jpg', '.png', '.jpeg'))]

    return render_template('galeria1.html', titulo="Gallery Page", func='gallery', images=images)

@app.route('/galerie')
def galerie():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion get_gallery")
    print(APP_ROOT)
    print(os.path)
    print(os.listdir(APP_ROOT + '/static/images/gallery'))

    image_names = os.listdir(APP_ROOT + '/static/images/gallery')
    return render_template('gallery.html', titulo="Gallery Page", func='gallery', image_names=image_names)

@app.route('/add_gallery', methods=['POST'])
def add_gallery():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion add_gallery")
    if request.method == 'POST':
        action = request.form['btn']
        print(action)
        data = request.form.to_dict()
        print(data)
        if action == 'cancel':
            destination = 'static/images/gallery/' + data["filename"]
            app.logger.info(destination)
            os.remove(destination)
            print('borrar el archivo')
            #cargar las imagene 
            image_names = os.listdir(APP_ROOT + '/static/images/gallery')
        else:
            app.logger.info("funccion add_gallery boton ok")
            app.logger.info("Guardar el archivo")
            image_directory = os.path.join(app.root_path, 'static/images/gallery')
            # Obtener la lista de archivos en el directorio
            images = [os.path.join('/static/images/gallery', file) for file in os.listdir(image_directory) if file.endswith(('.jpg', '.png', '.jpeg'))]
    return render_template('galeria1.html', titulo="Gallery Page", func='gallery', images=images)

@app.route('/menuqr', methods=['GET', 'POST'])
def menuqr():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    #results = []
    #registros =Product.read_all()
    registros = Product.query.order_by(Product.ordercat.asc()).all()
    #app.logger.info(registros)
    return render_template('menuqr.html', resultados=registros)
    
@app.route('/carta')
@login_required
def carta():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    registros = Product.read_all()
    app.logger.info(type(registros))
    registros_dict = [registro.__dict__ for registro in registros]
     # Elimina la clave '_sa_instance_state' que no es necesaria
    for registro in registros_dict:
        del registro['_sa_instance_state']
        
    return render_template("carta.html", titulo="Bienvenue", results=registros_dict)

@app.route('/newplat', methods=['POST'])
def newplat():    
    if request.method == "POST": 
        nombre_funcion = inspect.currentframe().f_code.co_name
        app.logger.info(nombre_funcion)
        data = request.form.to_dict()
        app.logger.info(data)        
        if data['categorie'] == "Entrées": order = 1
        if data['categorie'] == "Plats": order = 2 
        if data['categorie'] == "Fromages & Planches": order = 3 
        if data['categorie'] == "Desserts": order = 4 
        if data['categorie'] == "Coupes de glaces": order = 5 
        
        nomplat = data["titre"].replace("'","''")
        descrip = data['descripcion'].replace("'","''")
        product_new = Product(int(data['idcat']), nomplat, float(data['prix']),descrip, 'fondo.png', data['categorie'], int(order))
        app.logger.info(product_new)
        db.session.add(product_new) # Agregar objeto a la solicitud
        db.session.commit() 
        app.logger.info(product_new)
        return redirect(url_for('carta'))
    return redirect(url_for('carta'))

@app.route('/carta_up/<string:id>', methods=['GET', 'POST'])
def carta_up(id):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info(id)    
    data = request.form.to_dict()
    app.logger.info(data)
    app.logger.info("******** inicio de la funcion carta_up <string:id> " + id + " accion:  *************")
    if 'accion' not in data:
        flash('Essayez de nouveau','alert-danger')
        return redirect(url_for('carta'))
    else:
        if data['accion'] == 'upload':
            fichier = request.files['archivo']
            app.logger.info("******** POST  Accion = Upload   *************")
            app.logger.info(fichier.filename)
            if fichier.filename == '':
                flash('Nom de l image vide !','alert-danger')
                return redirect(request.url)

            if fichier and allowed_file_images(fichier.filename):
                # Genera un nuevo nombre de archivo para evitar conflictos
                fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], fichier.filename))
                sql = "UPDATE product SET image = '" + fichier.filename + "' WHERE product.id=" + id   
                app.logger.info(fichier.filename) 
                app.logger.info(sql) 
                producto_up = Product.get_by_id(id)
                producto_up.image = fichier.filename # Modificar objeto
                app.logger.info(producto_up) 
                db.session.add(producto_up) # Agregar objeto a la solicitud
                db.session.commit() # Hacer commit a la solicitud
                app.logger.info("actualizado el campo de image en la base por el product " + id) 
                flash('Image ajoutée !','alert-success')
            else:
                app.logger.info("Image refoule pour format incorrect ! ")
                flash('Image refoule pour format incorrect !','alert-danger')
            
        elif data['accion']=='save':
            app.logger.info("******** carta_up <string:id> " + id + "  POST  Accion = save   *************")
            app.logger.info(request.files)
            nombre_image = data["nombre_archivo"]
            app.logger.info("nombre archivo = " + nombre_image)
            app.logger.info("******** carta_up  POST   save  *************")                
            if data['categorie'] == "Entrées": order = 1
            if data['categorie'] == "Plats": order = 2 
            if data['categorie'] == "Fromages & Planches": order = 3 
            if data['categorie'] == "Desserts": order = 4 
            if data['categorie'] == "Coupes de glaces": order = 5   
            
            nomplat = data["titre"].replace("'"," ")
            descrip = data['descripcion'].replace("'"," ")   
            app.logger.info(nomplat)  
            app.logger.info(descrip)
            producto_up = Product.get_by_id(id)
            app.logger.info(producto_up)
            producto_up.id = int(id)
            producto_up.idcat = int(data['idcat'])
            producto_up.titre = nomplat
            producto_up.description = descrip
            producto_up.prix=float(data['prix'])
            producto_up.categorie = data['categorie']
            producto_up.ordercat = int(order)
            producto_up.image = nombre_image
            app.logger.info(producto_up)
            db.session.add(producto_up) # Agregar objeto a la solicitud
            db.session.commit() # Hacer commit a la solicitud
            # db.session.add(product_up) # Agregar objeto a la solicitud
            # db.session.commit()
            app.logger.info("******** carta_up <string:id>  POST  Accion = save  FIN *************")
            return redirect(url_for('carta'))
            
        elif data['accion']=='Delete':
            app.logger.info("******** carta_up <string:id>  POST  Accion = Delete   *************")       
            producto = Product.query.get(id) 
            app.logger.info(producto)
            db.session.delete(producto)
            db.session.commit()
            app.logger.info(" se borro el registro numero " + id)
            app.logger.info("******** carta_up <string:id>  POST  Accion = delete  fin  *************")
            return redirect(url_for('carta'))  
        else:
            return redirect(request.url)
    
    return redirect(url_for('carta'))
     
@app.route('/subir_foto/<string:id>', methods=['POST'])
def subir_foto(id):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info(" subir_ foto con id=")
    app.logger.info(id)
    if 'archivo' not in request.files:
        return redirect(request.url)

    archivo = request.files['archivo']

    if archivo.filename == '':
        return redirect(request.url)

    if archivo and allowed_file(archivo.filename):
        # Genera un nuevo nombre de archivo para evitar conflictos
        nuevo_nombre = 'nuevo_nombre' + os.path.splitext(archivo.filename)[1]
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre))
        return 'Archivo subido exitosamente como {}'.format(nuevo_nombre)

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    hoy = dt.date.today()
    hoy.strftime('%Y-%m-%d')
    app.logger.info(hoy)
    if request.method == "POST":
        data = request.form.to_dict()
        menu_hoy = Menudia(titre=data['titre'], description=data['description'], prix=float(data['prix']), image='', categorie=data['categorie'], fecha_created = hoy, fecha_presentacion = data['fecha_presentacion']  +  ' 00:00:01', fecha_fin = data['fecha_fin'] +  ' 23:59:59')
        app.logger.info(menu_hoy)
        menu_hoy.save()
        flash("Menu du jour sauvegarder ", "alert-success")
    #results = []
    #registros =Product.read_all()
    #registros = Product.query.order_by(Product.ordercat.asc()).all()
    #app.logger.info(registros)
    return render_template('menu.html',hoy=hoy.strftime('%Y-%m-%d'))
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        user1 = User("Thierry","nono")
        db.session.add(user1)
        db.session.commit()
    app.run()
    