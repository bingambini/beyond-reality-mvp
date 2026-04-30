import subprocess
import os

class AssemblerAgent:
    """აგენტი, რომელიც აწყობს სურათსა და ხმას ვიდეოდ + ადებს ნელ ზუმს"""
    
    def __init__(self, vault):
        self.vault = vault
        self.ffmpeg_path = "/usr/bin/ffmpeg" # Streamlit Cloud სტანდარტი

    def execute(self, image_path: str, audio_path: str, output_path: str) -> str:
        # აბსოლუტური გზები
        image_path = os.path.abspath(image_path)
        audio_path = os.path.abspath(audio_path)
        output_path = os.path.abspath(output_path)

        # Ken Burns ეფექტი: ნელი ზუმი ცენტრიდან (1.0 -> 1.5x)
        # d=1 ნიშნავს 1 ფრეიმს ზუმის ნაბიჯზე. ~24fps-ზე ეს იძლევა პლავურ ანიმაციას
        zoom_filter = "zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"

        cmd = [
            self.ffmpeg_path, "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", zoom_filter,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", # ვიდეოს სიგრძე = აუდიოს სიგრძე
            output_path
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print(f"[Assembler] ვიდეო მზადაა: {output_path} ({size_mb:.2f} MB)")
            return output_path
        else:
            raise Exception(f"FFmpeg შეცდომა: {res.stderr[:150]}")
