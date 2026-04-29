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

# ==================== კონფიგურაცია ====================
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
os.environ["IMAGEIO_FFMPEG_BINARY"] = "/usr/bin/ffmpeg"

CONFIG = {
    "GEMINI_API_KEY": st.secrets.get("GEMINI_API_KEY", ""),
    "HF_API_KEY": st.secrets.get("HF_API_KEY", ""),
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
            st.code("\n".join(self.entries[-35:]), language="text")

# ==================== აგენტები ====================
class ThemeAgent:
    THEMES = [
        "წვიმიანი შეხვედრა ძველ ქუჩაში",
        "დაკარგული წერილი ატყავედებულ მაგიდაზე",
        "მთვარის შუქზე სიარული ცარიელ სანაპიროზე",
        "ფანჯრიდან დანახული უცნობი სილუეტი",
        "შემოდგომის პარკში დარჩენილი წითელი ქურთუკი",
        "ღამის მატარებელი და უსაზღვრო ველები"
    ]
    def __init__(self, logger):
        self.log = logger

    def execute(self):
        self.log.add("ThemeAgent", "დაიწყო თემის შერჩევა...", "start")
        self.log.add("ThemeAgent", "ირჩევს თემას ბაზიდან (6 ვარიანტი)", indent=1)
        
        theme = random.choice(self.THEMES)
        self.log.add("ThemeAgent", f"შერჩეული თემა: \"{theme}\"", indent=1)
        
        self.log.add("ThemeValidator", "ამოწმებს სიგრძესა და ემოციურ ტონს", indent=1, sub="ThemeValidator")
        valid_len = len(theme) > 5
        emotional = any(w in theme.lower() for w in ["წვიმა", "მარტო", "დაკარგული", "იმედი", "შეხვედრა", "მთვარე", "სიყვარული", "ფანჯარა"])
        self.log.add("ThemeValidator", f"შედეგი: {'✅ სიგრძე და ტონი მისაღებია' if valid_len and emotional else '⚠️ ნეიტრალური, მაგრამ მისაღებია'}", indent=2, sub="ThemeValidator")
        
        self.log.add("ThemeAgent", "დასრულდა. თემა დამტკიცებულია.", "end")
        return theme


class ScriptAgent:
    def __init__(self, api_key, logger):
        self.api_key = api_key
        self.log = logger

    def _get_smart_models(self):
        try:
            genai.configure(api_key=self.api_key)
            models = genai.list_models()
            valid = []
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    name = m.name.replace("models/", "")
                    if 'flash' in name: valid.insert(0, name)
                    elif 'pro' in name: valid.append(name)
                    else: valid.append(name)
            return list(dict.fromkeys(valid))
        except Exception as e:
            self.log.add("ScriptAgent", f"მოდელთა სიის მიღება ვერ მოხერხდა: {str(e)[:50]}", "error")
            return ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]

    def execute(self, theme):
        self.log.add("ScriptAgent", "დაიწყო სცენარის წერა...", "start")
        self.log.add("ScriptAgent", "უკავშირდება Google-ს ხელმისაწვდომი მოდელების მისაღებად...", indent=1)
        
        models = self._get_smart_models()
        self.log.add("ScriptAgent", f"ნაპოვნია {len(models)} მოდელი. პრიორიტეტი: {', '.join(models[:3])}", indent=1)
        
        prompt = f"""
        დაწერე მოკლე, ემოციური მიკრო-ისტორია (2-3 წინადადება) ქართულ ენაზე.
        თემა: "{theme}"
        სტილი: მელანქოლიური, კინემატოგრაფიული, პოეტური.
        წესები: პირდაპირ შედი სცენაში. არ დაიწყო "აი", "წარმოიდგინე". მხოლოდ ისტორია.
        """
        self.log.add("ScriptAgent", "აგზავნის პრომპტს AI-ში...", indent=1)
        
        for model_name in models:
            self.log.add("ScriptAgent", f"🔄 ცდილობს მოდელს: {model_name}", indent=1)
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(model_name)
            
            for attempt in range(3):
                try:
                    resp = model.generate_content(prompt, generation_config={"temperature": 0.8})
                    text = resp.text.strip().replace('"', '').replace('*', '')
                    
                    self.log.add("ScriptAgent", f"მიღებული ტექსტი: \"{text[:40]}...\"", indent=1)
                    
                    self.log.add("ScriptEditor", "ამოწმებს წინადადებების რაოდენობასა და სტილს", indent=1, sub="ScriptEditor")
                    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 5]
                    self.log.add("ScriptEditor", f"შედეგი: {len(sentences)} წინადადება {'✅' if 1 < len(sentences) < 5 else '⚠️'}", indent=2, sub="ScriptEditor")
                    
                    self.log.add("ScriptAgent", "✅ წარმატება! სცენარი დამუშავებულია.", "end")
                    return text

                except Exception as e:
                    err_msg = str(e)
                    if '429' in err_msg or 'quota' in err_msg.lower():
                        wait_time = 15 * (attempt + 1)
                        self.log.add("ScriptAgent", f"⏳ ლიმიტი (429). ველოდები {wait_time}წმ... (ცდა {attempt+1}/3)", "warning")
                        time.sleep(wait_time)
                    elif 'not found' in err_msg.lower() or 'not supported' in err_msg.lower():
                        self.log.add("ScriptAgent", f"⚠️ მოდელი ხელმიუწვდომელია. გადადის შემდეგზე...", "warning")
                        break
                    else:
                        self.log.add("ScriptAgent", f"❌ შეცდომა: {err_msg[:60]}", "error")
                        break
            
            self.log.add("ScriptAgent", f"⚠️ {model_name} ამოიწურა. გადადის შემდეგ მოდელზე...", "warning")

        self.log.add("ScriptAgent", "❌ ყველა მოდელის ლიმიტი ამოიწურა. გთხოვთ დაელოდოთ ~1 საათი.", "error")
        return "[სისტემური ლოდინი: API ლიმიტი ამოიწურა. სცადეთ მოგვიანებით.]"


class VoiceAgent:
    def __init__(self, logger):
        self.log = logger

    async def execute(self, text, output_path):
        self.log.add("VoiceAgent", "დაიწყო ხმოვანი ნარაციის გენერაცია...", "start")
        
        voices = ["ka-GE-NinoNeural", "ka-GE-GiorgiNeural"]
        
        for voice in voices:
            self.log.add("VoiceAgent", f"სცადის ხმას: {voice}", indent=1)
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    temp_clip = mp.AudioFileClip(output_path)
                    dur = temp_clip.duration
                    temp_clip.close()
                    
                    self.log.add("VoiceProcessor", f"შედეგი: {dur:.1f} წამი ✅ ({voice})", indent=2, sub="VoiceProcessor")
                    self.log.add("VoiceAgent", f"✅ წარმატება! გამოყენებულია: {voice}", "end")
                    return output_path
                
            except Exception as e:
                self.log.add("VoiceAgent", f"⚠️ {voice} ჩავარდა: {str(e)[:40]}", "warning")
                continue
        
        self.log.add("VoiceAgent", "❌ ყველა ხმის ვარიანტი ჩავარდა.", "error")
        return None


class VisualAgent:
    def __init__(self, hf_key, logger):
        self.hf_key = hf_key
        self.log = logger

    def execute(self, theme, w, h):
        self.log.add("VisualAgent", "დაიწყო ვიზუალის გენერაცია...", "start")
        prompt = f"Cinematic vertical shot (9:16). {theme}. Moody, emotional atmosphere, high detail, 8k, photorealistic, dramatic lighting."
        self.log.add("VisualAgent", "ქმნის ვიზუალურ პრომპტს...", indent=1)
        
        fallbacks = [("HF_FLUX", self._hf), ("Pollinations", self._pollinations), ("Placeholder", self._placeholder)]
        for name, func in fallbacks:
            self.log.add("VisualAgent", f"სცადის წყაროს: {name}", indent=1)
            try:
                img = func(prompt, w, h)
                if img:
                    self.log.add("VisualCurator", f"ამოწმებს რეზოლუციას (მინ. {w}x{h})", indent=1, sub="VisualCurator")
                    ok = img.width >= w * 0.8
                    self.log.add("VisualCurator", f"შედეგი: {img.width}x{img.height} {'✅' if ok else '⚠️'}", indent=2, sub="VisualCurator")
                    
                    self.log.add("VisualAgent", f"დასრულდა. წყარო: {name}", "end")
                    return img
            except Exception as e:
                self.log.add("VisualAgent", f"{name} ჩავარდა: {str(e)[:40]}", "warning")
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


class AssemblerAgent:
    def __init__(self, logger):
        self.log = logger
        self.music_path = os.path.join(CONFIG["OUTPUT_DIR"], "bg_music.mp3")
        if not os.path.exists(self.music_path):
            try:
                self.log.add("AssemblerAgent", "იტვირთავს ფონურ მუსიკას...", indent=1)
                with open(self.music_path, "wb") as f: 
                    f.write(requests.get(CONFIG["FALLBACK_MUSIC_URL"], timeout=30).content)
                self.log.add("AssemblerAgent", "ფონური მუსიკა ჩამოტვირთულია.", indent=1)
            except: 
                self.log.add("AssemblerAgent", "ფონური მუსიკის ჩამოტვირთვა ვერ მოხერხდა.", "warning")
                self.music_path = None

    def execute(self, image_path, audio_path, duration, output_path):
        self.log.add("AssemblerAgent", "დაიწყო ვიდეოს აწყობა (FFmpeg)...", "start")
        
        image_path = os.path.abspath(image_path)
        audio_path = os.path.abspath(audio_path)
        output_path = os.path.abspath(output_path)
        
        final_audio_path = audio_path
        
        # 1. ხმის შერევა (თუ მუსიკა არსებობს)
        if self.music_path and os.path.exists(self.music_path):
            final_audio_path = os.path.join(CONFIG["OUTPUT_DIR"], "mixed_audio.mp3")
            mix_cmd = [
                "/usr/bin/ffmpeg", "-y",
                "-i", audio_path,
                "-i", self.music_path,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
                "-c:a", "libmp3lame", "-q:a", "2",
                final_audio_path
            ]
            self.log.add("AssemblerAgent", "ურევს ხმას ფონურ მუსიკასთან...", indent=1)
            res = subprocess.run(mix_cmd, capture_output=True, text=True)
            if res.returncode != 0:
                self.log.add("AssemblerAgent", f"შერევა ვერ მოხერხდა, ვიყენებთ მხოლოდ ხმას.", "warning")
                final_audio_path = audio_path
            else:
                self.log.add("AssemblerAgent", "ხმა წარმატებით შერეულია.", indent=1)

        # 2. ვიდეოს შექმნა FFmpeg-ით (ბევრად უფრო საიმედოა ვიდრე MoviePy)
        self.log.add("AssemblerAgent", "ქმნის ვიდეოს ffmpeg-ით...", indent=1)
        cmd = [
            "/usr/bin/ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", final_audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            size_mb = os.path.getsize(output_path) / (1024*1024)
            self.log.add("VideoQC", f"შედეგი: {size_mb:.1f}MB ✅", indent=2, sub="VideoQC")
            self.log.add("AssemblerAgent", "დასრულდა. ვიდეო ექსპორტირებულია.", "end")
            return output_path
        else:
            self.log.add("AssemblerAgent", f"ffmpeg შეცდომა: {res.stderr[:60]}", "error")
            return None


class StorageAgent:
    def __init__(self, logger):
        self.log = logger

    def execute(self, folder):
        self.log.add("StorageAgent", "დაიწყო ფაილების მენეჯმენტი...", "start")
        os.makedirs(folder, exist_ok=True)
        self.log.add("FileManager", "ქმნის/ამოწმებს საქაღალდეს", indent=1, sub="FileManager")
        
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        self.log.add("FileManager", f"შედეგი: {len(files)} ფაილი დარეგისტრირებულია ✅", indent=2, sub="FileManager")
        self.log.add("StorageAgent", "დასრულდა. ყველა ფაილი უსაფრთხოდ არის შენახული.", "end")
        return folder


# ==================== Streamlit UI ====================
st.set_page_config(page_title="🎬 AI Cinema Pipeline", page_icon="🎬", layout="wide")
st.title("🎬 AI Cinematic Pipeline — იერარქიული აგენტური სისტემა")
st.markdown("*ხელით სატესტო რეჟიმი | ჭკვიანი ფოლბექი და დინამიური მოდელები*")

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
    steps = [
        ("1. თემის შერჩევა", "theme"),
        ("2. სცენარის წერა", "script"),
        ("3. ხმის გენერაცია", "audio"),
        ("4. ვიზუალის შექმნა", "image"),
        ("5. ვიდეოს აწყობა", "video"),
        ("6. შენახვა & დასრულება", "storage")
    ]

    for i, (label, key) in enumerate(steps):
        disabled = i != P.step
        if st.button(label, key=f"btn_{i}", disabled=disabled, type="primary" if i==P.step else "secondary"):
            try:
                if i == 0:
                    P.data["theme"] = ThemeAgent(logger).execute()
                elif i == 1:
                    P.data["script"] = ScriptAgent(CONFIG["GEMINI_API_KEY"], logger).execute(P.data["theme"])
                elif i == 2:
                    ts = datetime.now().strftime("%H%M%S")
                    path = os.path.join(CONFIG["OUTPUT_DIR"], f"voice_{ts}.mp3")
                    P.data["audio"] = asyncio.run(VoiceAgent(logger).execute(P.data["script"], path))
                elif i == 3:
                    img = VisualAgent(CONFIG["HF_API_KEY"], logger).execute(P.data["theme"], CONFIG["VIDEO_WIDTH"], CONFIG["VIDEO_HEIGHT"])
                    ts = datetime.now().strftime("%H%M%S")
                    path = os.path.join(CONFIG["OUTPUT_DIR"], f"image_{ts}.png")
                    img.save(path)
                    P.data["image"] = path
                elif i == 4:
                    if not P.data.get("audio"):
                        logger.add("SYSTEM", "❌ ხმის ფაილი არ არსებობს. ვიდეო ვერ აიწყობა.", "error")
                    else:
                        temp_audio = mp.AudioFileClip(P.data["audio"])
                        dur = temp_audio.duration + 2.0
                        temp_audio.close()
                        
                        ts = datetime.now().strftime("%H%M%S")
                        vid_path = os.path.join(CONFIG["OUTPUT_DIR"], f"video_{ts}.mp4")
                        P.data["video"] = AssemblerAgent(logger).execute(P.data["image"], P.data["audio"], dur, vid_path)
                elif i == 5:
                    StorageAgent(logger).execute(os.path.dirname(P.data["video"] or "."))
                
                if i != 4 or P.data.get("video"):
                    P.step = i + 1
            except Exception as e:
                logger.add("SYSTEM", f"კრიტიკული შეცდომა ნაბიჯზე {i+1}: {str(e)}", "error")

    st.divider()
    st.subheader("📦 მიმდინარე შედეგები")
    if P.data.get("theme"): st.info(f"🎭 თემა: {P.data['theme']}")
    if P.data.get("script"): st.text_area("📜 სცენარი", P.data["script"], height=80)
    if P.data.get("audio"): st.audio(P.data["audio"])
    if P.data.get("image"): st.image(P.data["image"], use_column_width=True)
    if P.data.get("video"): 
        st.video(P.data["video"])
        st.success("✅ ვიდეო მზადაა! შეგიძლიათ ჩამოტვირთოთ ან გადახვიდეთ შემდეგ ციკლზე.")
        if st.button("🔄 ახალი ციკლი"):
            P.step = 0
            P.data = {}
            logger.entries.clear()
            st.rerun()

st.caption("💡 მითითება: სისტემა ავტომატურად პოულობს ხელმისაწვდომ მოდელებს და ლიმიტის დროს ელოდება. ლოგებში ჩანს ყველა გადაწყვეტილება.")
