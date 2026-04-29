import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import time
import random

st.set_page_config(page_title=" Romance Studio", page_icon="🎬", layout="wide")

# ==================== AGENT BASE CLASS ====================
class Agent:
    def __init__(self, name):
        self.name = name
        self.status = "idle"
    
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
    
    def generate_story(self, mood, language, max_retries=2):
        self.status = "working"
        models = self.get_available_models()
        self.report(f"ხელმისაწვდომი მოდელები: {', '.join(models[:3])}")
        
        # რომანტიკული/მელანქოლიური პრომპტი
        prompt = f"""
        Write a short, deeply emotional micro-story (3-4 sentences) in {language} about "{mood}".
        Focus on atmosphere, subtle emotions, and cinematic details. 
        Do not include labels, instructions, or explanations. Just the story.
        """
        
        for model_name in models:
            try:
                self.report(f"ვწერ ამბავს: {model_name}")
                model = genai.GenerativeModel(model_name)
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(prompt)
                        self.report(f"ამბავი მზადაა! ({model_name})", "success")
                        self.status = "done"
                        return response.text.strip()
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
            ("Lexica", self._try_lexica),
            ("Craiyon", self._try_craiyon),
            ("Placeholder", self._try_placeholder)
        ]
        
        for svc_name, svc_func in services:
            try:
                self.report(f"ვიზუალი: {svc_name}...")
                result = svc_func(prompt, width, height, max_attempts)
                if result:
                    if result.size != (width, height):
                        result = result.resize((width, height), Image.LANCZOS)
                    self.report(f"ვიზუალი მზადაა! ({svc_name})", "success")
                    self.status = "done"
                    return result
            except Exception as e:
                self.report(f"{svc_name} ჩავარდა: {str(e)[:80]}", "warning")
                continue
        
        self.status = "failed"
        raise Exception("ყველა ვიზუალური სერვისი ჩავარდა")
    
    def _try_huggingface(self, prompt, w, h, max_r):
        client = InferenceClient(api_key=self.hf_key)
        for attempt in range(max_r):
            try:
                return client.text_to_image(prompt=prompt, model="black-forest-labs/FLUX.1-schnell", width=w, height=h)
            except Exception as e:
                if '503' in str(e) or 'unavailable' in str(e).lower():
                    if attempt < max_r - 1: time.sleep(15 * (attempt + 1))
                    else: raise
                else: raise
    
    def _try_pollinations(self, prompt, w, h, max_r):
        for attempt in range(max_r):
            try:
                clean = prompt.replace("\n", " ").replace('"', '')
                url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean)}?width={w}&height={h}&nologo=true&seed={random.randint(1,999999)}&model=flux"
                resp = requests.get(url, timeout=60)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    return img.convert('RGB') if img.mode == 'RGBA' else img
                elif resp.status_code == 404: time.sleep(5)
                else: raise Exception(f"Status {resp.status_code}")
            except: 
                if attempt == max_r - 1: raise
                time.sleep(5)
    
    def _try_lexica(self, prompt, w, h, max_r):
        for attempt in range(max_r):
            try:
                resp = requests.get(f"https://lexica.art/api/v1/search?q={requests.utils.quote(prompt[:100])}", timeout=30)
                if resp.status_code == 200 and resp.json().get('images'):
                    img_url = resp.json()['images'][0]['url']
                    img = Image.open(io.BytesIO(requests.get(img_url, timeout=30).content))
                    return img.convert('RGB').resize((w, h))
                time.sleep(3)
            except: 
                if attempt == max_r - 1: raise
                time.sleep(3)
    
    def _try_craiyon(self, prompt, w, h, max_r):
        for attempt in range(max_r):
            try:
                resp = requests.post("https://api.craiyon.com/v3", json={"prompt": prompt[:200], "negative_prompt": "", "aspect_ratio": "portrait" if h>w else "square" if w==h else "landscape"}, timeout=90)
                if resp.status_code == 200 and resp.json().get('images'):
                    import base64
                    img = Image.open(io.BytesIO(base64.b64decode(resp.json()['images'][0])))
                    return img.convert('RGB').resize((w, h))
                time.sleep(5)
            except: 
                if attempt == max_r - 1: raise
                time.sleep(5)
    
    def _try_placeholder(self, prompt, w, h, max_r):
        self.report("უკიდურესი ფოლბექი: Placeholder-ის შექმნა...", "warning")
        img = Image.new('RGB', (w, h), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", min(w, h)//10)
        except: font = ImageFont.load_default()
        short = prompt[:100] + "..." if len(prompt) > 100 else prompt
        bbox = draw.textbbox((0,0), short, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((w//2-tw//2, h//2-th//2), short, fill=(200,200,200), font=font)
        return img

# ==================== DIRECTOR AGENT ====================
class DirectorAgent(Agent):
    def __init__(self, gemini_key, hf_key):
        super().__init__("Director")
        self.text_agent = TextAgent(gemini_key)
        self.image_agent = ImageAgent(hf_key)
        
        # კინემატოგრაფიული სცენების ბაზა
        self.scenes = {
            "🌧️ წვიმიანი შეხვედრა": "A lonely figure standing under a vintage street lamp in heavy rain, holding a black umbrella, looking at a warmly lit window across the street. Cinematic, melancholic, moody lighting, 8k, photorealistic, vertical composition",
            " დაკარგული სიყვარული": "An empty park bench in autumn, fallen leaves scattered, soft golden hour light, a single red scarf left on the bench. Emotional, nostalgic, cinematic depth of field, 8k, vertical",
            " იმედის სხივი": "A person standing on a cliff edge at sunrise, looking out over a misty valley, rays of light breaking through dark clouds. Hopeful, epic, cinematic, dramatic lighting, 8k, vertical",
            " ქალაქის მარტოობა": "A small apartment window at night, city lights blurred in background, raindrops on glass, a cup of coffee steaming on the windowsill. Intimate, lonely, cinematic, 8k, vertical",
            "🌙 მთვარის შუქზე": "Two silhouettes walking slowly along a quiet beach under a full moon, waves gently touching the shore, soft silver light reflecting on water. Romantic, peaceful, cinematic, 8k, vertical"
        }
    
    def orchestrate(self, mood_key, language, width, height):
        self.status = "orchestrating"
        self.report("დაწყება: რომანტიკული სცენის შექმნა...")
        
        scene_desc = self.scenes.get(mood_key, self.scenes["🌧️ წვიმიანი შეხვედრა"])
        mood_name = mood_key.split(" ", 1)[1] if " " in mood_key else mood_key
        
        # 1. ტექსტი
        self.report("📝 ამბავის წერა...")
        story_text = self.text_agent.generate_story(mood_name, language)
        
        # 2. სურათი (კინემატოგრაფიული პრომპტი)
        image_prompt = f"Cinematic vertical shot (9:16). {scene_desc}. Moody, emotional atmosphere, high detail, 8k, photorealistic, dramatic lighting."
        self.report("🎨 ვიზუალის შექმნა...")
        image_result = self.image_agent.generate_with_fallback(image_prompt, width, height)
        
        self.status = "done"
        self.report("✅ სცენა მზადაა!", "success")
        return story_text, image_result

# ==================== STREAMLIT APP ====================
@st.cache_resource
def load_secrets():
    return {"GEMINI": st.secrets.get("GEMINI_API_KEY"), "HF": st.secrets.get("HF_API_KEY")}

secrets = load_secrets()

st.title(" Beyond Reality — Romance Studio")
st.markdown("*AI Cinematic Stories | Vertical Format for TikTok/Reels*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Gemini API", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("System", "🎬 Romance v1.0")

tab1, tab2 = st.tabs([" სცენის შექმნა", "💡 ინსტრუქცია"])

with tab1:
    st.subheader("🎥 აირჩიე სცენა და ენა")
    
    col_a, col_b = st.columns(2)
    with col_a:
        mood = st.selectbox(" სცენა / განწყობა", [
            "🌧️ წვიმიანი შეხვედრა",
            "🍂 დაკარგული სიყვარული",
            "🌅 იმედის სხივი",
            "🌃 ქალაქის მარტოობა",
            "🌙 მთვარის შუქზე"
        ])
    with col_b:
        lang = st.selectbox(" ენა", ["ქართული", "English", "Español", "Français", "Deutsch"])
    
    if st.button(" შექმენი სცენა", type="primary"):
        with st.spinner("🎭 დირიჟორი ქმნის კინემატოგრაფიულ ისტორიას..."):
            try:
                if not secrets["GEMINI"]:
                    st.error("❌ GEMINI_API_KEY არ არის დაყენებული!"); st.stop()
                
                # ვერტიკალური ფორმატი (TikTok/Reels პტიმალური)
                W, H = 1080, 1920
                
                director = DirectorAgent(secrets["GEMINI"], secrets["HF"])
                story, image = director.orchestrate(mood, lang, W, H)
                
                st.session_state['story'] = story
                st.session_state['image'] = image
                
            except Exception as e:
                st.error(f"❌ სისტემური შეცდომა: {str(e)}")
    
    # შედეგების ჩვენება
    if 'story' in st.session_state:
        st.divider()
        st.subheader(f"📖 შედეგი: {mood}")
        
        # ტექსტი ზემოთ
        st.markdown(f"**📜 ამბავი:**\n\n{st.session_state['story']}")
        
        # სურათი ქვემოთ, ცენტრში, სრული სიგანით
        col_m, col_c, col_m = st.columns([0.05, 1, 0.05])
        with col_c:
            st.image(st.session_state['image'], caption="🎬 AI Cinematic Scene (9:16)", use_column_width=True)
            st.download_button("💾 ჩამოტვირთე სურათი (PNG)", data=st.session_state['image'], file_name="romance_scene.png", mime="image/png")

with tab2:
    st.info("💡 **როგორ გამოვიყენო ეს TikTok/Reels-ისთვის?**\n\n1. დააგენერირე სცენა ამ ხელსაწყოთი.\n2. ჩამოტვირთე ვერტიკალური სურათი.\n3. გამოიყენე CapCut ან InShot: დაამატე ტექსტი სურათზე, დაადე მელანქოლიური მუსიკა.\n4. ატვირთე TikTok/Reels-ზე ეშთეგებით: #AIArt #Melancholy #RomanceStory #AICinematic\n\n🔄 **სისტემა ავტომატურად ქმნის უნიკალურ კონტენტს ყოველ ჯერზე!**")
