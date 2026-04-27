import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import io

# გვერდის კონფიგურაცია
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
    st.subheader("🔮 ტესტის გენერაცია (Director v3.0 — ჰორიზონტალური კოლაჟი)")
    
    # პარამეტრების არჩევა ღილაკამდე
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა (ერთიანი ბექგრაუნდი)", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 დირიჟორი მუშაობს: ბექგრაუნდი → 3 კარი → ჰორიზონტალური შეკერვა..."):
            try:
                # A. ტექსტის გენერაცია
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # B. ვიზუალური გენერაცია (დირიჟორის ლოგიკა)
                client = InferenceClient(api_key=secrets["HF"])
                
                # 1. ერთიანი ბექგრაუნდი
                bg_prompt = f"cinematic {setting} environment, foggy, mysterious atmosphere, empty ground space, cinematic lighting, 9:16"
                bg_img = client.text_to_image(bg_prompt, model="black-forest-labs/FLUX.1-schnell")
                
                # 2. სამი განსხვავებული კარი
                door_prompts = [
                    "ancient heavy wooden door with iron rings, front view, isolated",
                    "futuristic sleek metal door with glowing blue accents, front view, isolated",
                    "magical crystalline door with glowing vines, front view, isolated"
                ]
                doors = [client.text_to_image(p, model="black-forest-labs/FLUX.1-schnell") for p in door_prompts]
                
                # 3. ჰორიზონტალური კომპოზიცია 9:16 კანვასზე
                W, H = 1080, 1920  # 9:16 ფორმატი
                canvas = Image.new('RGB', (W, H), (12, 12, 18)) # მუქი საბაზისო ფერი
                canvas.paste(bg_img.resize((W, H)), (0, 0))
                
                # ზომების გათვლა
                door_w = W // 3
                door_h = int(H * 0.55)
                y_pos = int(H * 0.22) # კარები მოთავსდება შუაში
                
                for i, door in enumerate(doors):
                    door_resized = door.resize((door_w, door_h))
                    x_pos = i * door_w
                    canvas.paste(door_resized, (x_pos, y_pos))
                
                # 4. ლეიბლების დამატება (A, B, C)
                draw = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
                except:
                    font = ImageFont.load_default()
                    
                for i, label in enumerate(["A", "B", "C"]):
                    txt_w, txt_h = draw.textlength(label, font=font), 70
                    x = (i * door_w) + (door_w // 2) - (txt_w // 2)
                    y = y_pos + door_h + 30
                    draw.text((x, y), label, fill=(255, 255, 255), font=font)
                
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas
                st.success("✅ დირიჟორმა წარმატებით ააწყო ჰორიზონტალური კომპოზიცია!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები (ჰორიზონტალური ტრიპტიქი)")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=400)
        with col_b:
            st.image(st.session_state['gen_image'], caption="🚪 ვარიანტები: A | B | C", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
