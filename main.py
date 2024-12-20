import os
import shutil
from io import BytesIO
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

app = FastAPI()

# Configuración de la base de datos
DATABASE_URL = "sqlite:///./usuarios.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Carpeta para almacenar las imágenes
UPLOAD_FOLDER = "./uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modelos de base de datos
class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    contraseña = Column(String, nullable=False)
    internet = relationship("InternetDB", back_populates="usuario", uselist=False)

class InternetDB(Base):
    __tablename__ = "internet"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    contraseña = Column(String, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("UsuarioDB", back_populates="internet")

class ImagenDB(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Modelos de datos para FastAPI
class Internet(BaseModel):
    nombre: str
    contraseña: str

class Usuario(BaseModel):
    nombre: str
    contraseña: str

class UsuarioConInternet(Usuario):
    internet: Internet

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de la API
@app.post("/usuarios/", response_model=UsuarioConInternet)
def crear_usuario(usuario: UsuarioConInternet, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioDB).filter(UsuarioDB.nombre == usuario.nombre).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    nuevo_usuario = UsuarioDB(nombre=usuario.nombre, contraseña=usuario.contraseña)
    nuevo_internet = InternetDB(nombre=usuario.internet.nombre, contraseña=usuario.internet.contraseña, usuario=nuevo_usuario)

    db.add(nuevo_usuario)
    db.add(nuevo_internet)
    db.commit()
    db.refresh(nuevo_usuario)
    return {
        "nombre": nuevo_usuario.nombre,
        "contraseña": nuevo_usuario.contraseña,
        "internet": {"nombre": nuevo_internet.nombre, "contraseña": nuevo_internet.contraseña}
    }

@app.get("/usuarios/{nombre}/internet", response_model=Internet)
def obtener_internet_usuario(nombre: str, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.nombre == nombre).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not usuario.internet:
        raise HTTPException(status_code=404, detail="Internet no encontrado para este usuario")
    return {"nombre": usuario.internet.nombre, "contraseña": usuario.internet.contraseña}

@app.put("/usuarios/internet", response_model=Internet)
def actualizar_internet(nombre: str, contraseña: str, nuevo_internet: Internet, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.nombre == nombre, UsuarioDB.contraseña == contraseña).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o contraseña incorrecta")
    
    usuario.internet.nombre = nuevo_internet.nombre
    usuario.internet.contraseña = nuevo_internet.contraseña

    db.commit()
    db.refresh(usuario.internet)
    return {"nombre": usuario.internet.nombre, "contraseña": usuario.internet.contraseña}

@app.delete("/usuarios/{nombre}")
def eliminar_usuario(nombre: str, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.nombre == nombre).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(usuario)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}

@app.get("/usuarios/", response_model=list[UsuarioConInternet])
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(UsuarioDB).all()
    return [
        {
            "nombre": usuario.nombre,
            "contraseña": usuario.contraseña,
            "internet": {
                "nombre": usuario.internet.nombre,
                "contraseña": usuario.internet.contraseña,
            } if usuario.internet else None,
        }
        for usuario in usuarios
    ]

# Ruta para subir una imagen
@app.post("/imagenes/")
async def subir_imagen(file: bytes = File(...), db: Session = Depends(get_db)):
    # Define el nombre del archivo de forma estática o genera uno único
    filename = "imagen_recibida.jpg"  # Puedes usar una lógica más compleja si necesitas nombres únicos
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Guardar la imagen en el disco
        with open(file_path, "wb") as buffer:
            buffer.write(file)
        
        # Guardar los metadatos en la base de datos
        nueva_imagen = ImagenDB(filename=filename)
        db.add(nueva_imagen)
        db.commit()
        db.refresh(nueva_imagen)
        
        return {"detail": "Imagen subida correctamente", "filename": nueva_imagen.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen: {str(e)}")

# Ruta para extraer y borrar la última imagen
@app.get("/imagenes/ultima/")
def extraer_ultima_imagen(db: Session = Depends(get_db)):
    # Obtener la última imagen
    ultima_imagen = db.query(ImagenDB).order_by(ImagenDB.id.desc()).first()
    if not ultima_imagen:
        raise HTTPException(status_code=404, detail="No hay imágenes disponibles")

    # Ruta del archivo en el sistema
    file_path = os.path.join(UPLOAD_FOLDER, ultima_imagen.filename)

    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="El archivo de imagen no existe")

    # Leer el archivo en memoria
    with open(file_path, "rb") as file:
        contenido = BytesIO(file.read())

    # Preparar la eliminación de todos los archivos y registros
    def eliminar_archivos_y_registros():
        shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        db.query(ImagenDB).delete()
        db.commit()

    # Devolver el archivo como respuesta y eliminar los datos después
    response = StreamingResponse(contenido, media_type="image/jpeg")
    response.headers["Content-Disposition"] = f"attachment; filename={ultima_imagen.filename}"
    eliminar_archivos_y_registros()
    return response
