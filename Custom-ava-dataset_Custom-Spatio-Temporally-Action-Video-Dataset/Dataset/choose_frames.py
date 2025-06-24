import os
import shutil
import sys

# 传参 这里传入视频多少秒
seconds = int(sys.argv[1])

# 传参 这里传入视频从那一秒开始，这里需要设置为 0
start = int(sys.argv[2])

# 需要检测标注的时间位置[0,1,2,3,4,5,6,7,8,9,10]
frames = range(start, seconds + 1)

# num_frames 存放对应图片的编号
num_frames = []
for i in frames:
    num_frames.append(i * 30 + 1)

# Create base choose_frames directory if it doesn't exist
if not os.path.exists('./choose_frames'):
    os.makedirs('./choose_frames')

# 遍历./frames
for filepath, dirnames, filenames in os.walk('./frames'):
    # Skip the root frames directory, only process subdirectories
    if filepath == './frames':
        continue

    filenames = sorted(filenames)

    # Skip if no files
    if not filenames:
        continue

    # Get the subdirectory name (1, 2, 3, etc.)
    temp_name = os.path.basename(filepath)

    # 在choose_frames下创建对应的目录文件夹
    path_temp_name = os.path.join('./choose_frames', temp_name)
    if not os.path.exists(path_temp_name):
        os.makedirs(path_temp_name)

    # 找到指定的图片，然后移动到choose_frames中对应的文件夹下
    for filename in filenames:
        if "checkpoint" in filename:
            continue
        if "Store" in filename:
            continue

        # Parse frame number from filename
        try:
            temp_num = filename.split('_')[1]
            temp_num = temp_num.split('.')[0]
            temp_num = int(temp_num)
        except (IndexError, ValueError):
            # Skip files that don't match expected naming pattern
            continue

        if temp_num in num_frames:
            # Use original filename for source file
            srcfile = os.path.join(filepath, filename)

            # Create destination filename with proper formatting (matching original behavior)
            temp_num_str = str(temp_num).zfill(6)
            dst_filename = temp_name + "_" + temp_num_str + ".jpg"
            dstpath = os.path.join(path_temp_name, dst_filename)

            # 复制文件
            shutil.copy(srcfile, dstpath)