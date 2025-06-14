import srt
import moviepy.editor as mp
from datetime import timedelta
import moviepy.config as mpy_conf
from pathlib import Path
import whisper
import string
from openai import OpenAI


# some stupid shit needed for it to not throw instilation error
mpy_conf.change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})  # ADJUST this path if needed

# some downgrade needed for pillow antialias
from PIL import Image
# Fix for deprecated Image.ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS


current_dir = Path().resolve()
parent_dir = current_dir.parent
filename = input("Folder name (no .extension): ")

fileloc = str(parent_dir / filename / filename)

# read the story
text_file_path = fileloc + ".txt"
with open(text_file_path, "r", encoding="utf-8") as f:
    title = f.readline()
    body = ''.join(f.readlines()).strip()


# TEXT TO SPEECH
# just the title
client = OpenAI()
with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="ash",
    input=title,
    speed=1.2
) as response:
    response.stream_to_file(fileloc+"_title.mp3")

# just the body
with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="ash",
    input=body,
    speed=1.2
) as response:
    response.stream_to_file(fileloc+"_body.mp3")



# TAKE VIDEO AUDIO AND COMBINE THEM
# WRITE THE GENERATED SRT FILE TO THE VIDEO
# Load video and audio
video = mp.VideoFileClip(fileloc+".mp4").without_audio()

# combine title and body audios
audio_title = mp.AudioFileClip(fileloc+"_title.mp3")
audio_body = mp.AudioFileClip(fileloc+"_body.mp3")
full_audio = mp.concatenate_audioclips([audio_title, audio_body])

# set the video to have audio
video = video.set_audio(full_audio)



# TAKE THE MP3 AND CREATE THE SRT FILE (SUBTITLES)
# make subtitles from audio
model = whisper.load_model("turbo")
result = model.transcribe(fileloc+"_body.mp3", verbose=False, word_timestamps=True)

off_set = audio_title.duration
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
        start_time = timedelta(seconds=word_group[0]['start'] + off_set)
        end_time = timedelta(seconds=word_group[-1]['end'] + off_set)

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


# generate background png and title text
title_bg = mp.ImageClip(str(parent_dir/"title.png")).set_duration(audio_title.duration)
title_bg = title_bg.resize(width=video.w-50)  # match video width
title_bg = title_bg.set_position(("center", "center"))


text_width = title_bg.w
text_height = title_bg.h
text_pos = ((video.w - title_bg.w) // 2 + 20, (video.h - title_bg.h) // 2 + 60)

title_text = mp.TextClip(
    title,
    fontsize=50,
    color="black",
    font="Arial-Bold",
    method="caption",
    size=(text_width, text_height),
    align="West"
).set_duration(audio_title.duration).set_position(text_pos)

title_text = title_text.set_duration(audio_title.duration)
title_clip = mp.CompositeVideoClip(
    [title_bg, title_text],
    size=(video.w, video.h)  
).set_duration(audio_title.duration)



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
sub_clips.insert(0, title_clip)

# Combine video with subtitles and trim it to end after story finishes
ending_buffer = 0.5
final = mp.CompositeVideoClip([video] + sub_clips)
final = final.set_duration(full_audio.duration + ending_buffer)

# Export final video
final.write_videofile(fileloc+"_finished.mp4", codec="libx264", audio_codec="aac")
