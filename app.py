import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import time
import random

st.set_page_config(page_title="Beyond Reality — MVP", page_icon="🏛️", layout="wide")

# ==================== AGENT BASE CLASS ====================
class Agent:
    def __init__(self, name):
        self.name = name
        self.status = "idle"
        self.last_error = None
    
    def report(self, message, level="info"):
        if level == "info": st.info(f"🤖 [{self.name}] {message}")
        elif level == "success": st.success(f"✅ [{self.name}] {message}")
        elif level == "warning": st.warning(f"⚠️ [{self.name}] {message}")
        elif level == "error": st.error(f"❌ [{self.name}] {message}")

# ==================== TEXT AGENT ====================
class TextAgent(Agent):
    def __init__(self, api_key):
        super().__init__("TextAgent")
        self.api_key = api_key
    
    def get_available_models(self):
        try:
            genai.configure(api_key=self.api_key)
            models = genai.list_models()
            available = []
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    name = m.name.replace("models/", "")
                    if 'flash' in name: available.insert(0, name)
                    elif 'pro' in name: available.append(name)
                    else: available.append(name)
            return available if available else ["gemini-pro"]
        except: return ["gemini-pro", "gemini-1.0-pro"]
    
    def generate(self, prompt, max_retries=2):
        self.status = "working"
        models = self.get_available_models()
        self.report(f"ხელმისაწვდომი მოდელები: {', '.join(models[:3])}")
        
        for model_name in models:
            try:
                self.report(f"ვცდილობ: {model_name}")
                model = genai.GenerativeModel(model_name)
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(prompt)
                        self.report(f"წარმატება! ({model_name})", "success")
                        self.status = "done"
                        return response
                    except Exception as e:
                        err = str(e)
                        if '429' in err or 'quota' in err.lower():
                            if attempt < max_retries - 1:
                                wait = 10 * (attempt + 1)
                                self.report(f"ლიმიტი. ველოდები {wait}წმ...", "warning")
                                time.sleep(wait)
                            else:
                                self.report(f"{model_name} ამოიწურა. გადავდივარ შემდეგზე...", "warning")
                                break
                        elif 'not found' in err.lower(): break
                        else: raise e
            except: continue
        self.status = "failed"
        raise Exception("ყველა ტექსტის მოდელი ამოიწურა")

# ==================== IMAGE AGENT ====================
class ImageAgent(Agent):
    def __init__(self, hf_api_key):
        super().__init__("ImageAgent")
        self.hf_key = hf_api_key
    
    def generate_with_fallback(self, prompt, width, height, max_attempts=3):
        self.status = "working"
        services = [
            ("HuggingFace_FLUX", self._try_huggingface),
            ("Pollinations", self._try_pollinations),
            ("DeepAI", self._try_deepai),
            ("Placeholder", self._try_placeholder)
        ]
        
        for svc_name, svc_func in services:
            try:
                self.report(f"მეთოდი: {svc_name}...")
                result = svc_func(prompt, width, height, max_attempts)
                if result:
                    self.report(f"წარმატება! ({svc_name})", "success")
                    self.status = "done"
                    return result
            except Exception as e:
                self.report(f"{svc_name} ჩავარდა: {str(e)[:80]}", "warning")
                continue
        
        self.status = "failed"
        raise Exception("ყველა სურათის სერვისი ჩავარდა")
    
    def _try_huggingface(self, prompt, w, h, max_r):
        client = InferenceClient(api_key=self.hf_key)
        for attempt in range(max_r):
            try:
                return client.text_to_image(prompt=prompt, model="black-forest-labs/FLUX.1-schnell", width=w, height=h)
            except Exception as e:
                if '503' in str(e) or 'unavailable' in str(e).lower():
                    if attempt < max_r - 1:
                        time.sleep(15 * (attempt + 1))
                    else: raise
                else: raise
    
    def _try_pollinations(self, prompt, w, h, max_r):
        for attempt in range(max_r):
            try:
                clean_prompt = prompt.replace("\n", " ").replace('"', '')
                seed = random.randint(1, 999999)
                url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean_prompt)}?width={w}&height={h}&nologo=true&seed={seed}&model=flux"
                resp = requests.get(url, timeout=60)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    return img.convert('RGB') if img.mode == 'RGBA' else img
                elif resp.status_code == 404:
                    time.sleep(5)  # ცოტა ხანი დაველოდოთ
                    continue
                else: raise Exception(f"Status {resp.status_code}")
            except: 
                if attempt == max_r - 1: raise
                time.sleep(5)
    
    def _try_deepai(self, prompt, w, h, max_r):
        # DeepAI free API (no key required for basic usage)
        for attempt in range(max_r):
            try:
                resp = requests.post(
                    "https://api.deepai.org/api/text2img",
                    data={'text': prompt[:500]},  # limit prompt length
                    headers={'api-key': 'free-key-placeholder'},  # DeepAI accepts any key for free tier
                    timeout=45
                )
                if resp.status_code == 200:
                    data = resp.json()
                    img_url = data.get('output_url')
                    if img_url:
                        img_resp = requests.get(img_url, timeout=30)
                        img = Image.open(io.BytesIO(img_resp.content))
                        return img.convert('RGB').resize((w, h))
                time.sleep(3)
            except: 
                if attempt == max_r - 1: raise
                time.sleep(3)
    
    def _try_placeholder(self, prompt, w, h, max_r):
        # უკიდურესი ფოლბექი: ქმნის სურათს ტექსტით
        img = Image.new('RGB', (w, h), color=(30, 30, 50))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except: font = ImageFont.load_default()
        
        # წერს პრომპტის შეჯამებას
        short_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        draw.text((w//2, h//2), "🚪 Image Placeholder\n" + short_prompt, fill=(200,200,200), font=font, anchor="mm")
        return img

# ==================== LABEL AGENT ====================
class LabelAgent(Agent):
    def __init__(self):
        super().__init__("LabelAgent")
    
    def apply(self, image, width, height, labels=["A","B","C"]):
        self.status = "working"
        canvas = image.copy()
        draw = ImageDraw.Draw(canvas)
        
        font_size = int(width * 0.70)
        y_pos = int(height * 0.70)
        
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except: font = ImageFont.load_default()
        
        door_w = width // 3
        for i, label in enumerate(labels):
            cx = (i * door_w) + (door_w // 2)
            bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((cx-tw//2, y_pos-th//2), label, fill=(255,255,255), font=font, stroke_width=25, stroke_fill=(0,0,0))
        
        self.status = "done"
        return canvas

# ==================== DIRECTOR AGENT ====================
class DirectorAgent(Agent):
    def __init__(self, gemini_key, hf_key):
        super().__init__("Director")
        self.text_agent = TextAgent(gemini_key)
        self.image_agent = ImageAgent(hf_key)
        self.label_agent = LabelAgent()
    
    def orchestrate(self, text_prompt, image_prompt, width, height):
        self.status = "orchestrating"
        self.report("დაწყება: კონტენტის გენერაცია...")
        
        # 1. ტექსტი
        self.report("📝 ტექსტის აგენტი მუშაობს...")
        text_result = self.text_agent.generate(text_prompt)
        
        # 2. სურათი
        self.report("🎨 სურათის აგენტი მუშაობს...")
        image_result = self.image_agent.generate_with_fallback(image_prompt, width, height)
        
        # 3. ლეიბლები
        self.report("🏷️ ლეიბლების აგენტი მუშაობს...")
        final_image = self.label_agent.apply(image_result, width, height)
        
        self.status = "done"
        self.report("✅ ყველა აგენტმა დაასრულა!", "success")
        return text_result.text, final_image

# ==================== STREAMLIT APP ====================
@st.cache_resource
def load_secrets():
    return {"GEMINI": st.secrets.get("GEMINI_API_KEY"), "HF": st.secrets.get("HF_API_KEY")}

@st.cache_data
def load_template():
    with open("config/templates/psych_test_door_choice_v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

secrets = load_secrets()
template = load_template()

st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Agent-Based Architecture*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Gemini API", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("System", "🤖 Agent-Based")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია (Agent System v1.0)")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    with col_b: setting = st.selectbox("🖼️ სცენა", template["generation"]["image_settings"])
    with col_c:
        fmt_choice = st.selectbox("📐 ფორმატი", ["9:16 (Vertical / TikTok)", "16:9 (Horizontal / YouTube)", "1:1 (Square / Instagram)"], index=0)
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🎭 დირიჟორი აკოორდინირებს აგენტებს..."):
            try:
                if not secrets["GEMINI"]:
                    st.error("❌ GEMINI_API_KEY არ არის დაყენებული!"); st.stop()
                
                # ფორმატის კონფიგურაცია
                fmt = {"9:16 (Vertical / TikTok)": {"w":1080,"h":1920,"desc":"vertical 9:16"},
                       "16:9 (Horizontal / YouTube)": {"w":1920,"h":1080,"desc":"horizontal 16:9"},
                       "1:1 (Square / Instagram)": {"w":1080,"h":1080,"desc":"square 1:1"}}
                cfg = fmt[fmt_choice]
                
                # პრომპტები
                text_prompt = template["generation"]["text_prompt"].replace("{language}", lang)
                image_prompt = f"""
                Cinematic {cfg['desc']} shot. Three distinct doors in {setting}.
                LEFT: Ancient wooden door. CENTER: Futuristic metal door with blue neon. RIGHT: Magical crystal door.
                Doors centered, high detail, 8k, photorealistic. Fill entire frame, no empty space.
                """
                
                # დირიჟორის ორკესტრაცია
                director = DirectorAgent(secrets["GEMINI"], secrets["HF"])
                gen_text, gen_image = director.orchestrate(text_prompt, image_prompt, cfg["w"], cfg["h"])
                
                st.session_state['gen_text'] = gen_text
                st.session_state['gen_image'] = gen_image
                
            except Exception as e:
                st.error(f"❌ სისტემური შეცდომა: {str(e)}")
    
    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader(f"📝 შედეგები ({fmt_choice})")
        st.text_area("📜 ტექსტი", st.session_state['gen_text'], height=120)
        col_m, col_c, col_m = st.columns([0.1, 1, 0.1])
        with col_c:
            st.image(st.session_state['gen_image'], caption="🚪 A | B | C", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
