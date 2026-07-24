import google.generativeai as genai
import os
from dotenv import load_dotenv

# .env dosyasındaki şifremizi alıyoruz
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

print("--- SISTEMINIZDE KULLANILABILEN MODELLER ---")
# Google'a bağlanıp izin verilen modelleri soruyoruz
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
print("--------------------------------------------")