from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os

from dotenv import load_dotenv
load_dotenv()

from inbody_extractor import InBodyExtractor

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
        # ✅ تحقق من نوع الملف
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="❌ لازم ترفع صورة")

        # ✅ قراءة الصورة
        contents = await file.read()

        # ✅ تحليل الصورة
        result = extractor.extract_from_bytes(
            image_bytes=contents,
            mime_type=file.content_type
        )

        if not result:
            raise HTTPException(status_code=500, detail="فشل في استخراج البيانات")

        return JSONResponse(content=result)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ متوافق مع Railway
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)