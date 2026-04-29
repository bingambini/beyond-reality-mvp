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

# ჩვენი ახალი სეიფი
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

# ==================== აგენტები (განახლებული) ====================
class ThemeResearcherAgent:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
    def execute(self, direction):
        self.log.add("ThemeResearcherAgent", f"კვლევა: {direction}", indent=1)
        key = self.vault.get_key("gemini_text", 0)
        if not key: return "წვიმიანი ქალაქის სცენა (გასაღები არ არის)"
        genai.configure(api_key=key)
        try:
            return genai.GenerativeModel("gemini-1.5-flash").generate_content(
                f"შექმენი 1 უნიკალური კინემატოგრაფიული თემა. მიმართულება: '{direction}'."
            ).text.strip().replace('"', '')
        except: return "დაკარგული წერილი მაგიდაზე"

class ThemeAgent1:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
    def execute(self, raw):
        self.log.add("ThemeAgent1", "ემოციური კონტექსტი...", indent=1)
        key = self.vault.get_key("gemini_text", 0)
        if not key: return raw
        genai.configure(api_key=key)
        try: return genai.GenerativeModel("gemini-1.5-flash").generate_content(
            f"გაავრცე: '{raw}'. დაამატე პერსონაჟის განცდა. 2-3 წინ."
        ).text.strip().replace('"', '')
        except: return raw

class ThemeAgent2:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
    def execute(self, proc):
        self.log.add("ThemeAgent2", "კინემატოგრაფიული ჩარჩო...", indent=1)
        key = self.vault.get_key("gemini_text", 0)
        if not key: return proc
        genai.configure(api_key=key)
        try: return genai.GenerativeModel("gemini-1.5-flash").generate_content(
            f"გარდაქმენი 9:16 ვიზუალურ სცენად: '{proc}'. კომპოზიცია, განათება, ფერები."
        ).text.strip().replace('"', '')
        except: return proc

class ThemeValidator1:
    def __init__(self, logger): self.log = logger
    def check(self, t):
        self.log.add("ThemeValidator1", "ტონი/ემოცია...", indent=1, sub="V1")
        ok = any(w in t.lower() for w in ["წვიმა","მარტო","დაკარგული","იმედი","შეხვედრა","მთვარე","სიყვარული","ფანჯარა","ჩრდილი","ხიდი","გზა","სიჩუმე"])
        self.log.add("ThemeValidator1", f"შედეგი: {'✅' if ok else '❌'}", indent=2, sub="V1"); return ok

class ThemeValidator2:
    def __init__(self, logger): self.log = logger
    def check(self, t):
        self.log.add("ThemeValidator2", "სიგრძე/ვიზუალი...", indent=1, sub="V2")
        s = [x.strip() for x in t.split('.') if len(x.strip()) > 5]
        ok = 1 <= len(s) <= 4 and len(t) > 15
        self.log.add("ThemeValidator2", f"შედეგი: {'✅' if ok else '❌'} ({len(s)} წინ.)", indent=2, sub="V2"); return ok

class ThemeAgent:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
        self.res = ThemeResearcherAgent(vault, logger)
        self.a1 = ThemeAgent1(vault, logger)
        self.a2 = ThemeAgent2(vault, logger)
        self.v1 = ThemeValidator1(logger)
        self.v2 = ThemeValidator2(logger)
    def execute(self):
        self.log.add("ThemeAgent", "თემის შერჩევა...", "start")
        d = "მელანქოლიური, რომანტიკული, ქალაქური ან ბუნებრივი სცენა"
        final = "წვიმიანი ქალაქის სცენა"
        for _ in range(2):
            raw = self.res.execute(d)
            p1 = self.a1.execute(raw)
            final = self.a2.execute(p1)
            if self.v1.check(final) and self.v2.check(final):
                self.log.add("ThemeAgent", "✅ თემა დამტკიცებულია", "success"); return final
            d += " (შენიშვნა: გააუმჯობესე ემოცია/სიგრძე)"
        self.log.add("ThemeAgent", "⚠️ ციკლები ამოიწურა", "warning"); return final

class ScriptAgent:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
    def execute(self, theme):
        self.log.add("ScriptAgent", "სცენარის წერა...", "start")
        key = self.vault.get_key("gemini_text", 0)
        if not key: return "[შეცდომა: გასაღები არ არის სეიფში]"
        genai.configure(api_key=key)
        try:
            models = genai.list_models()
            cands = [m.name.replace("models/","") for m in models if 'generateContent' in m.supported_generation_methods and ('flash' in m.name or 'pro' in m.name)]
            m_name = cands[0] if cands else "gemini-pro"
        except: m_name = "gemini-pro"
        self.log.add("ScriptAgent", f"მოდელი: {m_name}", indent=1)
        try:
            txt = genai.GenerativeModel(m_name).generate_content(
                f"დაწერე ემოციური მიკრო-ისტორია (2-3 წინ.) ქართულად. თემა: '{theme}'. სტილი: მელანქოლიური, კინემატოგრაფიული.",
                generation_config={"temperature": 0.8}
            ).text.strip().replace('"', '').replace('*', '')
            self.log.add("ScriptAgent", f"ტექსტი: \"{txt[:40]}...\"", indent=1)
            self.log.add("ScriptAgent", "✅ სცენარი მზადაა.", "end"); return txt
        except Exception as e:
            self.log.add("ScriptAgent", f"❌ {str(e)[:60]}", "error"); return f"[შეცდომა]"

class VoiceAgent:
    def __init__(self, logger): self.log = logger
    async def execute(self, text, out):
        self.log.add("VoiceAgent", "ხმის გენერაცია...", "start")
        for v in ["ka-GE-NinoNeural", "ka-GE-GiorgiNeural"]:
            try:
                await edge_tts.Communicate(text, v).save(out)
                if os.path.exists(out) and os.path.getsize(out) > 0:
                    dur = mp.AudioFileClip(out).duration; mp.AudioFileClip(out).close()
                    self.log.add("VoiceAgent", f"✅ ({v}, {dur:.1f}წმ)", "end"); return out
            except: continue
        self.log.add("VoiceAgent", "❌ ხმა ჩავარდა.", "error"); return None

class VisualAgent:
    def __init__(self, vault, logger):
        self.vault = vault; self.log = logger
    def execute(self, theme, w, h):
        self.log.add("VisualAgent", "ვიზუალის გენერაცია...", "start")
        prompt = f"Cinematic vertical shot (9:16). {theme}. Moody, emotional, high detail, 8k."
        key = self.vault.get_key("hf_image", 0)
        fallbacks = [("HF_FLUX", lambda p: InferenceClient(api_key=key).text_to_image(p, model="black-forest-labs/FLUX.1-schnell", width=w, height=h) if key else None)]
        if not key: fallbacks.append(("Pollinations", lambda p: Image.open(io.BytesIO(requests.get(f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}?width={w}&height={h}&nologo=true&seed={random.randint(1,99999)}&model=flux", timeout=60).content)).convert('RGB')))
        for name, func in fallbacks:
            try:
                img = func(prompt)
                if img: self.log.add("VisualAgent", f"✅ ({name})", "end"); return img
            except: continue
        raise RuntimeError("ვიზუალი ვერ შეიქმნა")

class AssemblerAgent:
    def __init__(self, logger):
        self.log = logger
        self.m_path = os.path.join(CONFIG["OUTPUT_DIR"], "bg_music.mp3")
        if not os.path.exists(self.m_path):
            try:
                with open(self.m_path, "wb") as f: f.write(requests.get(CONFIG["FALLBACK_MUSIC_URL"], timeout=30).content)
            except: self.m_path = None
    def execute(self, img_p, aud_p, dur, out_p):
        self.log.add("AssemblerAgent", "ვიდეოს აწყობა...", "start")
        img_p, aud_p, out_p = map(os.path.abspath, [img_p, aud_p, out_p])
        fin_aud = aud_p
        if self.m_path and os.path.exists(self.m_path):
            fin_aud = os.path.join(CONFIG["OUTPUT_DIR"], "mixed.mp3")
            res = subprocess.run(["/usr/bin/ffmpeg", "-y", "-i", aud_p, "-i", self.m_path, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first", "-c:a", "libmp3lame", "-q:a", "2", fin_aud], capture_output=True)
            if res.returncode != 0: fin_aud = aud_p
        cmd = ["/usr/bin/ffmpeg", "-y", "-loop", "1", "-i", img_p, "-i", fin_aud, "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", out_p]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            self.log.add("AssemblerAgent", f"✅ ({os.path.getsize(out_p)/(1024*1024):.1f}MB)", "end"); return out_p
        self.log.add("AssemblerAgent", f"❌ {res.stderr[:60]}", "error"); return None

class StorageAgent:
    def __init__(self, logger): self.log = logger
    def execute(self, folder):
        self.log.add("StorageAgent", "მენეჯმენტი...", "start")
        os.makedirs(folder, exist_ok=True)
        self.log.add("StorageAgent", f"✅ {len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])} ფაილი", "end"); return folder

# ==================== Streamlit UI ====================
st.set_page_config(page_title="🎬 AI Cinema Pipeline", page_icon="🎬", layout="wide")

# ინიციალიზაცია
if "vault" not in st.session_state: st.session_state.vault = VaultManager()
if "show_vault" not in st.session_state: st.session_state.show_vault = False
if "vault_inputs" not in st.session_state: st.session_state.vault_inputs = {}

vault = st.session_state.vault
logger = None

# მარცხენა მენიუ
with st.sidebar:
    st.header("🎛️ სისტემის მართვა")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 პაიპლაინი", use_container_width=True, type="primary" if not st.session_state.show_vault else "secondary"):
            st.session_state.show_vault = False; st.rerun()
    with c2:
        if st.button("🔐 სეიფი", use_container_width=True, type="primary" if st.session_state.show_vault else "secondary"):
            st.session_state.show_vault = True; st.rerun()
    st.divider()
    st.caption("ვ2.0 | ცენტრალური გასაღებთა მენეჯერი")

# ლოგების კონტეინერი
col_log = st.empty()
if "logger_obj" not in st.session_state:
    st.session_state.logger_obj = HierarchicalLogger(col_log)
logger = st.session_state.logger_obj

# ხედების გადართვა
if st.session_state.show_vault:
    # === 🔐 სეიფის ხედი ===
    st.title("🔐 ცენტრალური API სეიფი")
    st.markdown("აქ მართავთ ყველა პლატფორმის გასაღებსა და ლინკებს. სისტემა ავტომატურად ირჩევს მუშა გასაღებს.")
    
    # სესიის ინიციალიზაცია თუ ცარიელია
    if not st.session_state.vault_inputs:
        for svc_id, svc_data in vault.config.items():
            for i in range(svc_data["count"]):
                st.session_state.vault_inputs[f"{svc_id}_{i}"] = vault.config[svc_id]["keys"][i]

    for svc_id, svc_data in vault.config.items():
        with st.expander(f"{svc_data['label']}", expanded=True):
            is_link = svc_data["type"] == "link"
            for i in range(svc_data["count"]):
                c1, c2 = st.columns([3, 1])
                idx = f"{svc_id}_{i}"
                with c1:
                    lbl = f"#{i+1}"
                    if is_link:
                        val = st.text_input(lbl, value=st.session_state.vault_inputs.get(idx, ""), key=idx, placeholder="https://github.com/user/repo")
                    else:
                        val = st.text_input(lbl, value=st.session_state.vault_inputs.get(idx, ""), key=idx, type="password", placeholder="sk-... ან hf_...")
                    st.session_state.vault_inputs[idx] = val
                with c2:
                    if st.button("🔍 შემოწმება", key=f"chk_{idx}"):
                        ok, msg = vault.validate_key(svc_id, val)
                        if ok: st.success(msg)
                        else: st.error(msg)
    
    if st.button("💾 ყველაფრის შენახვა სეიფში", type="primary", use_container_width=True):
        for svc_id, svc_data in vault.config.items():
            for i in range(svc_data["count"]):
                vault.update_key(svc_id, i, st.session_state.vault_inputs.get(f"{svc_id}_{i}", ""))
        if vault.save_config():
            st.success("✅ ყველა გასაღები და ლინკი წარმატებით შენახულია!"); st.rerun()
        else: st.error("❌ შენახვა ვერ მოხერხდა.")

else:
    # === 🚀 პაიპლაინის ხედი ===
    st.title("🎬 AI Cinematic Pipeline")
    st.markdown("*ავტომატური კონტენტის ფაბრიკა | KeyVault v2.0*")
    
    col_ui, col_log_area = st.columns([1, 1])
    with col_log_area: logger._render()
        
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
                except Exception as e: logger.add("SYSTEM", f"❌ შეცდომა {i+1}: {str(e)}", "error")

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

    st.caption("💡 მითითება: გასაღებები მართვება მარცხენა მენიუში 'სეიფი' ტაბით.")
