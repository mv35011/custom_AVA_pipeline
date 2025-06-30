import os
import shutil
import sys


if not os.path.exists('./choose_frames_middle'):
    os.makedirs('./choose_frames_middle')
for filepath, dirnames, filenames in os.walk('./choose_frames'):
    if filepath == './choose_frames':
        continue

    if len(filenames) == 0:
        continue
    temp_name = os.path.basename(filepath)
    path_temp_name = os.path.join('./choose_frames_middle', temp_name)
    if not os.path.exists(path_temp_name):
        os.makedirs(path_temp_name)
        print(f"Created directory: {path_temp_name}")

    filenames = sorted(filenames)
    for filename in filenames:
        if "checkpoint" in filename:
            continue
        if "Store" in filename:
            continue

        try:
            temp_num = filename.split('_')[1]
            temp_num = temp_num.split('.')[0]
            temp_num = int(temp_num)


            srcfile = os.path.join(filepath, filename)
            dstpath = os.path.join(path_temp_name, filename)
            if os.path.exists(srcfile):
                shutil.copy(srcfile, dstpath)
                print(f"Copied: {filename} to {temp_name}/")
            else:
                print(f"Source file not found: {srcfile}")

        except (ValueError, IndexError) as e:
            print(f"Skipping file {filename}: {e}")
            continue

print("Processing complete!")
print("Created structure:")
print("./choose_frames_middle/")
for subdir in ['1', '2', '3']:
    subdir_path = os.path.join('./choose_frames_middle', subdir)
    if os.path.exists(subdir_path):
        file_count = len([f for f in os.listdir(subdir_path) if f.endswith('.jpg')])
        print(f"  ├── {subdir}/ ({file_count} files)")
    else:
        print(f"  ├── {subdir}/ (not created)")