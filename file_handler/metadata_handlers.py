# filehandler/metadata_handlers.py
from PIL import Image
from tinytag import TinyTag
import textract
import subprocess

# Get the size of an image file
def get_image_size(file_path):
    with Image.open(file_path) as img:
        return img.size

# Get the duration of an audio file
def get_audio_duration(file_path):
    tag = TinyTag.get(file_path)
    return tag.duration

# Get the word count of a document
def get_document_word_count(file_path):
    text = textract.process(file_path).decode('utf-8')
    return len(text.split())

# Get the duration of a video file using ffprobe (ffmpeg) command line tool
def get_video_duration(file_path):
    supported_formats = [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
    _, ext = os.path.splitext(file_path)

    if ext.lower() not in supported_formats:
        raise ValueError(f"Unsupported video format: {ext}")

    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {file_path}"
    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()

    return int(float(output))
