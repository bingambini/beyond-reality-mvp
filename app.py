import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import io
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
def get_best_gemini_model(api_key):
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        preferred = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
        available = [m.name.replace("models/", "") for m in models if 'generateContent' in m.supported_generation_methods]
        for p in preferred:
            if p in available: return genai.GenerativeModel(p)
        return genai.GenerativeModel(available[0]) if available else genai.GenerativeModel("gemini-pro")
    except: return genai.GenerativeModel("gemini-pro")

def generate_with_retry(model, prompt, max_retries=3):
    """ავტომატური Retry ლოგიკა 429 შეცდომისთვის"""
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'quota' in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = 12 * (attempt + 1)  # ექსპონენციალური backoff
                    st.warning(f" ლიმიტი ამოიწურა. ველოდები {wait_time}წმ... (ცდა {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise Exception("ლიმიტი ამოიწურა 3 ცდის შემდეგ. გთხოვთ სცადოთ 1 წუთში.")
            else:
                raise e
    return None

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Gemini API", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("Template", "📄 Loaded")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია (Auto-Retry Enabled)")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 დირიჟორი მუშაობს (ავტო-Retry ჩართულია)..."):
            try:
                # --- A. ტექსტის გენერაცია (Auto-Retry-თ) ---
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                
                st.info("📝 ტექსტის გენერაცია...")
                text_response = generate_with_retry(model, prompt_text)
                
                # --- B. ვიზუალური გენერაცია (Safe Zone Logic) ---
                client = InferenceClient(api_key=secrets["HF"])
                
                FINAL_W, FINAL_H = 1080, 1920
                IMAGE_RATIO = 0.75 
                IMAGE_H = int(FINAL_H * IMAGE_RATIO) 
                
                ai_prompt = f"""
                Cinematic vertical shot, 3:4 aspect ratio. 
                Three distinct doors standing side-by-side in a {setting}. 
                LEFT: Ancient wooden door. CENTER: Futuristic metal door with blue neon. RIGHT: Magical crystal door.
                Composition: Doors should be centered. High detail, 8k.
                """
                
                st.info("🎨 სურათის გენერაცია...")
                img = client.text_to_image(
                    prompt=ai_prompt, 
                    model="black-forest-labs/FLUX.1-schnell",
                    width=FINAL_W, 
                    height=IMAGE_H 
                )
                
                # --- C. კომპოზიცია + დიდი ლეიბლები ---
                canvas = Image.new('RGB', (FINAL_W, FINAL_H), color=(10, 10, 12))
                canvas.paste(img, (0, 0))
                
                draw = ImageDraw.Draw(canvas)
                
                # შრიფტის პარამეტრები
                FONT_SIZE = 180
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
                except:
                    font = ImageFont.load_default()
                
                door_width = FINAL_W // 3
                y_start = IMAGE_H + 60
                box_h = 220
                box_w = 200
                
                for i, label in enumerate(["A", "B", "C"]):
                    x_center = (i * door_width) + (door_width // 2)
                    x_left = x_center - box_w // 2
                    y_top = y_start
                    
                    # 1. ვხატავთ ფონს + ჩარჩოს
                    draw.rectangle([x_left, y_top, x_left + box_w, y_top + box_h], fill=(25, 25, 25), outline=(255, 255, 255), width=5)
                    
                    # 2. ვხატავთ ტექსტს ცენტრში
                    bbox = draw.textbbox((0, 0), label, font=font)
                    txt_w = bbox[2] - bbox[0]
                    txt_h = bbox[3] - bbox[1]
                    draw.text((x_center - txt_w//2, y_top + (box_h - txt_h)//2 - 15), label, fill=(255, 255, 255), font=font)
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success("✅ წარმატებით დაგენერირდა! (ლიმიტები ავტომატურად დარეგულირდა)")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები (Auto-Retry Enabled)")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=400)
        with col_b:
            st.image(st.session_state['gen_image'], caption="🚪 A | B | C (მკაფიო და დიდი)", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
