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
def get_available_models(api_key):
    """იღებს ყველა ხელმისაწვდომ მოდელს"""
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace("models/", "")
                if 'flash' in model_name:
                    available.insert(0, model_name)
                elif 'pro' in model_name:
                    available.append(model_name)
                else:
                    available.append(model_name)
        return available if available else ["gemini-pro"]
    except Exception as e:
        return ["gemini-pro", "gemini-1.0-pro"]

def generate_with_smart_fallback(api_key, prompt, max_retries_per_model=2):
    """ჭკვიანი გენერაცია: თუ ერთ მოდელს ლიმიტი ამოეწურა, გადადის მეორეზე"""
    available_models = get_available_models(api_key)
    st.info(f"🔍 ხელმისაწვდომი მოდელები: {', '.join(available_models[:3])}")
    
    for model_name in available_models:
        try:
            st.info(f"🔄 ვცდილობ მოდელს: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            for attempt in range(max_retries_per_model):
                try:
                    response = model.generate_content(prompt)
                    st.success(f"✅ წარმატება! გამოყენებულია: {model_name}")
                    return response
                except Exception as e:
                    error_msg = str(e)
                    if '429' in error_msg or 'quota' in error_msg.lower():
                        if attempt < max_retries_per_model - 1:
                            wait_time = 10 * (attempt + 1)
                            st.warning(f"⏳ {model_name}-ს ლიმიტი ამოიწურა. ველოდები {wait_time}წმ... (ცდა {attempt + 1}/{max_retries_per_model})")
                            time.sleep(wait_time)
                        else:
                            st.warning(f"⚠️ {model_name}-ზე ლიმიტი ამოიწურა. გადავდივარ შემდეგ მოდელზე...")
                            break
                    elif 'not found' in error_msg.lower() or 'not supported' in error_msg.lower():
                        st.warning(f"⚠️ {model_name} არ არის ხელმისაწვდომი. გადავდივარ შემდეგზე...")
                        break
                    else:
                        raise e
        except Exception as e:
            st.warning(f"⚠️ {model_name} ვერ ჩაიტვირთა: {str(e)}")
            continue
    
    raise Exception(f"❌ ყველა ხელმისაწვდომი მოდელის ლიმიტი ამოიწურა. გთხოვთ: 1) დაელოდოთ 2-3 წუთი, ან 2) დაამატოთ ახალი API გასაღები Secrets-ში")

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
    st.subheader("🔮 ტესტის გენერაცია (Dynamic Format Test)")
    
    # --- პარამეტრების არჩევა ---
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    with col_b:
        setting = st.selectbox("🖼️ სცენა (ფონი)", template["generation"]["image_settings"])
    with col_c:
        # ახალი პარამეტრი: ფორმატი
        format_choice = st.selectbox("📐 ფორმატი", [
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
                
                # --- B. დირიჟორის ლოგიკა (ფორმატის არჩევანი) ---
                # დირიჟორი განსაზღვრავს ზომებს არჩეული ფორმატის მიხედვით
                format_config = {
                    "9:16 (Vertical / TikTok)": {"w": 1080, "h": 1920, "ratio_desc": "vertical 9:16", "img_ratio": 0.75},
                    "16:9 (Horizontal / YouTube)": {"w": 1920, "h": 1080, "ratio_desc": "horizontal 16:9", "img_ratio": 0.80},
                    "1:1 (Square / Instagram)": {"w": 1080, "h": 1080, "ratio_desc": "square 1:1", "img_ratio": 0.75}
                }
                
                config = format_config[format_choice]
                FINAL_W, FINAL_H = config["w"], config["h"]
                IMAGE_H = int(FINAL_H * config["img_ratio"])
                
                # დირიჟორი ადგენს პრომპტს ფორმატის შესაბამისად
                ai_prompt = f"""
                Cinematic {config['ratio_desc']} shot. 
                Three distinct doors standing side-by-side in a {setting}. 
                LEFT: Ancient wooden door. CENTER: Futuristic metal door with blue neon. RIGHT: Magical crystal door.
                Composition: Doors should be centered. High detail, 8k.
                """
                
                client = InferenceClient(api_key=secrets["HF"])
                st.info(f"🎨 სურათის გენერაცია ({FINAL_W}x{FINAL_H})...")
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
                # შრიფტის ზომის ადაპტაცია ფორმატზე
                FONT_SIZE = 180 if FINAL_H > 1500 else 120 
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
                except:
                    font = ImageFont.load_default()
                
                door_width = FINAL_W // 3
                y_start = IMAGE_H + 40
                box_h = 180 if FINAL_H > 1500 else 120
                box_w = 150 if FINAL_H > 1500 else 100
                
                for i, label in enumerate(["A", "B", "C"]):
                    x_center = (i * door_width) + (door_width // 2)
                    x_left = x_center - box_w // 2
                    y_top = y_start
                    
                    # ფონი + ჩარჩო
                    draw.rectangle([x_left, y_top, x_left + box_w, y_top + box_h], fill=(25, 25, 25), outline=(255, 255, 255), width=4)
                    
                    # ტექსტი
                    bbox = draw.textbbox((0, 0), label, font=font)
                    txt_w = bbox[2] - bbox[0]
                    txt_h = bbox[3] - bbox[1]
                    draw.text((x_center - txt_w//2, y_top + (box_h - txt_h)//2 - 10), label, fill=(255, 255, 255), font=font)
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success(f"✅ წარმატებით დაგენერირდა {config['ratio_desc']} ფორმატში!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # --- შედეგების ჩვენება ---
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader(f"📝 შედეგები ({format_choice})")
        
        st.text_area("📜 გენერირებული ტექსტი", st.session_state['gen_text'], height=150)
        
        col_margin, col_main, col_margin = st.columns([0.1, 1, 0.1])
        with col_main:
            st.image(st.session_state['gen_image'], caption="🚪 A | B | C", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
