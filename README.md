# Meeting Summarizer

An automated tool that monitors a folder for new meeting recordings, transcribes them using Google's Gemini AI, and generates structured HTML summaries with key topics, decisions, and action items.

## Features

- 🎥 **Automatic Video Monitoring**: Watches a designated folder for new meeting recordings
- 🗣️ **Audio Transcription**: Extracts and transcribes audio using Google Gemini 2.5 Flash
- 🧠 **AI-Powered Summarization**: Generates structured meeting summaries with:
  - Meeting overview
  - Key topics discussed
  - Decisions made
  - Action items and next steps
  - Participant contributions
- 📁 **Multiple Format Support**: Works with MP4, MKV, AVI, MOV, and WEBM files
- ⚡ **Two Operating Modes**: 
  - Automatic file watcher mode
  - Manual single-file processing mode

## Prerequisites

- Python 3.10+
- Google Gemini API key
- FFmpeg (for video/audio processing)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already installed):
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Configuration

1. **Set up your Google Gemini API key**:
   
   Open `meeting_summary.py` and replace the API key on line 13:
   ```python
   genai.configure(api_key="YOUR_API_KEY_HERE")
   ```
   
   > ⚠️ **Security Note**: For production use, store your API key in environment variables instead of hardcoding it.

2. **Configure the watch folder** (optional):
   
   By default, the script monitors `/home/dev/Videos`. To change this, edit line 15:
   ```python
   WATCH_FOLDER = "/path/to/your/videos"
   ```

## Usage

### Option 1: Automatic File Watcher Mode

This mode continuously monitors a folder for new video files and processes them automatically.

```bash
python meeting_summary.py
```

When prompted, select option `1`:
```
Select option (1 or 2): 1
```

The script will:
- Monitor the configured folder
- Automatically detect new video files
- Process them and generate summaries
- Save summaries as HTML files in the same directory

Press `Ctrl+C` to stop monitoring.

### Option 2: Process Single File

To process a specific video file:

```bash
python meeting_summary.py
```

When prompted, select option `2` and provide the file path:
```
Select option (1 or 2): 2
Enter video file path: /path/to/your/meeting.mp4
```

## Output

For each processed video, the script generates an HTML summary file with the naming pattern:
```
[original_filename]_summary.html
```

The summary includes:
- Meeting overview and context
- Key topics discussed
- Decisions made during the meeting
- Action items with responsible persons
- Participant contributions

## Supported Video Formats

- `.mp4`
- `.mkv`
- `.avi`
- `.mov`
- `.webm`

## How It Works

1. **Video Detection**: The file watcher detects new video files in the monitored folder
2. **Audio Extraction**: Extracts audio from the video using MoviePy
3. **Upload**: Uploads the audio file to Google Gemini
4. **Transcription**: Transcribes the audio to text using Gemini 2.5 Flash
5. **Summarization**: Generates a structured HTML summary using AI
6. **Save**: Saves the summary as an HTML file alongside the original video

## Project Structure

```
.
├── meeting_summary.py    # Main application script
├── requirements.txt      # Python dependencies
├── venv/                # Virtual environment (created during setup)
└── README.md            # This file
```

## Key Dependencies

- **google-generativeai**: Google's Gemini AI API client
- **moviepy**: Video and audio processing
- **watchdog**: File system monitoring
- **imageio-ffmpeg**: FFmpeg integration for MoviePy

## Troubleshooting

### "No module named 'moviepy'" or similar errors
Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg not found
Install FFmpeg using your system's package manager (see Installation section).

### API Key errors
Ensure your Google Gemini API key is valid and has sufficient quota.

### File not processing
- Check that the video file format is supported
- Ensure the file has finished writing before processing (the script waits 5 seconds)
- Check console output for specific error messages

## Customization

### Modify Summary Structure

Edit the `SUMMARY_PROMPT` variable (lines 17-55) to customize the summary format and sections.

### Change Supported Formats

Edit the `SUPPORTED_FORMATS` set on line 16:
```python
SUPPORTED_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
```

### Adjust Processing Delay

Modify the sleep time on line 208 to change how long the script waits after detecting a new file:
```python
time.sleep(5)  # Wait 5 seconds for file to finish writing
```

## Security Considerations

- **API Key**: Never commit your API key to version control. Use environment variables:
  ```python
  import os
  genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
  ```
- **File Permissions**: Ensure the watch folder has appropriate read/write permissions
- **Temporary Files**: The script automatically cleans up temporary audio files after processing

## License

This project is provided as-is for personal and educational use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Acknowledgments

- Google Gemini AI for transcription and summarization
- MoviePy for video processing
- Watchdog for file system monitoring