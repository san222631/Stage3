from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, HTTPException
import boto3 
import os
from fastapi.staticfiles import StaticFiles
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# AWS S3 configuration
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
S3_KEY = os.getenv('S3_KEY')
S3_SECRET = os.getenv('S3_SECRET')

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
    region_name=S3_REGION
)

# Database Configuration
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# 創造暫時資料夾來儲存檔案
TMP_DIR = "tmp"
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

@app.get("/")
async def index(request: Request, include_in_schema=False):
    return FileResponse("./static/index.html", media_type="text/html")

@app.post("/upload")
async def upload_file(caption: str = Form(...), image: UploadFile = File(...)):
    if image.filename == '':
        raise HTTPException(status_code=400, detail="No selected file")

    filename = image.filename
    file_location = os.path.join(TMP_DIR, filename)

    with open(file_location, "wb") as file:
        content = await image.read()
        file.write(content)

    try:
        s3.upload_file(
            file_location,
            S3_BUCKET,
            filename,
        )
        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"

        # Save the message and image URL to the database
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        if connection.is_connected():
            cursor = connection.cursor()
            sql = "INSERT INTO messages (message, image_url) VALUES (%s, %s)"
            cursor.execute(sql, (caption, image_url))
            connection.commit()
            cursor.close()
            connection.close()

    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": True,
                "message":"伺服器內部錯誤"
            }
        )
    finally:
        os.remove(file_location)

    return JSONResponse(
        status_code=200,
        content={
            "message": caption, 
            "image_url": image_url
        }
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

@app.get("/api/contents")
async def fetch_contents():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT message, image_url
            FROM messages
            ORDER BY Time DESC
            """
            cursor.execute(query)
            contents = cursor.fetchall()
            cursor.close()
            connection.close()
            response = {
                "data": contents
            }
            return response
    
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message":"伺服器內部錯誤"
            }
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close() 


