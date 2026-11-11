# Worship music sources (9pm verse videos)

Royalty-free instrumentals from Pixabay Music, chosen by the account owner. Pixabay Content License: free for
commercial use including social media videos, no attribution required; it does not allow redistributing the
files as-is, so the original MP3s are kept out of git (`audio/worship_src/`, git-ignored). Only edited 30 s beds
(selected section, layered with the birdsong, loudness-normalised, faded) are committed in `web/worship/`.

| File (in audio/worship_src/) | Pixabay track |
|---|---|
| denis-pavlov-beautiful-worship-piano.mp3 | Denis Pavlov Music, "Beautiful Worship Piano, Peaceful Music" (240319) |
| denis-pavlov-worship-piano-peaceful-prayer.mp3 | Denis Pavlov Music, "Worship Piano Instrumental, Peaceful Prayer Music" (223373) |
| leberch-worship-instrumental.mp3 | Leberch, "Worship Instrumental" (587285) |
| leberch-worship-music.mp3 | Leberch, "Worship Music" (590363) |
| zeldafleming-jesus-you-alone.mp3 | zeldafleming_007, "Jesus You Alone" (525581) |

To add tracks: drop the MP3 in `audio/worship_src/`, add its best 30 s sections to `WORSHIP_SECTIONS` in
`make_audio.py`, run `python3 make_audio.py worship`, commit the new beds.
