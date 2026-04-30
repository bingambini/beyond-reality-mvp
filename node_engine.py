import json
from typing import Dict, List, Any

class SimpleNodeEngine:
    """გამარტივებული ძრავა: მართავს ნაკადს და ქმნის Mermaid დიაგრამას"""
    
    def __init__(self, config_path: str, logger, vault):
        self.logger = logger
        self.vault = vault
        with open(config_path, "r", encoding="utf-8") as f:
            self.workflow = json.load(f)
        
        # მონაცემთა საცავი ნოდებს შორის გადასაცემად
        self.data_store = {}
    
    def execute(self) -> bool:
        """ასრულებს ნაკადს პირდაპირი ლოგიკით (მარტივი ვერსია)"""
        self.logger.add("NodeEngine", "🚀 ნაკადის დაწყება...", "start")
        
        try:
            # 1. თემის ნოდი
            self.logger.add("theme_node", "🔄 იწყება...", "info")
            from agents.theme_agent import ThemeAgent  # პირდაპირი იმპორტი
            theme_result = ThemeAgent(self.vault, self.logger).execute()
            if not theme_result: return False
            self.data_store["theme"] = theme_result
            self.logger.add("theme_node", "✅ დასრულდა", "success")
            
            # 2. სცენარის ნოდი (იღებს თემას)
            self.logger.add("script_node", "🔄 იწყება...", "info")
            from agents.script_agent import ScriptAgent
            script_result = ScriptAgent(self.vault, self.logger).execute(self.data_store["theme"])
            if not script_result: return False
            self.data_store["script"] = script_result
            self.logger.add("script_node", "✅ დასრულდა", "success")
            
            # 3. ხმის და ვიზუალის ნოდები (პარალელურად)
            self.logger.add("voice_node", "🔄 იწყება...", "info")
            from agents.voice_agent import VoiceAgent
            import asyncio, os, datetime
            ts = datetime.datetime.now().strftime("%H%M%S")
            audio_path = os.path.join("./output", f"voice_{ts}.mp3")
            audio_result = asyncio.run(VoiceAgent(self.logger).execute(self.data_store["script"], audio_path))
            if not audio_result: return False
            self.data_store["audio"] = audio_result
            self.logger.add("voice_node", "✅ დასრულდა", "success")
            
            self.logger.add("visual_node", "🔄 იწყება...", "info")
            from agents.visual_agent import VisualAgent
            visual_result = VisualAgent(self.vault, self.logger).execute(self.data_store["theme"], 1080, 1920)
            if not visual_result: return False
            img_path = os.path.join("./output", f"image_{ts}.png")
            visual_result.save(img_path)
            self.data_store["image"] = img_path
            self.logger.add("visual_node", "✅ დასრულდა", "success")
            
            # 4. ვიდეოს აწყობა
            self.logger.add("assembler_node", "🔄 იწყება...", "info")
            from agents.assembler_agent import AssemblerAgent
            dur = 12 # ან აუდიოს ხანგრძლივობა
            video_path = os.path.join("./output", f"video_{ts}.mp4")
            video_result = AssemblerAgent(self.logger).execute(self.data_store["image"], self.data_store["audio"], dur, video_path)
            if not video_result: return False
            self.data_store["video"] = video_path
            self.logger.add("assembler_node", "✅ დასრულდა", "success")
            
            # 5. შენახვა
            self.logger.add("storage_node", "🔄 იწყება...", "info")
            from agents.storage_agent import StorageAgent
            StorageAgent(self.logger).execute(os.path.dirname(video_path))
            self.logger.add("storage_node", "✅ დასრულდა", "success")
            
            self.logger.add("NodeEngine", "✅ მთლიანი ნაკადი წარმატებით დასრულდა!", "success")
            return True
            
        except Exception as e:
            self.logger.add("NodeEngine", f"❌ კრიტიკული შეცდომა: {str(e)}", "error")
            return False
    
    def get_mermaid_diagram(self) -> str:
        """ქმნის Mermaid.js დიაგრამას"""
        lines = ["graph LR"]
        for node in self.workflow["nodes"]:
            # Mermaid-ისთვის უნიკალური ID
            safe_id = node["id"].replace("_", "")
            lines.append(f'    {safe_id}["{node["label"]}"]')
        
        for edge in self.workflow["edges"]:
            from_id = edge["from"].replace("_", "")
            to_id = edge["to"].replace("_", "")
            label = edge.get("label", "")
            lines.append(f'    {from_id} -- "{label}" --> {to_id}')
        
        return "\n".join(lines)
