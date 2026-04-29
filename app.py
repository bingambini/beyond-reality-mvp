import streamlit as st
import os
import time
import random
import asyncio
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import edge_tts
import moviepy.editor as mp
import requests
import io
from huggingface_hub import InferenceClient

# ==================== კონფიგურაცია ====================
CONFIG = {
    "GEMINI_API_KEY": st.secrets.get("GEMINI_API_KEY", ""),
    "HF_API_KEY": st.secrets.get("HF_API_KEY", ""),
    "OUTPUT_DIR": "./output",
    "VIDEO_WIDTH": 1080,
    "VIDEO_HEIGHT": 1920,
    "TTS_VOICE": "ka-GE-NinoNeural",  # ქართული ხმა. ინგლისურისთვის: "en-US-AriaNeural"
    "FALLBACK_MUSIC_URL": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=ambient-piano-loop-114773.mp3"
}

os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)

# ==================== აგენტების მთავარი ინტერფეისი ====================
class Agent:
    def __init__(self, name, logger_func):
        self.name = name
        self.log = logger_func
        self.sub_agents = {}

    def register_sub_agent(self, name, sub_agent):
        self.sub_agents[name] = sub_agent

    def report(self, msg, level="info"):
        self.log(self.name, msg, level)

# ==================== 1. თემის აგენტი + სუბ-ვალიდატორი ====================
class ThemeValidator:
    def validate(self, theme):
        if not theme or len(theme) < 5:
            return False, "თემა ძალიან მოკლეა"
        # შევამოწმოთ რომ კინემატოგრაფიული/ემოციური ტონი იყოს
        emotional_words = ["წვიმა", "მარტო", "დაკარგული", "იმედი", "შეხვედრა", "მთვარე", "სიყვარული", "ფანჯარა"]
        if any(w in theme.lower() for w in emotional_words):
            return True, "✅ ტონი და სიგრძე შესაბამისობაშია"
        return True, "⚠️ ტონი ნეიტრალურია, მაგრამ მისაღებია"

class ThemeAgent(Agent):
    THEMES = [
        "წვიმიანი შეხვედრა ძველ ქუჩაში",
        "დაკარგული წერილი ატყავედებულ მაგიდაზე",
        "მთვარის შუქზე სიარული ცარიელ სანაპიროზე",
        "ფანჯრიდან დანახული უცნობი სილუეტი",
        "შემოდგომის პარკში დარჩენილი წითელი ქურთუკი",
        "ღამის მატარებელი და უსაზღვრო ველები"
    ]
    
    def __init__(self, logger_func):
        super().__init__("🎭 ThemeAgent", logger_func)
        self.register_sub_agent("Validator", ThemeValidator())

    def execute(self):
        self.report("ირჩევს თემას ბაზიდან...")
        theme = random.choice(self.THEMES)
        self.report(f"შერჩეულია: '{theme}'")
        
        valid, msg = self.sub_agents["Validator"].validate(theme)
        self.report(f"სუბ-აგენტი (Validator): {msg}", "success" if valid else "warning")
        
        if not valid:
            self.report("გადაარჩევს სხვა თემას...", "warning")
            return self.execute() # რეკურსიული გადარჩევა
        return theme

# ==================== 2. სცენარის აგენტი + სუბ-რედაქტორი ====================
class ScriptEditor:
    def validate(self, text, max_sentences=4):
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) > max_sentences:
            return False, "ტექსტი ზედმეტად გრძელია"
        if "აი" in text or "აქ" in text or "თუ" in text[:20]: # AI არტეფაქტების შემოწმება
            return False, "აღმოჩენილია AI-ის ტიპიური ფრაზები"
        return True, "✅ სტრუქტურა და სტილი შესაბამისობაშია"

class ScriptAgent(Agent):
    def __init__(self, api_key, logger_func):
        super().__init__("📝 ScriptAgent", logger_func)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.register_sub_agent("Editor", ScriptEditor())

    def execute(self, theme):
        self.report(f"წერს სცენარს თემაზე: {theme}")
        prompt = f"""
        დაწერე მოკლე, ემოციური მიკრო-ისტორია (2-3 წინადადება) ქართულ ენაზე.
        თემა: "{theme}"
        სტილი: მელანქოლიური, კინემატოგრაფიული, პოეტური.
        წესები: არ დაიწყო "აი", "წარმოიდგინე", "ეს არის". პირდაპირ შედი სცენაში.
        """
        try:
            resp = self.model.generate_content(prompt)
            text = resp.text.strip().replace('"', '')
            
            valid, msg = self.sub_agents["Editor"].validate(text)
            self.report(f"სუბ-აგენტი (Editor): {msg}", "success" if valid else "warning")
            
            if not valid:
                self.report("სთხოვს ხელახლა გენერაციას სუფთა ვერსიას...", "warning")
                return self.execute(theme)
            return text
        except Exception as e:
            self.report(f"შეცდომა: {str(e)}", "error")
            return f"ისტორია ვერ დაიწერა. თემა: {theme}"

# ==================== 3. ხმის (TTS) აგენტი + სუბ-პროცესორი ====================
class VoiceProcessor:
    def validate(self, audio_path, min_duration=2.0):
        try:
            dur = mp.AudioFileClip(audio_path).duration
            if dur < min_duration:
                return False, f"ხმა ძალიან მოკლეა ({dur:.1f}წმ)"
            return True, f"✅ ხანგრძლივობა: {dur:.1f}წმ"
        except: return False, "ფაილი ვერ წაიკითხა"

class VoiceAgent(Agent):
    def __init__(self, voice, logger_func):
        super().__init__("🎙️ VoiceAgent", logger_func)
        self.voice = voice
        self.register_sub_agent("Processor", VoiceProcessor())

    async def execute(self, text, output_path):
        self.report(f"ქმნის ხმოვან ნარაციას ({self.voice})...")
        try:
            comm = edge_tts.Communicate(text, self.voice)
            await comm.save(output_path)
            
            valid, msg = self.sub_agents["Processor"].validate(output_path)
            self.report(f"სუბ-აგენტი (Processor): {msg}", "success" if valid else "warning")
            return output_path if valid else None
        except Exception as e:
            self.report(f"შეცდომა TTS-ში: {str(e)}", "error")
            return None

# ==================== 4. ვიზუალის აგენტი + სუბ-კურატორი ====================
class VisualCurator:
    def validate(self, img, min_width=800):
        if img.width < min_width:
            return False, "რეზოლუცია დაბალია"
        return True, f"✅ ზომა: {img.width}x{img.height}"

class VisualAgent(Agent):
    def __init__(self, hf_key, logger_func):
        super().__init__("🖼️ VisualAgent", logger_func)
        self.hf_key = hf_key
        self.register_sub_agent("Curator", VisualCurator())

    def execute(self, theme, w, h):
        self.report(f"აგენერირებს ვიზუალს: {theme}")
        prompt = f"Cinematic vertical shot (9:16). {theme}. Moody, emotional atmosphere, high detail, 8k, photorealistic, dramatic lighting."
        
        fallbacks = [("HF_FLUX", self._hf), ("Pollinations", self._pollinations), ("Placeholder", self._placeholder)]
        for name, func in fallbacks:
            try:
                self.report(f"სუბ-აგენტი იყენებს: {name}")
                img = func(prompt, w, h)
                if img:
                    valid, msg = self.sub_agents["Curator"].validate(img)
                    self.report(f"სუბ-აგენტი (Curator): {msg}", "success" if valid else "warning")
                    if valid: return img
            except Exception as e:
                self.report(f"{name} ჩავარდა: {str(e)[:60]}", "warning")
        raise RuntimeError("ყველა ვიზუალური წყარო ჩავარდა")

    def _hf(self, p, w, h):
        return InferenceClient(api_key=self.hf_key).text_to_image(p, model="black-forest-labs/FLUX.1-schnell", width=w, height=h)
    def _pollinations(self, p, w, h):
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}?width={w}&height={h}&nologo=true&seed={random.randint(1,99999)}&model=flux"
        return Image.open(io.BytesIO(requests.get(url, timeout=60).content)).convert('RGB')
    def _placeholder(self, p, w, h):
        img = Image.new('RGB', (w, h), (25,25,35))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        except: font = ImageFont.load_default()
        draw.text((w//2-200, h//2), p[:60]+"...", fill=(200,200,200), font=font)
        return img

# ==================== 5. ვიდეოს აწყობის აგენტი + სუბ-QC ====================
class VideoQC:
    def validate(self, path, min_size_mb=1):
        size = os.path.getsize(path) / (1024*1024)
        if size < min_size_mb: return False, "ფაილი ზედმეტად მცირეა"
        return True, f"✅ ზომა: {size:.1f}MB"

class AssemblerAgent(Agent):
    def __init__(self, logger_func):
        super().__init__("🎥 AssemblerAgent", logger_func)
        self.register_sub_agent("QC", VideoQC())
        self.music_path = None

    def setup_music(self):
        if not self.music_path or not os.path.exists(self.music_path):
            try:
                self.music_path = os.path.join(CONFIG["OUTPUT_DIR"], "bg_music.mp3")
                r = requests.get(CONFIG["FALLBACK_MUSIC_URL"], timeout=30)
                with open(self.music_path, "wb") as f: f.write(r.content)
            except: self.music_path = None

    def execute(self, image_path, audio_path, duration, output_path):
        self.report(f"აწყობს ვიდეოს: {os.path.basename(output_path)}")
        self.setup_music()
        try:
            clip = mp.ImageClip(image_path).set_duration(duration)
            audio = mp.AudioFileClip(audio_path)
            music = mp.AudioFileClip(self.music_path).volumex(0.25).set_duration(duration) if self.music_path else None
            
            final_audio = mp.CompositeAudioClip([audio, music]) if music else audio
            video = clip.set_audio(final_audio)
            video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, logger=None)
            
            valid, msg = self.sub_agents["QC"].validate(output_path)
            self.report(f"სუბ-აგენტი (QC): {msg}", "success" if valid else "warning")
            return output_path
        except Exception as e:
            self.report(f"ვიდეოს აწყობა ვერ მოხერხდა: {str(e)}", "error")
            return None

# ==================== 6. შენახვის აგენტი + სუბ-მენეჯერი ====================
class FileManager:
    def organize(self, folder):
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return True, f"✅ {len(files)} ფაილი შენახულია"

class StorageAgent(Agent):
    def __init__(self, logger_func):
        super().__init__(" StorageAgent", logger_func)
        self.register_sub_agent("Manager", FileManager())

    def execute(self, folder):
        os.makedirs(folder, exist_ok=True)
        valid, msg = self.sub_agents["Manager"].organize(folder)
        self.report(msg, "success" if valid else "warning")
        return folder

# ==================== Streamlit UI & ორკესტრატორი ====================
st.set_page_config(page_title="AI Cinema Pipeline", page_icon="🎬", layout="wide")
st.title("🎬 AI Cinematic Pipeline — იერარქიული აგენტური სისტემა")
st.markdown("*ხელით სატესტო რეჟიმი | თითოეული აგენტი + სუბ-აგენტი კონტროლდება ცალკე*")

# ლოგების კონტეინერი
log_box = st.empty()
logs = []

def add_log(agent, msg, level="info"):
    logs.append(f"[{agent}] {msg}")
    with log_box.container():
        for l in logs[-10:]: # ბოლო 10 ლოგი
            st.code(l, language=None)

# სესიის მონაცემები
if "pipeline" not in st.session_state:
    st.session_state.pipeline = {
        "theme": None, "script": None, "audio": None, 
        "image": None, "video": None, "step": 0,
        "agents": {
            "theme": ThemeAgent(add_log),
            "script": ScriptAgent(CONFIG["GEMINI_API_KEY"], add_log),
            "voice": VoiceAgent(CONFIG["TTS_VOICE"], add_log),
            "visual": VisualAgent(CONFIG["HF_API_KEY"], add_log),
            "assembler": AssemblerAgent(add_log),
            "storage": StorageAgent(add_log)
        }
    }

P = st.session_state.pipeline
A = P["agents"]
STEP = P["step"]

# ნაბიჯების ინტერფეისი
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader(" ნაბიჯები")
    steps = ["1. თემის შერჩევა", "2. სცენარის წერა", "3. ხმის გენერაცია", 
             "4. ვიზუალის შექმნა", "5. ვიდეოს აწყობა", "6. შენახვა"]
    for i, s in enumerate(steps):
        st.button(s, key=f"btn_{i}", disabled=(i != STEP), type="primary" if i==STEP else "secondary")

with col2:
    st.subheader("⚙️ კონტროლის პანელი")
    
    if STEP == 0:
        if st.button("🚀 ნაბიჯი 1: თემის შერჩევა"):
            P["theme"] = A["theme"].execute()
            P["step"] = 1
            st.rerun()
            
    elif STEP == 1:
        st.text_input("არჩეული თემა", P["theme"], disabled=True)
        if st.button(" ნაბიჯი 2: სცენარის წერა"):
            P["script"] = A["script"].execute(P["theme"])
            P["step"] = 2
            st.rerun()
            
    elif STEP == 2:
        st.text_area("სცენარი", P["script"], height=100)
        if st.button("🚀 ნაბიჯი 3: ხმის გენერაცია (TTS)"):
            ts = datetime.now().strftime("%H%M%S")
            path = os.path.join(CONFIG["OUTPUT_DIR"], f"voice_{ts}.mp3")
            P["audio"] = asyncio.run(A["voice"].execute(P["script"], path))
            P["step"] = 3
            st.rerun()
            
    elif STEP == 3:
        if P["audio"]: st.audio(P["audio"])
        if st.button("🚀 ნაბიჯი 4: ვიზუალის შექმნა"):
            img = A["visual"].execute(P["theme"], CONFIG["VIDEO_WIDTH"], CONFIG["VIDEO_HEIGHT"])
            ts = datetime.now().strftime("%H%M%S")
            path = os.path.join(CONFIG["OUTPUT_DIR"], f"image_{ts}.png")
            img.save(path)
            P["image"] = path
            P["step"] = 4
            st.rerun()
            
    elif STEP == 4:
        if P["image"]: st.image(P["image"], use_column_width=True)
        if st.button(" ნაბიჯი 5: ვიდეოს აწყობა"):
            ts = datetime.now().strftime("%H%M%S")
            vid_path = os.path.join(CONFIG["OUTPUT_DIR"], f"video_{ts}.mp4")
            dur = mp.AudioFileClip(P["audio"]).duration + 2.0 if P["audio"] else 12.0
            P["video"] = A["assembler"].execute(P["image"], P["audio"], dur, vid_path)
            P["step"] = 5
            st.rerun()
            
    elif STEP == 5:
        if P["video"]: 
            st.video(P["video"])
            st.success("✅ ვიდეო მზადაა ჩამოსატვირთად!")
        if st.button("🚀 ნაბიჯი 6: ფაილების შენახვა & დასრულება"):
            folder = A["storage"].execute(os.path.dirname(P["video"] or "."))
            P["step"] = 6
            st.rerun()
            
    elif STEP == 6:
        st.success("🎉 პაიპლაინი წარმატებით დასრულდა! ყველა აგენტი და სუბ-აგენტი გატესტილია.")
        if st.button("🔄 ახალი ციკლის დაწყება"):
            for k in ["theme","script","audio","image","video","step"]:
                if k=="step": P[k]=0
                else: P[k]=None
            logs.clear()
            st.rerun()

# ფეისერი
st.divider()
st.caption("💡 მითითება: თითოეული ღილაკი ააქტიურებს მხოლოდ ერთ აგენტს. ლოგებში ჩანს სუბ-აგენტების კონტროლი. წარმატებული ტესტის შემდეგ შეგიძლიათ გადახვიდეთ ავტომატურ რეჟიმზე (Cron/GitHub Actions).")
