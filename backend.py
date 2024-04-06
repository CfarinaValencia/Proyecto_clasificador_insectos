from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import uvicorn
import numpy as np
import pandas as pd
import mysql.connector
from mysql.connector import Error
from io import BytesIO
from pydantic import BaseModel
from fastapi import HTTPException

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()


# Monta el directorio de archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/login.html')

@app.get("/clasificar")
async def get_classification_page():
    return FileResponse('static/clasificar.html')

@app.get("/registro")
async def get_register_page():
    return FileResponse('static/register.html')


# Configuración de la aplicación y CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga del modelo y configuración de la base de datos
model = load_model('mi_modelo.h5')
# db_config = {
#     'user': 'alejoval',
#     'password': 'alejoval',
#     'host': 'localhost',
#     'database': 'clasificadorinsectosia'
# }

db_config = {
    'user': 'alejoval',
    'password': 'alejoval',
    'host': 'db',  # Nombre del servicio en docker-compose.yml, NO 'localhost'
    'database': 'clasificadorinsectosia'
}



# Cargamos el mapeo de etiquetas desde el CSV
df_classes = pd.read_csv('_classes.csv')
label_map = {index - 2: class_name for index, class_name in enumerate(df_classes.columns) if index != 0}


# Función de conexión a la base de datos
def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection

class UserRegistration(BaseModel):
    username: str
    password: str

@app.post("/registrar")
def register_user(user: UserRegistration):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
        
        # Insertar el nuevo usuario
        cursor.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (%s, %s)", (user.username, user.password))
        connection.commit()
        
        return {"mensaje": "Usuario registrado con éxito"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {err}")
    finally:
        cursor.close()
        connection.close()

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT * FROM usuarios WHERE usuario = %s AND contrasena = %s"
        cursor.execute(query, (username, password))
        user_record = cursor.fetchone()
        if user_record:
            return {"mensaje": "Login exitoso"}
        else:
            raise HTTPException(status_code=400, detail="Credenciales inválidas")
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {err}")
    finally:
        cursor.close()
        connection.close()	

@app.post("/clasificar")
async def clasificar_imagen(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = load_img(BytesIO(contents), target_size=(150, 150))
        image_array = img_to_array(image)
        image_array = np.expand_dims(image_array, axis=0) / 255.0

        prediction = model.predict(image_array)
        prediction_result = np.argmax(prediction, axis=1)[0]
        predicted_class = label_map[prediction_result]
        predicted_class = predicted_class.strip()

        connection = get_db_connection()
        cursor = connection.cursor()

        query = "SELECT descripcion FROM insectos WHERE nombre = %s"
        cursor.execute(query, (predicted_class,))
        description = cursor.fetchone()

        if description:
            description = description[0]
        else:
            description = "Descripción no encontrada."

        cursor.close()
        connection.close()

        return {"clase": predicted_class, "descripcion": description}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


