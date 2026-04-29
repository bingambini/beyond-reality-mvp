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

# ==================== ლოგერი ====================
class HierarchicalLogger:
    def __init__(self, container):
        self.container = container
        self.entries = []
    def add(self, agent, msg, level="info", indent=0, sub=None):
        icons = {"info":"🔹","success":"✅","warning":"⚠️","error":"❌","start":"🚀","end":"🏁"}
        icon = icons.get(level, "•")
        prefix = "  "*indent
        line = f"{prefix}  ↳ {sub}: {msg}" if sub else f"{prefix}{icon} {agent}: {msg}"
        self.entries.append(line)
        self._render()
    def _render(self):
        with self.container:
            st.markdown("**📊 სისტემური ლოგები**")
            st.code("\n".join(self.entries[-40:]), language="text")

# ==================== აგენტები ====================

class ThemeAgent:
    def __init__(self, vault, logger):
        self.vault = vault
        self.log = logger

    def execute(self):
        self.log.add("ThemeAgent", "თემის შერჩევა (Multi-Provider)...", "start")
        
        providers = [
            ("gemini_text", "Google Gemini"),
            ("openrouter", "OpenRouter"),
            ("groq", "Groq")
        ]

        prompt = """
        შექმენი უნიკალური კინემატოგრაფიული თემა 9:16 ვიდეოსთვის.
        მიმართულება: "მელანქოლიური, რომანტიკული, ქალაქური ან ბუნებრივი სცენა".
        
        მოითხოვნები:
        1. აღწერე ვიზუალი (განათება, კომპოზიცია, ფერები).
        2. დაამატე ემოციური კონტექსტი.
        3. იყავი ლაკონიური! მაქსიმუმ 5-8 წინადადება.
        4. ენა: ქართული.
        """
        
        for service_id, name in providers:
            k = self.vault.get_key(service_id, 0)
            if not k: continue
            
            self.log.add("ThemeAgent", f"ვცდილობ {name}-ს...", indent=1)
            model, msg = self.vault.discover_and_test_model(service_id, k)
            
            if not model:
                self.log.add("ThemeAgent", f"{name} ვერ იმუშავა: {msg}", "warning")
                continue
            
            try:
                text = ""
                if service_id == "gemini_text":
                    genai.configure(api_key=k)
                    text = genai.GenerativeModel(model).generate_content(prompt).text
                elif service_id == "openrouter":
                    headers = {"Authorization": f"Bearer {k}", "HTTP-Referer": "http://localhost", "X-Title": "BeyondReality"}
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 150}, timeout=20)
                    if resp.status_code == 200: text = resp.json()["choices"][0]["message"]["content"]
                    else: raise Exception(f"API Error {resp.status_code}")
                elif service_id == "groq":
                    headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 150}, timeout=20)
                    if resp.status_code == 200: text = resp.json()["choices"][0]["message"]["content"]
                    else: raise Exception(f"API Error {resp.status_code}")
                
                self.log.add("ThemeAgent", f"✅ წარმატება ({name})", "success")
                return text.strip().replace('"', '')
            except Exception as e:
                self.log.add("ThemeAgent", f"❌ შეცდომა {name}-ზე: {str(e)[:40]}", "error")
                continue

        self.log.add("ThemeAgent", "❌ ყველა პროვაიდერი ჩავარდა", "error")
        return None

class ScriptAgent:
    def __init__(self, vault, logger): self.vault=vault; self.log=logger
    def execute(self, theme):
        self.log.add("ScriptAgent", "სცენარის წერა (Multi-Provider)...", "start")
        
        providers = [
            ("gemini_text", "Google Gemini"),
            ("openrouter", "OpenRouter"),
            ("groq", "Groq")
        ]
        
        prompt_content = f"დაწერე ემოციური მიკრო-ისტორია (2-3 წინ.) ქართულად. თემა: '{theme}'. სტილი: მელანქოლიური, კინემატოგრაფიული."

        for service_id, name in providers:
            k = self.vault.get_key(service_id, 0)
            if not k: continue
            
            self.log.add("ScriptAgent", f"ვცდილობ {name}-ს...", indent=1)
            model, msg = self.vault.discover_and_test_model(service_id, k)
            
            if not model:
                self.log.add("ScriptAgent", f"{name} ვერ იმუშავა: {msg}", "warning")
                continue

            try:
                txt = ""
                if service_id == "gemini_text":
                    genai.configure(api_key=k)
                    txt = genai.GenerativeModel(model).generate_content(prompt_content, generation_config={"temperature":0.8}).text
                elif service_id == "openrouter":
                    headers = {"Authorization": f"Bearer {k}", "HTTP-Referer": "http://localhost", "X-Title": "BeyondReality"}
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": model, "messages": [{"role": "user", "content": prompt_content}], "max_tokens": 150, "temperature": 0.8}, timeout=30)
                    if resp.status_code == 200: txt = resp.json()["choices"][0]["message"]["content"]
                    else: raise Exception(f"Error {resp.status_code}")
                elif service_id == "groq":
                    headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={"model": model, "messages": [{"role": "user", "content": prompt_content}], "max_tokens": 150, "temperature": 0.8}, timeout=30)
                    if resp.status_code == 200: txt = resp.json()["choices"][0]["message"]["content"]
                    else: raise Exception(f"Error {resp.status_code}")
                
                txt = txt.strip().replace('"','').replace('*','')
                self.log.add("ScriptAgent", f"✅ წარმატება ({name})", "success")
                return txt
            except Exception as e: 
                self.log.add("ScriptAgent", f"❌ შეცდომა {name}-ზე: {str(e)[:40]}", "error")
                continue
        
        self.log.add("ScriptAgent", "❌ ყველა პროვაიდერი ჩავარდა", "error")
        return None

class VoiceAgent:
    def __init__(self, logger): self.log=logger
    async def execute(self, text, out):
        self.log.add("VoiceAgent", "ხმის გენერაცია...", "start")
        for v in ["ka-GE-NinoNeural","ka-GE-GiorgiNeural"]:
            try:
                await edge_tts.Communicate(text,v).save(out)
                if os.path.exists(out) and os.path.getsize(out)>0:
                    dur=mp.AudioFileClip(out).duration; mp.AudioFileClip(out).close()
                    self.log.add("VoiceAgent", f"✅ ({v}, {dur:.1f}წმ)", "end"); return out
            except: continue
        self.log.add("VoiceAgent", "❌ ხმა ჩავარდა.", "error"); return None

class VisualAgent:
    def __init__(self, vault, logger): self.vault=vault; self.log=logger
    def execute(self, theme, w, h):
        self.log.add("VisualAgent", "ვიზუალის გენერაცია...", "start")
        prompt=f"Cinematic vertical shot (9:16). {theme}. Moody, emotional, high detail, 8k."
        k = self.vault.get_key("hf_image", 0)
        if k:
            try:
                img = InferenceClient(api_key=k).text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell", width=w, height=h)
                self.log.add("VisualAgent", f"✅ რეზოლუცია: {img.width}x{img.height} (HF_FLUX)", "end"); return img
            except Exception as e: 
                self.log.add("VisualAgent", f"HF ჩავარდა: {str(e)[:30]}", "warning")
        
        self.log.add("VisualAgent", "ვცდილობ Pollinations-ს...", "warning")
        try:
            img = Image.open(io.BytesIO(requests.get(f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width={w}&height={h}&nologo=true&seed={random.randint(1,99999)}&model=flux", timeout=60).content)).convert('RGB')
            self.log.add("VisualAgent", f"✅ რეზოლუცია: {img.width}x{img.height} (Pollinations)", "end"); return img
        except Exception as e: 
            self.log.add("VisualAgent", f"❌ ვიზუალი ვერ შეიქმნა: {str(e)[:30]}", "error")
            return None

class AssemblerAgent:
    def __init__(self, logger):
        self.log=logger
        self.m_path = os.path.join(CONFIG["OUTPUT_DIR"], "bg_music.mp3")
        if not os.path.exists(self.m_path):
            try:
                self.log.add("AssemblerAgent", "🎵 ჩამოვტვირთავ ფონურ მუსიკას...", indent=1)
                with open(self.m_path, "wb") as f: f.write(requests.get(CONFIG["FALLBACK_MUSIC_URL"], timeout=30).content)
                self.log.add("AssemblerAgent", "🎵 მუსიკა ჩამოტვირთულია", indent=1)
            except: 
                self.log.add("AssemblerAgent", "⚠️ მუსიკის ჩამოტვირთვა ვერ მოხერხდა", "warning")
                self.m_path=None

    def execute(self, img_p, aud_p, dur, out_p):
        self.log.add("AssemblerAgent", "🎬 ვქმნი კინემატოგრაფიულ ვიდეოს...", "start")
        img_p, aud_p, out_p = map(os.path.abspath, [img_p, aud_p, out_p])
        fin_aud = aud_p
        
        # 1. ხმის შერევა (თუ მუსიკა არსებობს)
        if self.m_path and os.path.exists(self.m_path):
            self.log.add("AssemblerAgent", "🎵 ვურევ ნარაციას მუსიკასთან...", indent=1)
            fin_aud = os.path.join(CONFIG["OUTPUT_DIR"], "mixed.mp3")
            res = subprocess.run([
                "/usr/bin/ffmpeg", "-y",
                "-i", aud_p, "-i", self.m_path,
                "-filter_complex", "[0:a]volume=1.5[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2",
                "-c:a", "libmp3lame", "-q:a", "2", fin_aud
            ], capture_output=True, text=True)
            
            if res.returncode != 0:
                self.log.add("AssemblerAgent", "⚠️ შერევა ვერ მოხერხდა, ვიყენებთ მხოლოდ ხმას", "warning")
                fin_aud = aud_p

        # 2. ვიდეოს შექმნა + CINEMATIC ZOOM (Ken Burns Effect)
        # ეს ქმნის ნამდვილ ვიდეო ფაილს, სადაც კამერა ნელა უახლოვდება (Zoom In)
        self.log.add("AssemblerAgent", "🎞️ ვადებ კინემატოგრაფიულ ზუმს (Slow Zoom)...", indent=1)
        
        cmd = [
            "/usr/bin/ffmpeg", "-y",
            "-loop", "1", "-i", img_p,
            "-i", fin_aud,
            # ვიზუალური ეფექტი: ნელი ზუმი ცენტრიდან (1.0-დან 1.5-მდე)
            "-vf", "zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_p
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            size_mb = os.path.getsize(out_p) / (1024*1024)
            try:
                video_clip = mp.VideoFileClip(out_p)
                vid_dur = video_clip.duration
                video_clip.close()
                self.log.add("AssemblerAgent", f"✅ ვიდეო მზადაა! ({size_mb:.1f}MB, {vid_dur:.1f}წმ)", "end")
            except:
                self.log.add("AssemblerAgent", f"✅ ვიდეო მზადაა! ({size_mb:.1f}MB)", "end")
            return out_p
        else:
            self.log.add("AssemblerAgent", f"❌ FFmpeg შეცდომა: {res.stderr[:60]}", "error")
            return None

class StorageAgent:
    def __init__(self, logger): self.log=logger
    def execute(self, folder):
        self.log.add("StorageAgent", "მენეჯმენტი...", "start")
        os.makedirs(folder, exist_ok=True)
        self.log.add("StorageAgent", f"✅ {len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])} ფაილი", "end")
        return folder

# ==================== UI ====================
st.set_page_config(page_title="🎬 AI Cinema Pipeline", page_icon="🎬", layout="wide")

if "vault" not in st.session_state: st.session_state.vault = VaultManager()
if "show_vault" not in st.session_state: st.session_state.show_vault = False
if "vault_inputs" not in st.session_state: 
    st.session_state.vault_inputs = {}
    for sid, sd in st.session_state.vault.config.items():
        for i in range(sd["count"]):
            st.session_state.vault_inputs[f"{sid}_{i}"] = st.session_state.vault.config[sid]["keys"][i]

vault = st.session_state.vault
logger = None

with st.sidebar:
    st.header("🎛️ სისტემის მართვა")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("🚀 პაიპლაინი", use_container_width=True, type="primary" if not st.session_state.show_vault else "secondary"):
            st.session_state.show_vault=False; st.rerun()
    with c2:
        if st.button("🔐 სეიფი", use_container_width=True, type="primary" if st.session_state.show_vault else "secondary"):
            st.session_state.show_vault=True; st.rerun()
    st.divider()
    st.caption("v6.0 | Cinematic Motion (Zoom Effect)")

col_log = st.empty()
if "logger_obj" not in st.session_state: st.session_state.logger_obj = HierarchicalLogger(col_log)
logger = st.session_state.logger_obj

if st.session_state.show_vault:
    st.title("🔐 ცენტრალური API სეიფი")
    st.markdown("აქ მართავთ ყველა პლატფორმის გასაღებსა და ლინკებს.")
    
    for sid, sd in vault.config.items():
        with st.expander(f"{sd['label']}", expanded=True):
            is_link = sd["type"]=="link"
            for i in range(sd["count"]):
                c1,c2 = st.columns([3,1])
                idx = f"{sid}_{i}"
                with c1:
                    lbl = f"#{i+1}"
                    val = st.text_input(lbl, value=st.session_state.vault_inputs.get(idx,""), key=idx, type="password" if not is_link else "default", placeholder="https://..." if is_link else "sk-... ან hf_...")
                    st.session_state.vault_inputs[idx] = val
                with c2:
                    if st.button("🔍 შემოწმება", key=f"chk_{idx}"):
                        ok, msg = vault.validate_key(sid, val)
                        if ok: st.success(msg)
                        else: st.error(msg)
    
    if st.button("💾 ყველაფრის შენახვა სეიფში", type="primary", use_container_width=True):
        for sid, sd in vault.config.items():
            for i in range(sd["count"]):
                vault.update_key(sid, i, st.session_state.vault_inputs.get(f"{sid}_{i}", ""))
        if vault.save_config():
            st.toast("✅ ყველა გასაღები და ლინკი წარმატებით შენახულია!", icon="🔒")
        else: st.error("❌ შენახვა ვერ მოხერხდა.")

else:
    st.title("🎬 AI Cinematic Pipeline")
    st.markdown("*ავტომატური კონტენტის ფაბრიკა | Cinematic Motion v6.0*")
    col_ui, col_log_area = st.columns([1, 1])
    with col_log_area: logger._render()
    
    with col_ui:
        st.subheader("⚙️ ნაბიჯების მართვა")
        if "step" not in st.session_state: st.session_state.step = 0
        if "data" not in st.session_state: st.session_state.data = {}
        P = st.session_state
        
        steps=[("1. თემის შერჩევა","theme"),("2. სცენარის წერა","script"),("3. ხმის გენერაცია","audio"),("4. ვიზუალის შექმნა","image"),("5. ვიდეოს ანიმაცია","video"),("6. შენახვა","storage")]

        for i, (label, key) in enumerate(steps):
            is_done = i < P.step
            is_active = i == P.step
            
            current_label = f"✅ {label}" if is_done else label
            btn_type = "secondary" if is_done else ("primary" if is_active else "secondary")
            disabled = not is_active 
            
            if st.button(current_label, key=f"btn_{i}", disabled=disabled, type=btn_type, use_container_width=True):
                try:
                    if i==0: result = ThemeAgent(vault, logger).execute()
                    elif i==1: result = ScriptAgent(vault, logger).execute(P.data.get("theme"))
                    elif i==2:
                        ts=datetime.now().strftime("%H%M%S")
                        result = asyncio.run(VoiceAgent(logger).execute(P.data.get("script"), os.path.join(CONFIG["OUTPUT_DIR"], f"voice_{ts}.mp3")))
                    elif i==3:
                        img = VisualAgent(vault, logger).execute(P.data.get("theme"), CONFIG["VIDEO_WIDTH"], CONFIG["VIDEO_HEIGHT"])
                        if img:
                            ts=datetime.now().strftime("%H%M%S")
                            path=os.path.join(CONFIG["OUTPUT_DIR"], f"image_{ts}.png")
                            img.save(path); result = path
                        else: result = None
                    elif i==4:
                        if not P.data.get("audio"): 
                            logger.add("SYSTEM", "❌ ხმა არ არსებობს", "error"); result = None
                        else:
                            dur=mp.AudioFileClip(P.data["audio"]).duration+2.0; mp.AudioFileClip(P.data["audio"]).close()
                            ts=datetime.now().strftime("%H%M%S")
                            result = AssemblerAgent(logger).execute(P.data["image"], P.data["audio"], dur, os.path.join(CONFIG["OUTPUT_DIR"], f"video_{ts}.mp4"))
                    elif i==5: result = StorageAgent(logger).execute(os.path.dirname(P.data.get("video") or "."))
                    
                    if result is not None:
                        P.data[key] = result
                        P.step += 1
                        st.rerun()
                    else:
                         logger.add("SYSTEM", "⚠️ ნაბიჯი ვერ დასრულდა. შეამოწმე ლოგები.", "warning")

                except Exception as e: logger.add("SYSTEM", f"❌ შეცდომა {i+1}: {str(e)}", "error")

        st.divider()
        st.subheader("📦 მიმდინარე შედეგები")
        if P.data.get("theme"): st.info(f"🎭 თემა: {P.data['theme']}")
        if P.data.get("script"): st.text_area("📜 სცენარი", P.data["script"], height=80)
        if P.data.get("audio"): st.audio(P.data["audio"])
        if P.data.get("image"): st.image(P.data["image"], use_column_width=True)
        if P.data.get("video"): 
            st.video(P.data["video"]); st.success("✅ ვიდეო მზადაა!")
            if st.button("🔄 ახალი ციკლი (Reset)"): P.step, P.data, logger.entries = 0, {}, []; st.rerun()

    st.caption("💡 მითითება: გასაღებები მართვება მარცხენა მენიუში 'სეიფი' ტაბით.")
