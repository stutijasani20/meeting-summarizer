import os
import time
import tempfile
from pathlib import Path
from moviepy import VideoFileClip
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==============================
# CONFIGURATION
# ==============================
genai.configure(api_key="your_api_key_here")  # Replace with your actual API key

WATCH_FOLDER = "/home/dev/Videos"  
SUPPORTED_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SUMMARY_PROMPT = """
You are an expert meeting summarizer.
Your task: generate a **structured meeting summary** in **pure HTML**, not Markdown.

Formatting Rules:
- Use only valid HTML tags (<h2>, <ul>, <li>, <p>, <strong>).
- Do NOT use Markdown (** or ## or * or ---).
- Do NOT include <html> or <body> tags — return only the summary content.
- Keep formatting clean and readable.

Structure the HTML output exactly as below:

<h2>Meeting Overview</h2>
<p>[Provide a concise summary of the meeting’s purpose, date, and context]</p>

<h2>Key Topics Discussed</h2>
<ul>
  <li>[Topic 1 summary]</li>
  <li>[Topic 2 summary]</li>
  <li>[Topic 3 summary]</li>
</ul>

<h2>Decisions Made</h2>
<ul>
  <li>[Decision 1]</li>
  <li>[Decision 2]</li>
</ul>

<h2>Action Items / Next Steps</h2>
<ul>
  <li>[Action item 1 with responsible person and deadline if available]</li>
  <li>[Action item 2]</li>
</ul>

<h2>Participant Contributions</h2>
<ul>
  <li><strong>[Participant Name]</strong>: [Their key input or contribution]</li>
</ul>
"""


# ==============================
# PROCESSING FUNCTIONS
# ==============================
def extract_audio(video_path: str) -> str:
    """Extract audio from video and return path to temp .wav file."""
    print(f"🎥 Extracting audio from: {os.path.basename(video_path)}")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        audio_path = tmp_audio.name
        VideoFileClip(video_path).audio.write_audiofile(
            audio_path, codec="pcm_s16le", logger=None
        )
    print(f"✅ Audio extracted")
    return audio_path


def upload_to_gemini(audio_path: str):
    """Upload audio file to Gemini."""
    print("📤 Uploading to Gemini...")
    uploaded = genai.upload_file(audio_path)
    print(f"✅ Uploaded successfully")
    return uploaded


def transcribe_audio(uploaded_audio):
    """Transcribe audio using Gemini 2.5 Flash."""
    print("🗣️ Transcribing...")
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content([
        uploaded_audio,
        "Please transcribe this meeting audio word-for-word in English."
    ])
    if not response or not response.text:
        raise ValueError("No transcription received")
    return response.text.strip()


def summarize_text(transcript: str):
    """Generate structured HTML summary using Gemini."""
    print("🧠 Generating summary...")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    # ✅ Use only 'user' and 'model' roles (no 'system')
    response = model.generate_content(
        [
            {
                "role": "user",
                "parts": [
                    SUMMARY_PROMPT,
                    f"\nMeeting Transcript:\n{transcript}"
                ],
            },
        ],
        generation_config={
            "temperature": 0.3,
            "top_p": 1,
            "top_k": 40,
        },
    )

    if not response or not hasattr(response, "text") or not response.text.strip():
        raise ValueError("No summary generated.")
    
    html_summary = response.text.strip()

    # Clean accidental markdown symbols if Gemini adds them
    html_summary = html_summary.replace("**", "").replace("##", "")
 
    return html_summary


def save_summary(summary: str, video_path: str):
    """Save summary as markdown file."""
    base_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(base_dir, f"{video_name}_summary.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Meeting Summary: {video_name}\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(summary)

    print(f"💾 Summary saved: {output_path}\n")
    return output_path


def process_video(video_path: str):
    """Complete processing pipeline for a video file."""
    print(f"\n{'='*60}")
    print(f"🎬 Processing: {os.path.basename(video_path)}")
    print(f"{'='*60}")
    
    audio_path = None
    try:
        # Check if summary already exists
        summary_path = video_path.replace(
            os.path.splitext(video_path)[1], 
            "_summary.md"
        )
        if os.path.exists(summary_path):
            print(f"⏭️  Summary already exists, skipping...")
            return

        # Processing pipeline
        audio_path = extract_audio(video_path)
        uploaded = upload_to_gemini(audio_path)
        transcript = transcribe_audio(uploaded)
        summary = summarize_text(transcript)
        save_summary(summary, video_path)
        
        print(f"✅ Successfully processed: {os.path.basename(video_path)}")

    except Exception as e:
        print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
    
    finally:
        # Cleanup temp audio
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


# ==============================
# FILE WATCHER
# ==============================
class MeetingRecordingHandler(FileSystemEventHandler):
    """Handles new video file creation events."""
    
    def __init__(self):
        self.processing = set()  # Track files being processed
    
    def on_created(self, event):
        """Called when a file is created."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a supported video format
        if file_ext not in SUPPORTED_FORMATS:
            return
        
        # Avoid duplicate processing
        if file_path in self.processing:
            return
        
        print(f"\n🔔 New recording detected: {os.path.basename(file_path)}")
        
        # Wait for file to finish writing (optional delay)
        print("⏳ Waiting for file to complete writing...")
        time.sleep(5)
        
        # Mark as processing
        self.processing.add(file_path)
        
        try:
            process_video(file_path)
        finally:
            self.processing.discard(file_path)
    
    def on_modified(self, event):
        """Handle file modifications (useful for large files being written)."""
        # You can add logic here if needed
        pass


def start_watching():
    """Start monitoring the watch folder."""
    # Create watch folder if it doesn't exist
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"👁️  MEETING RECORDING MONITOR STARTED")
    print(f"{'='*60}")
    print(f"📁 Watching folder: {os.path.abspath(WATCH_FOLDER)}")
    print(f"📹 Supported formats: {', '.join(SUPPORTED_FORMATS)}")
    print(f"⌛ Waiting for new recordings...\n")
    
    event_handler = MeetingRecordingHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        observer.stop()
    
    observer.join()
    print("✅ Monitor stopped")


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("🚀 Automatic Meeting Summarizer")
    print("\nOptions:")
    print("1. Start file watcher (automatic mode)")
    print("2. Process existing video file")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == "1":
        start_watching()
    elif choice == "2":
        video_path = input("Enter video file path: ").strip()
        if os.path.exists(video_path):
            process_video(video_path)
        else:
            print("❌ File not found")
    else:
        print("❌ Invalid option")