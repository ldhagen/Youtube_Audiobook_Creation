import os
import subprocess
import time
from multiprocessing import Pool

def process_single_segment(args):
    segment_file, segment_dir, output_dir, temp_audio_dir, edge_tts_path, voice, static_image = args
    
    segment_id = segment_file.replace('segment_', '').replace('.txt', '')
    text_path = os.path.join(segment_dir, segment_file)
    audio_path = os.path.join(temp_audio_dir, f'segment_{segment_id}.mp3')
    video_path = os.path.join(output_dir, f'war_and_peace_{segment_id}.mp4')
    
    if os.path.exists(video_path):
        # Quick check if file is valid
        try:
            check_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return f"Skipping {video_path}, already exists and is valid."
        except:
            pass
        os.remove(video_path)
        
    # 1. Generate Audio
    try:
        tts_cmd = [edge_tts_path, '--voice', voice, '--file', text_path, '--write-media', audio_path]
        subprocess.run(tts_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return f"Error generating audio for {segment_id}: {e}"
        
    # 2. Create Video
    # -c:a aac for better Windows compatibility
    # -movflags +faststart for better streaming/playback
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', static_image, '-i', audio_path,
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
        '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', video_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        if os.path.exists(audio_path): os.remove(audio_path)
        return f"Error generating video for {segment_id}: {e}"
        
    # Clean up audio
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    # Add a small delay to avoid rate-limiting from the TTS service
    time.sleep(15)
        
    return f"Successfully created {video_path}"

def process_segments():
    segment_dir = 'war_and_peace_segments'
    output_dir = 'war_and_peace_mp4s'
    temp_audio_dir = 'war_and_peace_audio'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_audio_dir, exist_ok=True)
    
    edge_tts_path = '/home/ldhagen/venvs/edge/bin/edge-tts'
    voice = 'en-US-ChristopherNeural'
    static_image = 'warandpeace.jpg'
    
    # Get sorted list of segments
    segments = sorted([f for f in os.listdir(segment_dir) if f.startswith('segment_') and f.endswith('.txt')])
    
    tasks = [(s, segment_dir, output_dir, temp_audio_dir, edge_tts_path, voice, static_image) for s in segments]
    
    print(f"Starting parallel processing with 4 workers for {len(segments)} segments...", flush=True)
    
    with Pool(processes=4) as pool:
        for result in pool.imap_unordered(process_single_segment, tasks):
            print(result, flush=True)

if __name__ == "__main__":
    process_segments()
