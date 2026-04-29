import streamlit as st
import os
import time
import random
import asyncio
import requests
import io
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import edge_tts
import moviepy.editor as mp
from huggingface_hub import InferenceClient
import imageio.plugins.ffmpeg

# შემოვიტანოთ ჩვენი ახალი სეიფი
from vault_system import VaultManager

# ==================== კონფიგურაცია ====================
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
os.environ["IMAGEIO_FFMPEG_BINARY"] = "/usr/bin/ffmpeg"

CONFIG = {
    "OUTPUT_DIR": "./output",
    "VIDEO_WIDTH": 1080,
    "VIDEO_HEIGHT": 1920,
    "FALLBACK_MUSIC_URL": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=ambient-piano-loop-114773.mp3"
}
os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)

# ==================== იერარქიული ლოგერი ====================
class HierarchicalLogger:
    def __init__(self, container):
        self.container = container
        self.entries = []

    def add(self, agent, msg, level="info", indent=0, sub=None):
        icons = {"info": "🔹", "success": "✅", "warning": "⚠️", "error": "❌", "start": "🚀", "end": "🏁"}
        icon = icons.get(level, "•")
        prefix = "  " * indent
        line = f"{prefix}  ↳ {sub}: {msg}" if sub else f"{prefix}{icon} {agent}: {msg}"
        self.entries.append(line)
        self._render()

    def _render(self):
        with self.container:
            st.markdown("**📊 სისტემური ლოგები (რეალურ დროში)**")
            st.code("\n".join(self.entries[-45:]), language="text")

# ==================== აგენტები (ახლა იღებენ Vault-ს) ====================
class ThemeResearcherAgent:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger

    def execute(self, direction):
        self.log.add("ThemeResearcherAgent", f"იწყებს კვლევას: {direction}", indent=1)
        key = self.vault.get_key("gemini_text")
        if not key: return "წვიმიანი ქალაქის სცენა (გასაღები არ არის)"
        
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"შექმენი 1 უნიკალური, ემოციური კინემატოგრაფიული თემა. მიმართულება: '{direction}'. მხოლოდ თემის სახელი."
        try: return model.generate_content(prompt).text.strip().replace('"', '')
        except: return "დაკარგული წერილი მაგიდაზე"

class ThemeAgent1:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger
    def execute(self, raw_theme):
        self.log.add("ThemeAgent1", f"ამუშავებს ემოციურ კონტექსტს...", indent=1)
        key = self.vault.get_key("gemini_text")
        if not key: return raw_theme
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"გაავრცე თემა: '{raw_theme}'. დაამატე პერსონაჟის შინაგანი განცდა და ატმოსფერო. 2-3 წინადადება."
        try: return model.generate_content(prompt).text.strip().replace('"', '')
        except: return raw_theme

class ThemeAgent2:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger
    def execute(self, processed_theme):
        self.log.add("ThemeAgent2", "ამატებს კინემატოგრაფიულ ჩარჩოს...", indent=1)
        key = self.vault.get_key("gemini_text")
        if not key: return processed_theme
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"გარდაქმენი ვიზუალურ სცენად 9:16-ისთვის: '{processed_theme}'. მიუთითე კომპოზიცია, განათება, ფერები."
        try: return model.generate_content(prompt).text.strip().replace('"', '')
        except: return processed_theme

class ThemeValidator1:
    def __init__(self, logger): self.log = logger
    def check(self, theme):
        self.log.add("ThemeValidator1", "ამოწმებს ტონსა და ემოციას...", indent=1, sub="Validator1")
        ok = any(w in theme.lower() for w in ["წვიმა","მარტო","დაკარგული","იმედი","შეხვედრა","მთვარე","სიყვარული","ფანჯარა","ჩრდილი","ხიდი","გზა","სიჩუმე"])
        self.log.add("ThemeValidator1", f"შედეგი: {'✅' if ok else '❌'}", indent=2, sub="Validator1")
        return ok

class ThemeValidator2:
    def __init__(self, logger): self.log = logger
    def check(self, theme):
        self.log.add("ThemeValidator2", "ამოწმებს სიგრძესა და ვიზუალიზაციას...", indent=1, sub="Validator2")
        sentences = [s.strip() for s in theme.split('.') if len(s.strip()) > 5]
        ok = 1 <= len(sentences) <= 4 and len(theme) > 15
        self.log.add("ThemeValidator2", f"შედეგი: {'✅' if ok else '❌'} ({len(sentences)} წინ.)", indent=2, sub="Validator2")
        return ok

class ThemeAgent:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger
        self.researcher = ThemeResearcherAgent(vault, logger)
        self.agent1 = ThemeAgent1(vault, logger)
        self.agent2 = ThemeAgent2(vault, logger)
        self.v1 = ThemeValidator1(logger)
        self.v2 = ThemeValidator2(logger)

    def execute(self):
        self.log.add("ThemeAgent", "დაიწყო თემის შერჩევის პროცესი...", "start")
        direction = "მელანქოლიური, რომანტიკული, ქალაქური ან ბუნებრივი სცენა"
        final = "წვიმიანი ქალაქის სცენა"
        for attempt in range(2):
            raw = self.researcher.execute(direction)
            processed = self.agent1.execute(raw)
            final = self.agent2.execute(processed)
            if self.v1.check(final) and self.v2.check(final):
                self.log.add("ThemeAgent", f"✅ საბოლოო თემა დამტკიცებულია", "success")
                return final
            direction += " (შენიშვნა: გააუმჯობესე ემოცია/სიგრძე)"
        self.log.add("ThemeAgent", "⚠️ მაქსიმალური ციკლები ამოიწურა", "warning")
        return final

class ScriptAgent:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger

    def execute(self, theme):
        self.log.add("ScriptAgent", "დაიწყო სცენარის წერა...", "start")
        key = self.vault.get_key("gemini_text")
        if not key: return "[შეცდომა: გასაღები არ არის სეიფში]"
        
        genai.configure(api_key=key)
        try:
            models = genai.list_models()
            candidates = [m.name.replace("models/","") for m in models if 'generateContent' in m.supported_generation_methods and ('flash' in m.name or 'pro' in m.name)]
            model_name = candidates[0] if candidates else "gemini-pro"
        except: model_name = "gemini-pro"
            
        self.log.add("ScriptAgent", f"ირჩევს მოდელს: {model_name}", indent=1)
        model = genai.GenerativeModel(model_name)
        prompt = f"დაწერე ემოციური მიკრო-ისტორია (2-3 წინ.) ქართულად. თემა: '{theme}'. სტილი: მელანქოლიური, კინემატოგრაფიული. პირდაპირ შედი სცენაში."
        
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.8})
            text = resp.text.strip().replace('"', '').replace('*', '')
            self.log.add("ScriptAgent", f"მიღებული ტექსტი: \"{text[:40]}...\"", indent=1)
            self.log.add("ScriptAgent", "✅ წარმატება! სცენარი დამუშავებულია.", "end")
            return text
        except Exception as e:
            self.log.add("ScriptAgent", f"❌ შეცდომა: {str(e)[:60]}", "error")
            return f"[შეცდომა: {str(e)[:50]}]"

class VoiceAgent:
    def __init__(self, logger): self.log = logger
    async def execute(self, text, output_path):
        self.log.add("VoiceAgent", "დაიწყო ხმოვანი ნარაციის გენერაცია...", "start")
        for voice in ["ka-GE-NinoNeural", "ka-GE-GiorgiNeural"]:
            try:
                await edge_tts.Communicate(text, voice).save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    dur = mp.AudioFileClip(output_path).duration
                    mp.AudioFileClip(output_path).close()
                    self.log.add("VoiceAgent", f"✅ წარმატება! ({voice}, {dur:.1f}წმ)", "end")
                    return output_path
            except: continue
        self.log.add("VoiceAgent", "❌ ყველა ხმა ჩავარდა.", "error")
        return None

class VisualAgent:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger

    def execute(self, theme, w, h):
        self.log.add("VisualAgent", "დაიწყო ვიზუალის გენერაცია...", "start")
        prompt = f"Cinematic vertical shot (9:16). {theme}. Moody, emotional, high detail, 8k, photorealistic."
        key = self.vault.get_key("hf_image")
        
        # თუ HF გასაღები არ არის, პირდაპირ Pollinations-ზე გადადის
        fallbacks = [("HF_FLUX", lambda p: InferenceClient(api_key=key).text_to_image(p, model="black-forest-labs/FLUX.1-schnell", width=w, height=h) if key else None)]
        if not key: fallbacks.append(("Pollinations", lambda p: Image.open(io.BytesIO(requests.get(f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}?width={w}&height={h}&nologo=true&seed={random.randint(1,99999)}&model=flux", timeout=60).content)).convert('RGB')))
        
        for name, func in fallbacks:
            try:
                img = func(prompt)
                if img:
                    self.log.add("VisualAgent", f"✅ დასრულდა. წყარო: {name}", "end")
                    return img
            except: continue
        raise RuntimeError("ვიზუალი ვერ შეიქმნა")

class AssemblerAgent:
    def __init__(self, logger):
        self.log = logger
        self.music_path = os.path.join(CONFIG["OUTPUT_DIR"], "bg_music.mp3")
        if not os.path.exists(self.music_path):
            try:
                with open(self.music_path, "wb") as f: f.write(requests.get(CONFIG["FALLBACK_MUSIC_URL"], timeout=30).content)
            except: self.music_path = None

    def execute(self, image_path, audio_path, duration, output_path):
        self.log.add("AssemblerAgent", "დაიწყო ვიდეოს აწყობა (FFmpeg)...", "start")
        image_path, audio_path, output_path = map(os.path.abspath, [image_path, audio_path, output_path])
        final_audio = audio_path
        
        if self.music_path and os.path.exists(self.music_path):
            final_audio = os.path.join(CONFIG["OUTPUT_DIR"], "mixed.mp3")
            res = subprocess.run(["/usr/bin/ffmpeg", "-y", "-i", audio_path, "-i", self.music_path, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first", "-c:a", "libmp3lame", "-q:a", "2", final_audio], capture_output=True)
            if res.returncode != 0: final_audio = audio_path

        cmd = ["/usr/bin/ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", final_audio, "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            self.log.add("AssemblerAgent", f"✅ დასრულდა ({os.path.getsize(output_path)/(1024*1024):.1f}MB)", "end")
            return output_path
        self.log.add("AssemblerAgent", f"❌ ffmpeg შეცდომა: {res.stderr[:60]}", "error")
        return None

class StorageAgent:
    def __init__(self, logger): self.log = logger
    def execute(self, folder):
        self.log.add("StorageAgent", "დაიწყო ფაილების მენეჯმენტი...", "start")
        os.makedirs(folder, exist_ok=True)
        self.log.add("StorageAgent", f"✅ {len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])} ფაილი შენახულია", "end")
        return folder

# ==================== Streamlit UI ====================
st.set_page_config(page_title="🎬 AI Cinema Pipeline", page_icon="🎬", layout="wide")
st.title("🎬 AI Cinematic Pipeline")
st.markdown("*KeyVault System | ჭკვიანი რესურსების განაწილება*")

# ინიციალიზაცია
if "vault" not in st.session_state:
    st.session_state.vault = VaultManager()

vault = st.session_state.vault
logger = None # ინიციალიზდება ქვემოთ

# 1. მარცხენა მენიუ (Sidebar) - API სეიფი
with st.sidebar:
    st.header("🔐 API სეიფი")
    st.markdown("აქ შეგიძლია შეინახო და შეამოწმო გასაღებები.")
    
    # Gemini Key
    st.subheader("🧠 Google Gemini (ტექსტი)")
    current_gemini = vault.get_key("gemini_text")
    new_gemini = st.text_input("Gemini API Key", value=current_gemini, type="password")
    
    if st.button("💾 შენახვა და შემოწმება (Gemini)", key="btn_gemini"):
        if new_gemini != current_gemini:
            is_valid, msg = vault.validate_and_test("gemini_text", new_gemini)
            if is_valid:
                vault.save_key("gemini_text", new_gemini)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        else:
            st.info("გასაღები უცვლელია.")

    # HuggingFace Key
    st.subheader("🎨 HuggingFace (ვიზუალი)")
    current_hf = vault.get_key("hf_image")
    new_hf = st.text_input("HuggingFace API Key", value=current_hf, type="password")
    
    if st.button("💾 შენახვა და შემოწმება (HF)", key="btn_hf"):
        if new_hf != current_hf:
            is_valid, msg = vault.validate_and_test("hf_image", new_hf)
            if is_valid:
                vault.save_key("hf_image", new_hf)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        else:
            st.info("ტოკენი უცვლელია.")

    st.divider()
    st.caption("⚠️ გასაღებები ინახება ლოკალურ `vault_config.json` ფაილში.")

# 2. მთავარი ინტერფეისი
col_ui, col_log = st.columns([1, 1])

with col_log:
    log_container = st.empty()
    if "logger" not in st.session_state: 
        st.session_state.logger = HierarchicalLogger(log_container)
    logger = st.session_state.logger

with col_ui:
    st.subheader("⚙️ ნაბიჯების მართვა")
    if "step" not in st.session_state: st.session_state.step = 0
    if "data" not in st.session_state: st.session_state.data = {}

    P = st.session_state
    steps = [("1. თემის შერჩევა","theme"),("2. სცენარის წერა","script"),("3. ხმის გენერაცია","audio"),("4. ვიზუალის შექმნა","image"),("5. ვიდეოს აწყობა","video"),("6. შენახვა","storage")]

    for i, (label, key) in enumerate(steps):
        disabled = i != P.step
        if st.button(label, key=f"btn_{i}", disabled=disabled, type="primary" if i==P.step else "secondary"):
            try:
                # ყველა აგენტს გადავცემთ vault-ს
                if i == 0: P.data["theme"] = ThemeAgent(vault, logger).execute()
                elif i == 1: P.data["script"] = ScriptAgent(vault, logger).execute(P.data["theme"])
                elif i == 2:
                    ts = datetime.now().strftime("%H%M%S")
                    P.data["audio"] = asyncio.run(VoiceAgent(logger).execute(P.data["script"], os.path.join(CONFIG["OUTPUT_DIR"], f"voice_{ts}.mp3")))
                elif i == 3:
                    img = VisualAgent(vault, logger).execute(P.data["theme"], CONFIG["VIDEO_WIDTH"], CONFIG["VIDEO_HEIGHT"])
                    ts = datetime.now().strftime("%H%M%S")
                    path = os.path.join(CONFIG["OUTPUT_DIR"], f"image_{ts}.png")
                    img.save(path); P.data["image"] = path
                elif i == 4:
                    if not P.data.get("audio"): logger.add("SYSTEM", "❌ ხმა არ არსებობს", "error")
                    else:
                        dur = mp.AudioFileClip(P.data["audio"]).duration + 2.0; mp.AudioFileClip(P.data["audio"]).close()
                        ts = datetime.now().strftime("%H%M%S")
                        P.data["video"] = AssemblerAgent(logger).execute(P.data["image"], P.data["audio"], dur, os.path.join(CONFIG["OUTPUT_DIR"], f"video_{ts}.mp4"))
                elif i == 5: StorageAgent(logger).execute(os.path.dirname(P.data["video"] or "."))
                if i != 4 or P.data.get("video"): P.step = i + 1
            except Exception as e: logger.add("SYSTEM", f"❌ შეცდომა ნაბიჯზე {i+1}: {str(e)}", "error")

    st.divider()
    st.subheader("📦 მიმდინარე შედეგები")
    if P.data.get("theme"): st.info(f"🎭 თემა: {P.data['theme']}")
    if P.data.get("script"): st.text_area("📜 სცენარი", P.data["script"], height=80)
    if P.data.get("audio"): st.audio(P.data["audio"])
    if P.data.get("image"): st.image(P.data["image"], use_column_width=True)
    if P.data.get("video"): 
        st.video(P.data["video"])
        st.success("✅ ვიდეო მზადაა!")
        if st.button("🔄 ახალი ციკლი"): P.step, P.data, logger.entries = 0, {}, []; st.rerun()

st.caption("💡 მითითება: გასაღებები იმართება Sidebar-ის მეშვეობით. სისტემა ავტომატურად ამოწმებს მათ ვალიდურობას.")
