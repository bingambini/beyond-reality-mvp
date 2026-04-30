import streamlit as st
import os
from pathlib import Path

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

# ==================== ფაილების სტრუქტურის ჩვენება ====================
def show_file_structure():
    """აჩვენებს მთელ პროექტის ფაილების სტრუქტურას"""
    st.title("📁 პროექტის ფაილების სტრუქტურა")
    
    # მიმდინარე დირექტორია
    root_dir = Path(".")
    
    # ხის სტრუქტურის აგება
    tree_lines = []
    
    def build_tree(directory, prefix="", is_last=True):
        # დირექტორიის სახელი
        dir_name = directory.name if directory != root_dir else "beyond-reality-mvp"
        connector = "└── " if is_last else "├── "
        tree_lines.append(f"{prefix}{connector}📁 {dir_name}/")
        
        # შიგთავსის მიღება
        try:
            contents = sorted(directory.iterdir(), key=lambda x: (not x.is_file(), x.name.lower()))
            # გავფილტროთ ზოგიერთი ფაილი
            contents = [c for c in contents if not c.name.startswith('.') and c.name not in ['__pycache__', 'venv', 'env', '.git']]
        except PermissionError:
            return
        
        # ახალი პრეფიქსი
        extension = "    " if is_last else "│   "
        
        for i, item in enumerate(contents):
            is_last_item = (i == len(contents) - 1)
            
            if item.is_file():
                # ფაილის ხატი და ფერი
                icon = "📄"
                ext = item.suffix.lower()
                if ext == '.py':
                    icon = "🐍"
                elif ext == '.json':
                    icon = "📋"
                elif ext == '.md':
                    icon = "📝"
                elif ext in ['.png', '.jpg', '.gif']:
                    icon = "🖼️"
                elif ext in ['.mp4', '.avi', '.mov']:
                    icon = "🎬"
                elif ext in ['.mp3', '.wav']:
                    icon = "🎵"
                
                tree_lines.append(f"{prefix}{extension}{icon} {item.name}")
            else:
                build_tree(item, prefix + extension, is_last_item)
    
    # ხის აგება
    tree_lines.append("📁 beyond-reality-mvp/")
    try:
        contents = sorted(root_dir.iterdir(), key=lambda x: (not x.is_file(), x.name.lower()))
        contents = [c for c in contents if not c.name.startswith('.') and c.name not in ['__pycache__', 'venv', 'env', '.git']]
        
        for i, item in enumerate(contents):
            is_last = (i == len(contents) - 1)
            
            if item.is_file():
                icon = "📄"
                ext = item.suffix.lower()
                if ext == '.py': icon = "🐍"
                elif ext == '.json': icon = "📋"
                elif ext == '.md': icon = "📝"
                
                tree_lines.append(f"├── {icon} {item.name}" if not is_last else f"└── {icon} {item.name}")
            else:
                build_tree(item, "", is_last)
    except Exception as e:
        tree_lines.append(f"❌ შეცდომა: {e}")
    
    # ჩვენება
    st.markdown("### 🌳 ფაილების ხე")
    st.code("\n".join(tree_lines), language="text")
    
    # დამატებითი ინფორმაცია
    st.divider()
    st.subheader("📊 სტატისტიკა")
    
    py_files = list(root_dir.rglob("*.py"))
    json_files = list(root_dir.rglob("*.json"))
    total_files = sum(1 for _ in root_dir.rglob("*") if _.is_file() and not _.name.startswith('.') and 'cache' not in str(_))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Python ფაილები", len(py_files))
    col2.metric("JSON ფაილები", len(json_files))
    col3.metric("სულ ფაილები", total_files)
    
    # საჭირო ფაილების ჩეკლისტი
    st.divider()
    st.subheader("✅ საჭირო ფაილების სტატუსი")
    
    required_files = {
        "app.py": " მთავარი აპლიკაცია",
        "workflow_config.json": "📋 ნაკადის კონფიგურაცია",
        "node_engine.py": "⚙️ ნოდების ძრავა",
        "vault_system.py": "🔐 API გასაღებების მენეჯერი",
        "requirements.txt": "📦 ბიბლიოთეკები",
        "agents/__init__.py": "📦 აგენტების პაკეტი",
        "agents/theme_agent.py": "🎭 თემის აგენტი",
        "agents/script_agent.py": "📝 სცენარის აგენტი",
        "agents/voice_agent.py": "🎙️ ხმის აგენტი",
        "agents/visual_agent.py": "🎨 ვიზუალის აგენტი",
        "agents/assembler_agent.py": "🎬 ვიდეოს აგენტი",
        "agents/storage_agent.py": "💾 შენახვის აგენტი"
    }
    
    checklist_data = []
    for file_path, description in required_files.items():
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        size = os.path.getsize(file_path) if exists else 0
        checklist_data.append({
            "ფაილი": file_path,
            "სტატუსი": status,
            "აღწერა": description,
            "ზომა": f"{size/1024:.1f} KB" if exists else "-"
        })
    
    st.table(checklist_data)
    
    # რჩევები
    st.divider()
    st.info("""
    💡 **როგორ გამოვიყენოთ:**
    1. გადახედე ზემოთ სტრუქტურას
    2. შეამოწმე ჩეკლისტი - რომელი ფაილები აკლია (❌)
    3. შექმენი აკლული ფაილები
    4. ჩაწერე კოდი თითოეულ ფაილში
    5. დააჭირე "↩️ უკან დაბრუნება" ღილაკს მთავარ ეკრანზე დასაბრუნებლად
    """)

# ==================== მთავარი აპლიკაცია ====================
if "show_structure" not in st.session_state:
    st.session_state.show_structure = False

# Sidebar
with st.sidebar:
    st.header("🎛️ მართვა")
    
    if st.button("📁 ფაილების სტრუქტურა", use_container_width=True):
        st.session_state.show_structure = True
        st.rerun()
    
    if st.button("🎬 მთავარი ეკრანი", use_container_width=True, type="primary"):
        st.session_state.show_structure = False
        st.rerun()
    
    st.divider()
    
    if st.session_state.show_structure:
        st.info("👈 დააჭირე 'მთავარი ეკრანი' დასაბრუნებლად")

# მთავარი ხედი
if st.session_state.show_structure:
    show_file_structure()
else:
    # აქ იქნება შენი ნორმალური აპლიკაციის კოდი
    st.title("🎬 AI Cinematic Pipeline")
    st.markdown("*ნოდური სისტემა ვიზუალური ნაკადით*")
    
    st.info("👉 დააჭირე გვერდითა პანელში **'📁 ფაილების სტრუქტურა'** ღილაკს, რომ ნახო ყველა ფაილი")
    
    # აქ შეგიძლია ჩასვა დანარჩენი აპლიკაციის კოდი
    # (Mermaid დიაგრამა, ლოგები, გაშვების ღილაკი და ა.შ.)

# ფეისერი
st.caption("""
💡 **მითითება:** 
- ფაილების სტრუქტურაში ნახავ რომელი ფაილები გაქვს და რომელი აკლია
- მწვანე ✅ ნიშნავს რომ ფაილი არსებობს
- წითელი ❌ ნიშნავს რომ ფაილი უნდა შექმნა
""")
