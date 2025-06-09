import srt
import moviepy.editor as mp
from datetime import timedelta
import moviepy.config as mpy_conf
from pathlib import Path
import whisper
import string

# dependencies
# pip install moviepy
# pip install srt
# download whisper from OpenAI
# download imagemagick from chrome for moviepy to work  *on install check ADD to PATH and Install leacy utilities(convert)

# some stupid shit needed for it to not throw instilation error
mpy_conf.change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})  # ADJUST this path if needed


current_dir = Path(__file__).parent
parent_dir = current_dir.parent

filename = str(parent_dir / input("File name (no .extension): "))


# TAKE THE MP3 AND CREATE THE SRT FILE (SUBTITLES)
# make subtitles from audio
model = whisper.load_model("turbo")
result = model.transcribe(filename+".mp3", verbose=False, word_timestamps=True)

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
        for word_data in word_group:
            word = word_data['word']
            cleaned_word = ""
            for char in word:
                if char not in string.punctuation or char == "'":
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
with open(filename+".srt", "w", encoding="utf-8") as f:
    f.write(srt.compose(subtitles))



# TAKE VIDEO AUDIO AND COMBINE THEM
# WRITE THE GENERATED SRT FILE TO THE VIDEO
# Load video and audio
video = mp.VideoFileClip(filename+".mp4").without_audio()
audio = mp.AudioFileClip(filename+".mp3")
video = video.set_audio(audio)

# Load and parse the .srt file
with open(filename+".srt", "r", encoding="utf-8") as f:
    subtitles = list(srt.parse(f.read()))

# Create text clips for each subtitle
sub_clips = []
for sub in subtitles:
    start = sub.start.total_seconds()
    end = sub.end.total_seconds()
    duration = end - start

    txt_clip = (
        mp.TextClip(sub.content, fontsize=80, color='white', font='Arial-Bold')
        .set_position("center")
        .set_duration(duration)
        .set_start(start)
    )
    sub_clips.append(txt_clip)

# Combine video with subtitles
final = mp.CompositeVideoClip([video] + sub_clips)

# Export final video
final.write_videofile(filename+"_finished.mp4", codec="libx264", audio_codec="aac")
