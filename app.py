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
    st.subheader("🔮 ტესტის გენერაცია (Director v4.0 — Unified Scene)")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა (ერთიანი ატმოსფერო)", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 დირიჟორი ქმნის ერთიან სცენას... (შეიძლება 15-20წმ დასჭირდეს)"):
            try:
                # A. ტექსტის გენერაცია
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # B. ვიზუალური გენერაცია (UNIFIED PROMPT LOGIC)
                client = InferenceClient(api_key=secrets["HF"])
                
                # დირიჟორი ქმნის ერთ მთლიან პრომპტს, რომელიც აიძულებს AI-ს შექმნას ერთიანი სივრცე
                unified_prompt = f"""
                Cinematic vertical shot 9:16. A mysterious {setting} environment. 
                Three distinct doors stand side-by-side on a unified stone path. 
                LEFT DOOR (A): Ancient heavy wooden door with iron rings. 
                CENTER DOOR (B): Futuristic sleek metallic door with glowing cyan vertical lines. 
                RIGHT DOOR (C): Magical fantasy door made of blue crystal and glowing vines. 
                Unified atmospheric fog, consistent cinematic lighting, photorealistic, 8k, highly detailed, no text.
                """
                
                img = client.text_to_image(
                    prompt=unified_prompt, 
                    model="black-forest-labs/FLUX.1-schnell",
                    width=1080, height=1920
                )
                
                # C. ლეიბლების დამატება (A, B, C) - ახლა ბევრად უფრო თვალსაჩინო
                W, H = img.size
                canvas = img.copy()
                draw = ImageDraw.Draw(canvas)
                
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                except:
                    font = ImageFont.load_default()
                    
                # ლეიბლების პოზიციები (თითოეული კარის ქვემოთ, ცენტრში)
                door_width = W // 3
                y_label = int(H * 0.62) # კარების სავარაუდო ქვედა ზღვარი
                
                for i, label in enumerate(["A", "B", "C"]):
                    x = (i * door_width) + (door_width // 2)
                    # ტექსტის ზომა
                    bbox = draw.textbbox((0, 0), label, font=font)
                    txt_w = bbox[2] - bbox[0]
                    # ხატვა თეთრი ფონით კონტრასტისთვის
                    draw.rectangle([x-40, y_label-10, x+40, y_label+90], fill=(0, 0, 0, 180))
                    draw.text((x - txt_w//2, y_label), label, fill=(255, 255, 255), font=font)
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success("✅ დირიჟორმა წარმატებით შექმნა ერთიანი სცენა!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები (Unified 9:16)")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=400)
        with col_b:
            st.image(st.session_state['gen_image'], caption="🚪 ვარიანტები: A (მარცხნივ) | B (ცენტრში) | C (მარჯვნივ)", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
