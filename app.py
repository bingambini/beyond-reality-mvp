import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import time

st.set_page_config(page_title="Beyond Reality — MVP", page_icon="🏛️", layout="wide")

# --- 1. მონაცემების ჩატვირთვა ---
@st.cache_resource
def load_secrets():
    return {
        "GEMINI": st.secrets.get("GEMINI_API_KEY"),
        "HF": st.secrets.get("HF_API_KEY")
    }

@st.cache_data
def load_template():
    with open("config/templates/psych_test_door_choice_v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource
def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace("models/", "")
                if 'flash' in model_name: available.insert(0, model_name)
                elif 'pro' in model_name: available.append(model_name)
                else: available.append(model_name)
        return available if available else ["gemini-pro"]
    except Exception:
        return ["gemini-pro", "gemini-1.0-pro"]

def generate_with_smart_fallback(api_key, prompt, max_retries=2):
    available_models = get_available_models(api_key)
    st.info(f" ხელმისაწვდომი მოდელები: {', '.join(available_models[:3])}")
    
    for model_name in available_models:
        try:
            st.info(f"🔄 ვცდილობ მოდელს: {model_name}")
            model = genai.GenerativeModel(model_name)
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    st.success(f"✅ წარმატება! გამოყენებულია: {model_name}")
                    return response
                except Exception as e:
                    error_msg = str(e)
                    if '429' in error_msg or 'quota' in error_msg.lower():
                        if attempt < max_retries - 1:
                            wait = 10 * (attempt + 1)
                            st.warning(f"⏳ {model_name}-ს ლიმიტი. ველოდები {wait}წმ...")
                            time.sleep(wait)
                        else:
                            st.warning(f"⚠️ {model_name} ამოიწურა. გადავდივარ შემდეგზე...")
                            break
                    elif 'not found' in error_msg.lower() or 'not supported' in error_msg.lower():
                        st.warning(f"⚠️ {model_name} არ არის ხელმისაწვდომი.")
                        break
                    else: raise e
        except Exception: continue
    raise Exception(" ყველა მოდელის ლიმიტი ამოიწურა. გთხოვთ დაელოდოთ ან დაამატოთ ახალი გასაღები.")

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Gemini API", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("Template", "📄 Loaded")

tab1, tab2, tab3 = st.tabs(["️ გენერაცია", " დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader(" ტესტის გენერაცია (Director v8.0 — Pure Text Overlay)")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    with col_b: setting = st.selectbox("️ სცენა", template["generation"]["image_settings"])
    with col_c:
        format_choice = st.selectbox(" ფორმატი", [
            "9:16 (Vertical / TikTok)", 
            "16:9 (Horizontal / YouTube)", 
            "1:1 (Square / Instagram)"
        ], index=0)
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 დირიჟორი ამუშავებს ლოგიკას..."):
            try:
                if not secrets["GEMINI"]:
                    st.error("❌ GEMINI_API_KEY არ არის დაყენებული!")
                    st.stop()
                
                genai.configure(api_key=secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                
                st.info("📝 ტექსტის გენერაცია...")
                text_response = generate_with_smart_fallback(secrets["GEMINI"], prompt_text)
                
                # --- ფორმატის კონფიგურაცია ---
                fmt = {
                    "9:16 (Vertical / TikTok)": {"w": 1080, "h": 1920, "desc": "vertical 9:16"},
                    "16:9 (Horizontal / YouTube)": {"w": 1920, "h": 1080, "desc": "horizontal 16:9"},
                    "1:1 (Square / Instagram)": {"w": 1080, "h": 1080, "desc": "square 1:1"}
                }
                cfg = fmt[format_choice]
                W, H = cfg["w"], cfg["h"]
                
                # პრომპტი: ვთხოვთ AI-ს შეავსოს მთელი კადრი
                ai_prompt = f"""
                Cinematic {cfg['desc']} shot. 
                Three distinct doors standing side-by-side in a {setting}. 
                LEFT: Ancient wooden door. CENTER: Futuristic metal door with blue neon. RIGHT: Magical crystal door.
                Composition: Doors centered, high detail, 8k, photorealistic. 
                IMPORTANT: Fill the entire frame, detailed ground/floor, no empty space.
                """
                
                client = InferenceClient(api_key=secrets["HF"])
                st.info(f"🎨 სურათის გენერაცია ({W}x{H})...")
                img = client.text_to_image(prompt=ai_prompt, model="black-forest-labs/FLUX.1-schnell", width=W, height=H)
                
                # --- ლეიბლების დადება (Pure Text Overlay) ---
                canvas = img.copy()
                draw = ImageDraw.Draw(canvas)
                
                # დინამიური ომები
                font_size = int(W * 0.07) # შრიფტის ზომა
                y_pos = int(H * 0.82)     # პოზიცია (კარების ძირთან)
                
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                door_w = W // 3
                for i, label in enumerate(["A", "B", "C"]):
                    cx = (i * door_w) + (door_w // 2)
                    
                    # ტექსტის ზომის გაზომვა ცენტრირებისთვის
                    bbox = draw.textbbox((0, 0), label, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    
                    # 1. ჩრდილი (Shadow) - რომ გამოირჩეოდეს ნებისმიერ ფონზე
                    draw.text((cx - tw//2 + 3, y_pos - th//2 + 3), label, fill=(0, 0, 0), font=font)
                    
                    # 2. ძირითადი თეთრი ტექსტი
                    draw.text((cx - tw//2, y_pos - th//2), label, fill=(255, 255, 255), font=font)
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success(f"✅ წარმატებით! ({cfg['desc']} + Pure Overlay)")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # --- შედეგების ჩვენება ---
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader(f"📝 შედეგები ({format_choice})")
        st.text_area("📜 ტექსტი", st.session_state['gen_text'], height=120)
        
        col_m, col_c, col_m = st.columns([0.1, 1, 0.1])
        with col_c:
            st.image(st.session_state['gen_image'], caption=" A | B | C (Pure Overlay)", use_column_width=True)

with tab2: st.info(" დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
