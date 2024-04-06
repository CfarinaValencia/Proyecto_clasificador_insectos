# Usa una imagen base de Python 3.9
FROM python:3.9.10

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos del proyecto al directorio de trabajo en el contenedor
COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Indica el puerto que tu aplicación utilizará
EXPOSE 8000

# Define el comando que ejecutará tu aplicación
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--reload"]
