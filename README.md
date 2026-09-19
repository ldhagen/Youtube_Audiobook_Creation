# War and Peace: Full Audiobook & Video Processing Pipeline

Automated pipeline for converting Leo Tolstoy's *War and Peace* into YouTube-ready, multi-part video audiobooks (under 1 hour per part) using Microsoft Edge TTS and FFmpeg.

---

## 1. Pipeline Overview

The workflow transforms a monolithic plain-text book (`warandpeace.txt`, ~3.36 MB) into 144 standalone MP4 videos (`War_and_Peace_001.mp4` through `War_and_Peace_144.mp4`), each pairing high-fidelity synthesized speech with static cover art (`warandpeace.jpg`).

```
warandpeace.txt
      │
      ▼
prepare_segments.py  ──►  144 Text Segments (~8,500 words each, newline-sanitized)
                                │
                                ▼
process_segments.py  ──►  Parallel Edge-TTS & FFmpeg Processing (4 workers)
                                │
                                ├──► Temporary Audio (war_and_peace_audio/)
                                └──► Final MP4s (war_and_peace_mp4s/)
```

---

## 2. Identified Scripts & Technical Breakdown

### A. Text Preparation & Chunking: `prepare_segments.py`

* **Source File**: [`prepare_segments.py`](prepare_segments.py)
* **Input**: `warandpeace.txt`
* **Output**: Directory `war_and_peace_segments/` containing `segment_001.txt` through `segment_144.txt`

#### Key Functions:
* **TOC & Header Stripping (`split_text`)**:
  * Detects the beginning of the actual novel by locating the second instance of `"BOOK ONE: 1805"` (skipping the Table of Contents) or falling back to `"*** START"`.
  * Scans for structural book and chapter headings using regular expressions:
    ```python
    marker_pattern = r'\n\s*(BOOK|CHAPTER|FIRST EPILOGUE|SECOND EPILOGUE) [IVXLCDM0-9 :\-]+\n'
    ```
* **Target Word Count Partitioning**:
  * Groups natural chapters together until reaching `target_word_count=8500` words, ensuring resulting video durations stay under the 1-hour threshold suitable for YouTube uploads.
* **Pause Elimination (`clean_segment`)**:
  * Raw text line breaks cause Edge TTS to insert awkward pauses mid-sentence.
  * The script collapses single newlines (`(?<!\n)\n(?!\n)`) into spaces while keeping double newlines for paragraph pauses.

---

### B. Speech Synthesis & Video Encoding: `process_segments.py`

* **Source File**: [`process_segments.py`](process_segments.py)
* **Inputs**:
  * Segment text files: `war_and_peace_segments/segment_*.txt`
  * Static cover image: `warandpeace.jpg`
* **Outputs**:
  * Intermediate audio: `war_and_peace_audio/segment_*.mp3` (automatically cleaned up)
  * Final MP4 videos: `war_and_peace_mp4s/War_and_Peace_*.mp4`

#### Key Components:
* **Parallel Processing**:
  * Uses Python's `multiprocessing.Pool(processes=4)` to distribute segments across 4 worker processes.
* **TTS Engine & Voice**:
  * Binary: `/home/ldhagen/venvs/edge/bin/edge-tts`
  * Voice profile: `en-US-ChristopherNeural`
  * Pacing: Includes a 15-second delay (`time.sleep(15)`) between segment jobs to prevent rate-limiting or throttling from the upstream TTS service.
* **FFmpeg Video Generation**:
  * Merges the looped static image with the generated speech audio:
    ```bash
    ffmpeg -y -loop 1 -i warandpeace.jpg -i segment_XXX.mp3 \
      -vf scale=trunc(iw/2)*2:trunc(ih/2)*2 \
      -c:v libx264 -tune stillimage -pix_fmt yuv420p \
      -c:a aac -b:a 192k -movflags +faststart -shortest \
      war_and_peace_XXX.mp4
    ```
  * **Windows & Streaming Compatibility**:
    * `-c:a aac -b:a 192k`: Uses AAC audio codec instead of raw MP3 in MP4, resolving playback errors on default Windows media players.
    * `-pix_fmt yuv420p`: Standardizes pixel format for universal player support.
    * `-movflags +faststart`: Moves metadata atom to the front for smooth streaming.
* **Validation & Resume Capability**:
  * Runs `ffprobe` prior to processing each segment to verify if an existing MP4 is valid. If valid, the segment is skipped, enabling seamless resumption if interrupted.

---

## 3. Directory Structure

```
/home/ldhagen/ttl_work/
├── prepare_segments.py              # Segmentation & text cleaning script
├── process_segments.py              # Parallel TTS & video encoding script
├── warandpeace.txt                  # Full text source (Tolstoy)
├── warandpeace.jpg                  # Static video thumbnail/background
├── war_and_peace_segments/          # 144 cleaned text chunks (segment_001.txt - segment_144.txt)
├── war_and_peace_audio/             # Temporary intermediate MP3 scratch directory
├── war_and_peace_mp4s/              # 144 generated MP4s (War_and_Peace_001.mp4 - War_and_Peace_144.mp4)
└── war_and_peace_mp4s_backup/       # Full backup of the 144 MP4 files
```

---

## 4. Dependencies & Prerequisites

1. **Python 3**:
   * Standard libraries used: `os`, `re`, `subprocess`, `time`, `multiprocessing`.
2. **edge-tts**:
   * Installed in virtual environment: `/home/ldhagen/venvs/edge/bin/edge-tts`
   * Installation: `pip install edge-tts`
3. **FFmpeg & FFprobe**:
   * Required on system `$PATH` for audio/video muxing and stream validation.

---

## 5. Execution Steps

To reproduce or resume the processing from scratch:

```bash
cd /home/ldhagen/ttl_work

# Step 1: Slice and clean text into ~8,500 word segments
python3 prepare_segments.py

# Step 2: Run parallel TTS synthesis and MP4 creation
python3 process_segments.py

# Step 3 (Optional): Create a backup directory
cp -r war_and_peace_mp4s war_and_peace_mp4s_backup

# Step 4 (Optional): Rename to Title Case if needed
cd war_and_peace_mp4s
for f in war_and_peace_*.mp4; do
    mv "$f" "$(echo $f | sed 's/war_and_peace_/War_and_Peace_/')"
done
```
