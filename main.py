from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from dotenv import load_dotenv
load_dotenv()
from app.inbody_extractor import InBodyExtractor
# تحميل .env
load_dotenv()

app = FastAPI(
    title="InBody OCR API",
    description="Extract body composition data from InBody images",
    version="1.0"
)

extractor = InBodyExtractor()


@app.get("/")
def root():
    return {"message": "InBody API is running 🚀"}


@app.post("/analyze-inbody")
async def analyze_inbody(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="❌ لازم ترفع صورة")

        contents = await file.read()

        result = extractor.extract_from_bytes(
            image_bytes=contents,
            mime_type=file.content_type
        )

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# تشغيل مباشر
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)