# API de Usuarios con FastAPI

Esta API permite gestionar usuarios y su información de conexión a internet, además de soportar operaciones relacionadas con imágenes (subir, listar y extraer la última imagen). Está desarrollada en Python utilizando FastAPI y SQLAlchemy.

## Características

- CRUD de usuarios (Crear, Leer, Actualizar, Eliminar).
- Gestión de información de conexión a internet asociada a cada usuario.
- Subida y gestión de imágenes en formato `.jpg`.
- Base de datos SQLite para almacenar los datos.

## Requisitos

- Python 3.9 o superior.
- Las dependencias listadas en `requirements.txt`.

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <URL-DEL-REPOSITORIO>
   cd <NOMBRE-DEL-DIRECTORIO>
   ```

2. **Crear un entorno virtual** (opcional pero recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   uvicorn main:app --reload
   ```
   Esto iniciará el servidor en `http://127.0.0.1:8000`.

## Endpoints principales

### Usuarios

- **POST /usuarios/**
  - Crea un nuevo usuario con información de conexión a internet.
  - Ejemplo de solicitud:
    ```json
    {
      "nombre": "usuario1",
      "contraseña": "clave123",
      "internet": {
        "nombre": "WiFi-Casa",
        "contraseña": "wifi1234"
      }
    }
    ```

- **GET /usuarios/{nombre}/internet**
  - Obtiene la información de internet asociada a un usuario específico.

- **PUT /usuarios/internet**
  - Actualiza la información de internet de un usuario.

- **DELETE /usuarios/{nombre}**
  - Elimina un usuario por su nombre.

- **GET /usuarios/**
  - Lista todos los usuarios con su información.

### Imágenes

- **POST /imagenes/**
  - Sube una imagen en formato `.jpg`.

- **GET /imagenes/ultima/**
  - Extrae y descarga la última imagen subida. Borra todos los archivos y registros relacionados.

## Estructura del proyecto

```
.
├── main.py                # Archivo principal con la implementación de la API.
├── requirements.txt       # Archivo con las dependencias del proyecto.
├── uploaded_images/       # Carpeta para almacenar las imágenes subidas.
└── README.md              # Este archivo.
```

## Notas importantes

- Todas las imágenes deben ser en formato `.jpg`. Si no se cumple esta condición, se devolverá un error.
- La base de datos SQLite se crea automáticamente al iniciar el proyecto.
- El endpoint `/imagenes/ultima/` elimina todas las imágenes y sus registros después de extraer la última.

## Contribuciones

Si deseas contribuir a este proyecto:
1. Haz un fork del repositorio.
2. Crea una rama para tus cambios:
   ```bash
   git checkout -b mi-nueva-funcionalidad
   ```
3. Realiza un pull request una vez que termines tus modificaciones.

## Licencia

Este proyecto se distribuye bajo la [MIT License](LICENSE).

---

¡Gracias por usar esta API! Si tienes preguntas o problemas, no dudes en abrir un issue.
