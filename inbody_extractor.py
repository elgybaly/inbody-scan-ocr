import google.generativeai as genai
import json
import os
import base64
import re
from dotenv import load_dotenv

# =========================
# Load Environment
# =========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)


class InBodyExtractor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def extract_from_bytes(self, image_bytes: bytes, mime_type: str):
        """Extract InBody data from image bytes"""

        img_data = base64.b64encode(image_bytes).decode()

        # =========================
        # Improved Prompt
        # =========================
        prompt = """
حلل صورة InBody واستخرج البيانات التالية بدقة في JSON format فقط:

📊 البيانات المطلوبة:

1. age
2. gender (Male / Female)
3. weight (kg)
4. height (cm)

5. smm (Skeletal Muscle Mass)
6. body_fat_mass
7. ffm (Fat Free Mass)

8. muscle_percentage (%)
9. fat_percentage (%)
10. water_percentage (%)
11. bmr

⚠️ مهم:
- لازم ترجع JSON فقط بدون أي شرح
- لو القيمة غير موجودة ضع -1
- استخرج القيم حتى لو غير مباشرة من الصورة

📦 الشكل المطلوب:
{
  "age": 25,
  "gender": "Male",
  "weight": 80,
  "height": 175,
  "smm": 32.1,
  "body_fat_mass": 18.2,
  "ffm": 61.8,
  "muscle_percentage": 40.2,
  "fat_percentage": 20.5,
  "water_percentage": 55.3,
  "bmr": 1700
}
"""

        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": img_data
            }
        }

        try:
            response = self.model.generate_content([prompt, image_part])
            text = response.text.strip()

            # =========================
            # Safe JSON extraction
            # =========================
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                raise ValueError("❌ JSON not found in response")

            data = json.loads(match.group())

            # =========================
            # Post processing (smart fill)
            # =========================
            data = self._post_process(data)

            return data

        except json.JSONDecodeError:
            return self._extract_numbers(text)

        except Exception as e:
            return {"error": str(e)}

    # =========================
    # Smart Calculation Engine
    # =========================
    def _post_process(self, data: dict):

        weight = data.get("weight", -1)
        fat_mass = data.get("body_fat_mass", -1)
        smm = data.get("smm", -1)
        ffm = data.get("ffm", -1)

        # =========================
        # FFM calculation
        # =========================
        if ffm == -1 and weight > 0 and fat_mass > 0:
            ffm = weight - fat_mass
            data["ffm"] = ffm

        # =========================
        # Fat %
        # =========================
        if data.get("fat_percentage", -1) == -1:
            if fat_mass > 0 and weight > 0:
                data["fat_percentage"] = (fat_mass / weight) * 100

        # =========================
        # Muscle %
        # =========================
        if data.get("muscle_percentage", -1) == -1:
            if smm > 0 and weight > 0:
                data["muscle_percentage"] = (smm / weight) * 100
            elif ffm > 0 and weight > 0:
                data["muscle_percentage"] = (ffm * 0.5 / weight) * 100

        # =========================
        # Water %
        # =========================
        if data.get("water_percentage", -1) == -1:
            if ffm > 0 and weight > 0:
                data["water_percentage"] = (ffm * 0.73 / weight) * 100

        # =========================
        # BMR (Harris-Benedict)
        # =========================
        if data.get("bmr", -1) == -1:
            age = data.get("age", -1)
            height = data.get("height", -1)
            gender = data.get("gender", "").lower()

            if weight > 0 and height > 0 and age > 0:
                if "male" in gender:
                    data["bmr"] = 10 * weight + 6.25 * height - 5 * age + 5
                elif "female" in gender:
                    data["bmr"] = 10 * weight + 6.25 * height - 5 * age - 161

        # =========================
        # rounding cleanup
        # =========================
        for key, value in data.items():
            if isinstance(value, float):
                data[key] = round(value, 2)

        return data

    # =========================
    # fallback extractor
    # =========================
    def _extract_numbers(self, text: str):

        numbers = re.findall(r'\b\d+\.?\d*\b', text)

        return {
            "age": int(numbers[0]) if len(numbers) > 0 else -1,
            "gender": "Male",
            "weight": float(numbers[1]) if len(numbers) > 1 else -1,
            "height": float(numbers[2]) if len(numbers) > 2 else -1,
            "smm": float(numbers[3]) if len(numbers) > 3 else -1,
            "body_fat_mass": float(numbers[4]) if len(numbers) > 4 else -1,
            "ffm": float(numbers[5]) if len(numbers) > 5 else -1,
            "muscle_percentage": float(numbers[6]) if len(numbers) > 6 else -1,
            "fat_percentage": float(numbers[7]) if len(numbers) > 7 else -1,
            "water_percentage": float(numbers[8]) if len(numbers) > 8 else -1,
            "bmr": int(numbers[9]) if len(numbers) > 9 else -1,
        }