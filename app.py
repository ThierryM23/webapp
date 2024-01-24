from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from enum import Enum

import os
import inspect
import logging
import datetime as dt
import boto3
import s3upload as s3
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_user = os.getenv('DB_USER')
db_clave = os.getenv('DB_CLAVE')
db_base = os.getenv('DB_BASE')


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
app.config['GENERAL_FOLDER'] = APP_ROOT + "/static/images"

basedir = os.path.abspath(os.path.dirname(__file__))
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
#= os.getenv('DB_BASE')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file_images(filename):
    # Define una función para verificar la extensión del archivo si es necesarioa
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGES

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#Logging
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
    __tablename__   = 'users'
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80), unique=True, nullable=False)
    email           = db.Column(db.String(120))
    password_hash   = db.Column(db.String(256), nullable=False)
    tipo            = db.Column(db.Integer)  # 1 para admin y 2 para cliente
    telefono        = db.Column(db.String(120))
    instagram       = db.Column(db.String(120))
    facebook        = db.Column(db.String(120))
    password        = db.Column(db.String(120))
    
    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash   
    
    def __repr__(self):
        return '<Cliente: %r %r>' % (self.username, self.email)
    
    def save(self):
        app.logger.info(self.id)
        if not self.id:
            db.session.add(self)
        try:
            db.session.commit()
            app.logger.info("Commit User perfecto {0}".format(self))
            #flash("Commit TextoxPagina perfecto {0}".format(self), "alert-success")
        except Exception as err:
            app.logger.info(f"User Unexpected {err=}, {type(err)=}")
            flash(f"User Unexpected {err=}, {type(err)=}", "alert-success")

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
    prix        = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
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
        try:
            db.session.commit()
            app.logger.info("Commit Product perfecto {0}".format(self))
            #flash("Commit TextoxPagina perfecto {0}".format(self), "alert-success")
        except Exception as err:
            app.logger.info(f"Product Unexpected {err=}, {type(err)=}")
            flash(f"Product Unexpected {err=}, {type(err)=}", "alert-success")

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def read(cls, product_id):
        return cls.query.get(product_id)   
    # Función para leer todos los productos de la base de datos
    @classmethod
    def read_all(cls):
        return cls.query.order_by(cls.ordercat, cls.idcat).all()        #el order
    @staticmethod
    def get_by_id(id):
        return Product.query.get(id)
    @staticmethod
    def get_by_categorie(categorie):
        return Product.query.filter_by(categorie=categorie).all()

class Menudia(db.Model):
    __tablename__       = "menu_dia" 
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
        try:
            db.session.commit()
            app.logger.info("Commit MenuDia perfecto {0}".format(self))
            #flash("Commit TextoxPagina perfecto {0}".format(self), "alert-success")
        except Exception as err:
            app.logger.info(f"Menudia Unexpected {err=}, {type(err)=}")
            flash(f"Unexpected {err=}, {type(err)=}", "alert-success")

class TextoXpagina(db.Model):
    __tablename__       = "textoxpagina" 
    id                  = db.Column(db.Integer, primary_key=True)
    pagina              = db.Column(db.String, nullable=False)
    seccion             = db.Column(db.Integer, nullable=False)
    orden               = db.Column(db.Integer, nullable=False)
    titulo              = db.Column(db.String)
    texto               = db.Column(db.String)
    fecha_created       = db.Column(db.String(80))
    image               = db.Column(db.String)
   
    def __init__(self, pagina, seccion, orden, fecha_created=dt.datetime.today() ):
        self.pagina = pagina
        self.seccion = seccion      
        self.orden = orden
        self.fecha_created = fecha_created
        
    def save(self):
        if not self.id:
            db.session.add(self)
        try:
            db.session.commit()
            app.logger.info("Commit TextoxPagina perfecto {0}".format(self))
            #flash("Commit TextoxPagina perfecto {0}".format(self), "alert-success")
        except Exception as err:
            app.logger.info(f"textoxpagina Unexpected {err=}, {type(err)=}")
            flash(f"Unexpected {err=}, {type(err)=}", "alert-success")
        
    @staticmethod
    def get_orden(page, seccion):
        return TextoXpagina.query.filter_by(pagina=page, seccion=seccion).order_by(TextoXpagina.orden.desc()).first()

#busca en la tabla menu del dia los platos entre fecha_presentacion y fecha_fin
def listamenudia(tipo: int = 0):
    fecha_actual = dt.datetime.today()
    str_fecha_hora = fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
    str_fecha = fecha_actual.strftime("%Y-%m-%d")
    app.logger.info(fecha_actual)
    if tipo == 1:
        resultados = Menudia.query.filter(Menudia.fecha_fin >= str_fecha).all()
        app.logger.info(len(resultados))
    else:
        resultados = Menudia.query.filter(db.and_(Menudia.fecha_presentacion <= str_fecha_hora, Menudia.fecha_fin >= str_fecha_hora)).all()
        app.logger.info(len(resultados))
        
    return resultados

def textoxpage(page):
    app.logger.info(page)
    resultados = TextoXpagina.query.filter(TextoXpagina.pagina == page).order_by(TextoXpagina.seccion).all()
    app.logger.info(len(resultados))
    return resultados



with app.app_context():
    db.create_all()


"""
*************************************************************
Routes
*************************************************************

"""

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    if request.method == 'POST':
        data = request.form.to_dict()
        app.logger.info(data)
        username = request.form['username']
        password = request.form['password']
        passwordhash = generate_password_hash( password, method='pbkdf2:sha256')
        newuser= User( request.form['username'], request.form['email'],  passwordhash)
        newuser.telefono = request.form['telefono']
        newuser.instagram = request.form['instagram']
        newuser.facebook = request.form['facebook']
        newuser.password = password
        newuser.tipo = 2
        vrai = check_password_hash(passwordhash, password)
        print ("el valor de la variable vrai = " + str(vrai))
        app.logger.info("el valor de la variable vrai = " + str(vrai))
        if "admin" in data: 
            if request.form['admin'] == "1":
                newuser.tipo = 1
        #user = User.query.filter_by(username=username).first()
        app.logger.info(newuser)   
        try:
            User.save(newuser)
            app.logger.info(newuser) 
            flash("Vous etes enregistrer {0}".format(newuser.username), "alert-success")
        except Exception as err:
            app.logger.info(f"Unexpected {err=}, {type(err)=}")
            flash(f"Unexpected {err=}, {type(err)=}","alert-warning")
             
        
    return redirect(url_for('home'))      

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    if request.method == 'POST':
        data = request.form.to_dict()
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        app.logger.info(user)        
        #if user and user.check_password(password):
        if user and check_password_hash(user.password_hash , password):
        #if user and user.password_hash == data['password'] :
            if user.tipo == 1 :
                login_user(user)
                app.logger.info("login Success")
                flash('Vous êtes connecté comme administrateur!','alert-success')
                return redirect(url_for('home'))
            else:
                flash('Vous êtes enregistré!','alert-success')
                return redirect(url_for('home'))
        flash('vous n''êtes pas autorisé!','alert-warning')
        app.logger.info("login failed")
        return redirect(url_for('home'))
    return redirect(url_for('home'))        

@app.route('/logout')
@login_required
def logout():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    logout_user()
    app.logger.info("logout")
    return redirect(url_for('home'))

@app.route('/userlist')
@login_required
def userlist():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    users = User.query.all()
    app.logger.info(users)
    return render_template('userlist.html', users=users)


@app.route('/products')
@login_required
def products():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    user_id = current_user.id
    user_products = Product.query.filter_by(user_id=user_id).all()
    return render_template('products.html', products=user_products)

"""@app.route('/favicon.ico')
def favicon():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    pass
"""

@app.route('/')
def home():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    registros = listamenudia()
    app.logger.info(registros)
    if len(registros) == 0:
        registro = Menudia("Menu du jour á ", 16, "Consultez nos serveuses, elles se feront un plaisir de vous renseigner")
        registros.append(registro)
    
    results = textoxpage('home')
    app.logger.info(results)
    if len(results) == 0: # no deberia entrar aca nunca ###################################
        app.logger.info("NO encontro texto por esta pagina")
        result = TextoXpagina('home',1,1) 
        result.id = 1
        result.titulo = "Suivez le guide pour nous rejoindre!!"
        result.texto = "+33 6 15 08 90 39 à Saint etienne de Crossey"
        result.image="stEtienne1.jpg"
        bg_image="stEtienne1.jpg"
        results.append(result)       
    else:
        app.logger.info(results)       
        app.logger.info(results[0].titulo)
        app.logger.info(results[0].texto)
        bg_image = results[0].image
    
    app.logger.info(bg_image)
    app.logger.info("fin home")
    return render_template("home.html", titulo="Bienvenue", registros=registros, results=results, bg_image=bg_image)

@app.route('/about')
def about():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    results = textoxpage('about')
    if len(results) == 0:
        app.logger.info("NO encontro texto por esta pagina")
        result = TextoXpagina('about',1,1, "Le mot du chef","""Le chef Bruno Narici et son équipe vous accueillent dans son établissement, du mardi au dimanche midi, afin de vous faire découvrir sa cuisine traditionnelle de terroir composée principalement de produits frais de la région.
        La carte change au fil des saisons. Le chef vous propose également tous les dimanches midi, cuisses de grenouilles et gratin dauphinois, pensez à réserver. Nous vous souhaitons un agréable moment à l'Auberge Refleurie.""")
        results.append(result)
        titulo: str = "Le mot du chef"
    else:
        app.logger.info(results)       
        app.logger.info(results[0].titulo)
        app.logger.info(results[0].texto)
        titulo: str = results[0].titulo
        bg_image = results[0].image
    app.logger.info(results[0].titulo)
    app.logger.info("fin About")
    return render_template('about.html', titulo=titulo, bg_image=bg_image, results=results)

@app.route('/about/<string:id>', methods=['POST'])
def formabout(id):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info(id)    
    data = request.form.to_dict()
    app.logger.info(data)
    app.logger.info("******** inicio de la funcion formabout <string:id> " + id + " accion:  *************")
    if 'accion' not in data:
        flash('Essayez de nouveau','alert-danger')
    else:
        if data['accion'] == 'add':
            app.logger.info("Accion = add " + str(id) )
            texto = TextoXpagina.query.get(id)
            num=TextoXpagina.get_orden(texto.pagina, texto.seccion)
            numero = num.orden + 1
            app.logger.info(numero)
            textonew = TextoXpagina(texto.pagina, texto.seccion, orden = numero)
            TextoXpagina.save(textonew)
            app.logger.info(textonew.pagina + str(textonew.id))
            app.logger.info("Accion = add FIN ")
            flash('add' + texto.pagina + str(texto.seccion) + str(numero),'alert-danger')
        elif data['accion'] == 'del':
            texto = TextoXpagina.query.get(id)
            db.session.delete(texto)
            db.session.commit()
            flash('Del','alert-danger')
        elif data['accion'] == 'edit':
            texto = TextoXpagina.query.get(id)
            app.logger.info(texto)
            texto.titulo = data['titulo']
            texto.texto = data['texto']
            TextoXpagina.save(texto)            
            flash('edit','alert-danger')
        elif data['accion'] == 'upload':
            fichier = request.files['archivo']
            app.logger.info("******** POST  def FormAbout Accion = Upload   *******")
            app.logger.info(fichier.filename)
            if fichier.filename == '':
                flash('Nom de l image vide !','alert-danger')
                return redirect(request.url)

            if fichier and allowed_file_images(fichier.filename):
                # Genera un nuevo nombre de archivo para evitar conflictos
                fichier.save(os.path.join(app.config['GENERAL_FOLDER'], fichier.filename))  
                nombre_destino = 'general/' + fichier.filename
                nombre_origen = 'static/images/' + fichier.filename
                app.logger.info(fichier.filename) 
                texto = TextoXpagina.query.get(id)                
                texto.image = fichier.filename # Modificar objeto
                app.logger.info(texto)
                db.session.add(texto) # Agregar objeto a la solicitud
                db.session.commit() # Hacer commit a la solicitud                
                s3.upload_file(nombre_origen,'myappauberge',nombre_destino)
                app.logger.info("actualizado el campo de image en la base por el product " + id) 
                flash('Image ajoutée !','alert-success')
            else:
                app.logger.info("Image refoule pour format incorrect ! ")
                flash('Image refoule pour format incorrect !','alert-danger')
        else:
            flash('else','alert-danger')
        return redirect(url_for(texto.pagina))
    return redirect(url_for(texto.pagina))    


@app.route('/location')
def location():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    results = textoxpage('location')
    if len(results) == 0:
        app.logger.info("NO encontro texto por esta pagina")
        result = TextoXpagina('location',1,1) 
        result.id = 1
        result.titulo = "Suivez le guide pour nous rejoindre!!"
        result.texto = "+33 6 15 08 90 39 à Saint etienne de Crossey"
        result.image="stEtienne1.jpg"
        bg_image="stEtienne1.jpg"
        results.append(result)
        titulo: str = "Suivez le guide pour nous rejoindre!!"
        
    else:
        app.logger.info(results)       
        app.logger.info(results[0].titulo)
        app.logger.info(results[0].texto)
        titulo: str = results[0].titulo
        bg_image = results[0].image 
    return render_template("location.html", titulo="Bienvenue", bg_image=bg_image, results=results)

@app.route('/upload/<filename>')
def send_image(filename):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion send_image")
    app.logger.info(filename)
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
        #ext = os.path.splitext(filename)[1]
        if allowed_file_images(filename):
        #if (ext == ".jpg") or (ext == ".png") or (ext == ".jpeg"):
            app.logger.info("File supported moving on...")
            destination = "/".join([target, filename])            
            app.logger.info("Accept incoming file: %s ", filename)
            app.logger.info("Save it to: %s ", destination)
            upload.save(destination)
            
        else:
            app.logger.info("Files uploaded are not supported...")

    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("galeria1.html", func='upload', image_name=filename)

@app.route('/gallery')
def get_gallery():
    results = textoxpage('get_gallery')
    if len(results) == 0:
        app.logger.info("NO encontro texto por esta pagina")
        result = TextoXpagina('get_gallery',1,1)         
        result.titulo = "titulo no usado"
        result.texto = "texto no usado"
        result.image="Auberge-devant.jpg"
        bg_image="Auberge-devant.jpg"
        TextoXpagina.save(result)
        results = textoxpage('get_gallery')
        results.append(result)        
    else:
        app.logger.info(results)       
        app.logger.info(results[0].titulo)
        app.logger.info(results[0].texto)
        titulo: str = results[0].titulo
        bg_image = results[0].image 
    images = s3.listar('myappauberge','gallery')
    return render_template('galeria1.html', titulo="Gallery Page", func='gallery', images=images, bg_image=bg_image, results=results)

@app.route('/galerie')
def galerie():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info("funccion get_gallery")
    print(APP_ROOT)
    print(os.path)
    print(os.listdir(APP_ROOT + '/static/images/gallery'))

    #image_names = os.listdir(APP_ROOT + '/static/images/gallery')
    image_names = s3.listar('myappauberge','gallery')
    return render_template('galeria1.html', titulo="Gallery Page", func='gallery', image_names=image_names)

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
            try:
                os.remove(destination)
                print('borrar el archivo')
                flash("Image non sauvegardé ", "alert-warning")
            except:
                app.logger.info("error a borrar archivo (no existe por exemple)")            
            #cargar las imagenes 
            image_directory = os.path.join(app.root_path, 'static/images/gallery')
            #images = [os.path.join('/static/images/gallery', file) for file in os.listdir(image_directory) if file.endswith(('.jpg', '.png', '.jpeg'))]
            images = s3.listar('myappauberge','gallery')
        else:
            app.logger.info("funccion add_gallery boton ok")
            app.logger.info("Guardar el archivo")
            image_directory = os.path.join(app.root_path, 'static/images/gallery')
            #destination = 'static/images/gallery/' + data["filename"]
            destination = os.path.join(app.config['CLIENT_IMAGES'], data["filename"])
            s3.upload_file(file_name=destination, bucket='myappauberge', object_name='gallery/'+ data["filename"])
            flash("Image sauvegardé ", "alert-success")
            # Obtener la lista de archivos en el directorio
            #images = [os.path.join('/static/images/gallery', file) for file in os.listdir(image_directory) if file.endswith(('.jpg', '.png', '.jpeg'))]
            images = s3.listar('myappauberge','gallery')
    return redirect(url_for('get_gallery'))  # render_template('galeria1.html', titulo="Gallery Page", func='gallery', images=images)

@app.route('/borrar_gallery/<id>', methods=['POST'])
def borrar_gallery(id):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info(id)
    image_names = s3.listar('myappauberge','gallery')
    idreal = int(id) -1
    app.logger.info(image_names[int(idreal)])
    file = image_names[int(idreal)].split("amazonaws.com/")
    app.logger.info(file[0])
    app.logger.info(file[1])
    s3.del_image('myappauberge',file[1])
    return redirect(url_for('get_gallery'))


@app.route('/menuqr', methods=['GET', 'POST'])
def menuqr():
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    #results = []
    #registros =Product.read_all()
    registros = Product.query.order_by(Product.ordercat.asc(), Product.idcat.asc()).all()
    #ordercat,idcat
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
        nomplat = data["titre"]
        descrip = data['descripcion']
        product_new = Product(idcat=int(data['idcat']), titre=str(nomplat), prix=float(data['prix']),description=str(descrip), image='fondo.png', categorie=str(data['categorie']), ordercat=int(order))
        app.logger.info(product_new)
        Product.save(product_new)
        #db.session.add(product_new) # Agregar objeto a la solicitud
        #db.session.commit() 
        app.logger.info(product_new)
        flash("Plat ajouté á la carte","alert-success")
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
                flash("Nom de l'image vide !",'alert-danger')
                return redirect(request.url)

            if fichier and allowed_file_images(fichier.filename):
                # Genera un nuevo nombre de archivo para evitar conflictos
                fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], fichier.filename))  
                nombre_destino = 'photos/' + fichier.filename
                nombre_origen = 'static/images/photos/' + fichier.filename
                app.logger.info(fichier.filename) 
                producto_up = Product.get_by_id(id)
                producto_up.image = fichier.filename # Modificar objeto
                app.logger.info(producto_up) 
                db.session.add(producto_up) # Agregar objeto a la solicitud
                db.session.commit() # Hacer commit a la solicitud
                
                s3.upload_file(nombre_origen,'myappauberge',nombre_destino)
                app.logger.info("actualizado el campo de image en la base por el product " + id) 
                flash('Photo ajoutée !','alert-success')
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
            
            nomplat = data["titre"]
            descrip = data['descripcion']  
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
            flash("Plat modifié et ajouté á la carte","alert-success")
            app.logger.info("******** carta_up <string:id>  POST  Accion = save  FIN *************")
            return redirect(url_for('carta'))
            
        elif data['accion']=='Delete':
            app.logger.info("******** carta_up <string:id>  POST  Accion = Delete   *************")       
            producto = Product.query.get(id) 
            nom_origen = producto.image
            app.logger.info(producto)
            db.session.delete(producto)
            db.session.commit()
            if nom_origen != "fondo.png":
                s3.del_image('myappauberge', 'photos/' + nom_origen )
            flash("Plat éliminé de la carte","alert-success")
            app.logger.info(" se borro el registro numero " + id)
            app.logger.info("******** carta_up <string:id>  POST  Accion = delete  fin  *************")
            return redirect(url_for('carta'))  
        
        elif data['accion']=='eliminer':
            app.logger.info("******** carta_up <string:id>  POST  Accion = eliminer   *************")       
            producto = Product.query.get(id) 
            nom_origen = producto.image 
            producto.image = 'fondo.png'
            if nom_origen != producto.image:
                app.logger.info(producto)
                db.session.add(producto)
                db.session.commit()
                flash("Photo éliminé ","alert-success")
                app.logger.info(" se borro la image del plato numero %s" , id)
                #eliminamos del bucket de AWS el archivo
                s3.del_image('myappauberge', 'photos/' + nom_origen )
            else:
                flash("Cette photo ne peut etre eliminé ","alert-success")
                app.logger.info(" no se puede borrar Fondo.png")
            app.logger.info("******** carta_up <string:id>  POST  Accion = eliminer  fin  *************")
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

@app.route('/borrarmenu/<int:id>', methods=['GET', 'POST'])
def borrarmenu(id):
    nombre_funcion = inspect.currentframe().f_code.co_name
    app.logger.info(nombre_funcion)
    app.logger.info(int(id))
    if int(id)>0:
        menu = Menudia.query.get(id)
        app.logger.info(menu)
        db.session.delete(menu)
        db.session.commit()
    return redirect(url_for('menu'))  


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
        
    registros = listamenudia(1)
    app.logger.info(len(registros))
    if len(registros) == 0:
        registro = Menudia("Menu du jour á ", 16, "Consultez nos serveuses, elles se feront un plaisir de vous renseigner")
        registro.id=0
        registro.fecha_presentacion = "par default"
        registro.fecha_fin = "Toujours"
        registros.append(registro)
    app.logger.info(len(registros))
    return render_template('menu.html',hoy=hoy.strftime('%Y-%m-%d'), registros=registros)


@app.errorhandler(HTTPException)
def handle_exception(e):
    client_ip = request.remote_addr
    print(client_ip)
    if e.code == 404:
        response= "Erreur 404 : Not Found : L'URL demandée n'a pas été trouvée sur le serveur. Si vous avez saisi l'URL manuellement, veuillez vérifier votre orthographe et réessayer."
    elif e.code ==405:
        response = "Erreur 405 : Méthode non autorisée : La méthode n'est pas autorisée pour l'URL demandée."
    elif e.code== 500:
        response = "Erreur 500 - Erreur interne du serveur"
    else:
        response = "Erreur {0}: {1} : {2}".format(e.code, e.name, e.description)
    print(response)
    
    app.logger.info("errorhandler(HTTPException)")
    app.logger.info(response)
    flash(response, "alert-danger")
    #return response
    return response #redirect(url_for('home'))
    


if __name__ == '__main__':
    
    #pgloader sqlite://app2.sqlite2 postgresql://thierry:123456@localhost/auberge
    #with app.app_context():
    #    db.create_all()
    app.run()
    
    
