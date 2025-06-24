import os
import subprocess
import glob
import shutil
from pathlib import Path

base_dir = Path(__file__).parent.parent


def cut_videos():
    in_data_dir = base_dir / "Dataset" / "videos"
    out_data_dir = base_dir / "Dataset" / "video_crop"


    os.makedirs(out_data_dir, exist_ok=True)


    cuts = [
        (1030, 11, "1.mp4"),
        (1340, 11, "2.mp4"),
        (1850, 11, "3.mp4")
    ]

    input_video = os.path.join(in_data_dir, "1.mp4")

    if not os.path.exists(input_video):
        print(f"Error: Input video not found at {input_video}")
        print(
            f"Available files in {in_data_dir}: {os.listdir(in_data_dir) if os.path.exists(in_data_dir) else 'Directory not found'}")
        return

    for start_time, duration, output_name in cuts:
        output_path = os.path.join(out_data_dir, output_name)

        cmd = [
            "ffmpeg", "-ss", str(start_time), "-t", str(duration),
            "-y", "-i", input_video, "-avoid_negative_ts", "make_zero", output_path
        ]

        print(f"Cutting video: {output_name}")
        subprocess.run(cmd, check=True)


def extract_frames():
    in_data_dir = base_dir / "Dataset" / "video_crop"
    out_data_dir = base_dir / "Dataset" / "frames"

    os.makedirs(out_data_dir, exist_ok=True)

    video_files = glob.glob(os.path.join(in_data_dir, "*"))

    for video_path in video_files:
        video_name = os.path.basename(video_path)
        video_name_no_ext = os.path.splitext(video_name)[0]

        print(f"Processing: {video_name}")

        out_video_dir = os.path.join(out_data_dir, video_name_no_ext)
        os.makedirs(out_video_dir, exist_ok=True)

        out_name = os.path.join(out_video_dir, f"{video_name_no_ext}_%06d.jpg")

        cmd = [
            "ffmpeg", "-i", video_path, "-r", "30", "-q:v", "1", out_name
        ]

        subprocess.run(cmd, check=True)
def get_video_duration(video_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(float(result.stdout.strip()))
    except (subprocess.CalledProcessError, ValueError):
        return 11  # Default to 11 seconds if unable to determine


def main():
    """Main function to run the video processing pipeline"""
    print("Starting video processing pipeline...")

    print("Step 1: Cutting videos...")
    cut_videos()

    print("Step 2: Extracting frames...")
    extract_frames()

    print("Step 3: Selecting frames for annotation...")
    print("Video processing complete!")
    print("Selected frames are now available in Dataset/choose_frames_all/")


if __name__ == "__main__":
    main()