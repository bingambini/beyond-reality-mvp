import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import io

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
    st.subheader("🔮 ტესტის გენერაცია (Director v5.0 — Safe Zone Logic)")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია (Safe Zone)", type="primary"):
        with st.spinner("🤖 დირიჟორი ზომავს სივრცეს და ქმნის კომპოზიციას..."):
            try:
                # --- A. ტექსტის გენერაცია ---
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # --- B. ვიზუალური გენერაცია (Safe Zone Logic) ---
                client = InferenceClient(api_key=secrets["HF"])
                
                # 1. განვსაზღვროთ ზომები (9:16 ფორმატი)
                FINAL_W, FINAL_H = 1080, 1920
                IMAGE_RATIO = 0.75 # სურათი დაიკავებს ზედა 75%-ს
                IMAGE_H = int(FINAL_H * IMAGE_RATIO) # 1440px
                
                # 2. "ჭკვიანი პრომპტი" - ვთხოვთ AI-ს ფოკუსირდეს ზედა ნაწილზე
                # ჩვენ ვიცით, რომ ქვედა ნაწილი ჩვენს კოდში იქნება შავი.
                ai_prompt = f"""
                Cinematic vertical shot, 3:4 aspect ratio. 
                Three distinct doors standing side-by-side in a {setting}. 
                LEFT: Ancient wooden door. CENTER: Futuristic metal door with blue neon. RIGHT: Magical crystal door.
                Composition: Doors should be centered. High detail, 8k.
                """
                
                # ვითხოვთ სურათს ზუსტად იმ ზომით, რაც ზედა ნაწილისთვის გვჭირდება
                img = client.text_to_image(
                    prompt=ai_prompt, 
                    model="black-forest-labs/FLUX.1-schnell",
                    width=FINAL_W, 
                    height=IMAGE_H 
                )
                
                # --- C. კომპოზიცია (კოდით) ---
                # 1. ვქმნით სუფთა შავ კანვასს (სრული 9:16)
                canvas = Image.new('RGB', (FINAL_W, FINAL_H), color=(10, 10, 12))
                
                # 2. ვაკრავთ AI-ის სურათს ზედა ნაწილში (0, 0)
                # ეს გარანტიას გვაძლევს, რომ ქვედა 25% დარჩება სუფთა შავი
                canvas.paste(img, (0, 0))
                
                # 3. ვხატავთ ლეიბლებს (A, B, C) ქვედა ნაწილში (უსაფრთხო ზონაში)
                draw = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
                except:
                    font = ImageFont.load_default()
                
                door_width = FINAL_W // 3
                # ლეიბლების Y პოზიცია: სურათის ბოლოდან ცოტა ქვემოთ
                y_label = IMAGE_H + 50 
                
                for i, label in enumerate(["A", "B", "C"]):
                    x = (i * door_width) + (door_width // 2)
                    # ტექსტის ზომის გაზომვა ცენტრირებისთვის
                    bbox = draw.textbbox((0, 0), label, font=font)
                    txt_w = bbox[2] - bbox[0]
                    
                    # ვხატავთ თეთრ ასოს
                    draw.text((x - txt_w//2, y_label), label, fill=(255, 255, 255), font=font)
                    # ვამატებთ პატარა ხაზს ან წერტილს ვიზუალური გამყოფისთვის
                    draw.ellipse([x-5, y_label+100, x+5, y_label+110], fill=(50, 50, 50))
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success("✅ დირიჟორმა ზუსტად დაყო სივრცე!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები (Safe Zone Composition)")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=400)
        with col_b:
            st.image(st.session_state['gen_image'], caption="🚪 ზედა ნაწილი: სურათი | ქვედა ნაწილი: ლეიბლები", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
