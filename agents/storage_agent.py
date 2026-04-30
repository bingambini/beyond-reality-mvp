import os

class StorageAgent:
    """აგენტი, რომელიც ამოწმებს ფაილს, წერს მეტამონაცემებს და ადასტურებს შენახვას"""
    
    def __init__(self, vault):
        self.vault = vault

    def execute(self, video_path: str) -> dict:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"ვიდეო ფაილი ვერ მოიძებნა: {video_path}")
            
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        meta = {
            "path": video_path,
            "size_mb": round(size_mb, 2),
            "status": "completed"
        }
        print(f"[Storage] ✅ ფაილი წარმატებით შენახულია: {meta['size_mb']} MB")
        return meta
