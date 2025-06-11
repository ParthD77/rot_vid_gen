import srt
import moviepy.editor as mp
from datetime import timedelta
import moviepy.config as mpy_conf
from pathlib import Path
import whisper
import string
from openai import OpenAI
# todo: 
#   add the starting reddit image with the tet overlay

# dependencies
# pip install moviepy
# pip install srt
# download whisper from OpenAI
# download imagemagick from chrome for moviepy to work  *on install check ADD to PATH and Install leacy utilities(convert)
# OpenApi key must be set as a env vairable run this in cmd: $env:OPENAI_API_KEY="your-api-key-here" OR
# go into computers env variables and add it there

# To use, in one file location behind this code put your video and a text file with your story. Ensure video and text file have the same name
# and then run the script. 

# some stupid shit needed for it to not throw instilation error
mpy_conf.change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})  # ADJUST this path if needed


current_dir = Path(__file__).parent
parent_dir = current_dir.parent

fileloc = str(parent_dir / input("File name (no .extension): "))

# read the story
text_file_path = fileloc + ".txt"
with open(text_file_path, "r", encoding="utf-8") as f:
    text = f.read().strip()

"""
# TEXT TO SPEECH
client = OpenAI()
with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="ash",
    input=text,
    speed=1.2
) as response:
    response.stream_to_file(fileloc+".mp3")
"""
"""

# TAKE THE MP3 AND CREATE THE SRT FILE (SUBTITLES)
# make subtitles from audio
model = whisper.load_model("turbo")
result = model.transcribe(fileloc+".mp3", verbose=False, word_timestamps=True)

words_per_segment = 2
subtitles = []
index = 1

for segment in result['segments']:
    words = segment.get('words', []) # all words with their time stamp
    i = 0

    while i < len(words):
        word_group = []
        j = 0
        # combine words into desired chunk length
        while j < words_per_segment and (i + j) < len(words):
            word_group.append(words[i + j])
            j += 1

        i += words_per_segment

        if not word_group:
            continue

        # Start and end time for the subtitle chunk
        start_time = timedelta(seconds=word_group[0]['start'])
        end_time = timedelta(seconds=word_group[-1]['end'])

        # Build content string without punctuation
        content = ""
        allowed_punc = ["'", "?", "."]
        for word_data in word_group:
            word = word_data['word']
            cleaned_word = ""
            for char in word:
                if char not in string.punctuation or char in allowed_punc:
                    cleaned_word += char
            content += cleaned_word + " "

        content = content.strip()
        if content == "":
            continue

        # Create and add subtitle object
        subtitle = srt.Subtitle(index=index, start=start_time, end=end_time, content=content)
        subtitles.append(subtitle)
        index += 1

# Write the subtitles to an .srt file
with open(fileloc+".srt", "w", encoding="utf-8") as f:
    f.write(srt.compose(subtitles))

"""

# TAKE VIDEO AUDIO AND COMBINE THEM
# WRITE THE GENERATED SRT FILE TO THE VIDEO
# Load video and audio
video = mp.VideoFileClip(fileloc+".mp4").without_audio()
audio = mp.AudioFileClip(fileloc+".mp3")
video = video.set_audio(audio)


# Load and parse the .srt file
with open(fileloc+".srt", "r", encoding="utf-8") as f:
    subtitles = list(srt.parse(f.read()))

# Create text clips for each subtitle
sub_clips = []
for sub in subtitles:
    start = sub.start.total_seconds()
    end = sub.end.total_seconds()
    duration = end - start

    # make the subtitle display and make them look good
    txt_clip = (
        mp.TextClip(
            sub.content,
            fontsize=120,
            color='white',
            font='Impact',
            stroke_color='black',
            stroke_width=8,  # Thicker stroke = better visibility
            method='label'   # No line-wrapping; text stays compact
        )
        .set_position("center")
        .set_duration(duration)
        .set_start(start)
)
    

    sub_clips.append(txt_clip)


# Combine video with subtitles and trim it to end after story finishes
ending_buffer = 0.5
final = mp.CompositeVideoClip([video] + sub_clips)
final = final.set_duration(audio.duration + ending_buffer)

# Export final video
final.write_videofile(fileloc+"_finished.mp4", codec="libx264", audio_codec="aac")
