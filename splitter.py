import srt
from datetime import timedelta
import string

filename = input(".srt File Name (include .srt)")

with open(filename, "r", encoding="utf-8") as file:
    subtitles = list(srt.parse(file.read())) # list of subtitle objects

new_subtitles = []
new_index = 1
words_at_time = 2

# split the large subtitle chucnk into words
for sub in subtitles:
    words = sub.content.split()
    if not words:
        continue

    # reconnect words into desire length and removes puncuation
    chunks = []
    for i in range(0, len(words), words_at_time):
        small_bit = " ".join(words[i:i+words_at_time])
        clean_bit = ""
        for char in small_bit:
            if char not in string.punctuation:
                clean_bit += char
        chunks.append(clean_bit)



    # get characters in large chunk and how long the chunck originally was (time wise)
    total_chars = sum(len(chunk) for chunk in chunks)
    total_duration = sub.end - sub.start

    if total_chars == 0:
        continue

    # display the small chunk depending on how many characters it has compared to the large chunk
    # this maintains total time and adjusts for longer/shorter words
    start_time = sub.start
    for chunk in chunks:
        proportion = len(chunk) / total_chars
        chunk_duration = total_duration * proportion
        end_time = start_time + chunk_duration

        new_subtitles.append(srt.Subtitle(index=new_index, start=start_time, end=end_time,
                                           content=chunk, proprietary=''))
        new_index += 1
        start_time = end_time

# write
output_filename = filename.replace(".srt", "_split.srt")
with open(output_filename, "w", encoding="utf-8") as out_file:
    out_file.write(srt.compose(new_subtitles))

