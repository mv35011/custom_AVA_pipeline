import argparse
import sys
import csv
import os

sys.path.insert(0, './yolov5/')

from yolov5.utils.datasets import LoadImages
from yolov5.utils.general import check_img_size, xyxy2xywh
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort

import cv2
import torch
import numpy as np
import torch.backends.cudnn as cudnn
import pickle
from PIL import Image

# dict存放最后的结果
dicts = []


def detect(opt):
    source = opt.source
    stride = 32
    pt = True
    jit = False

    cfg = get_config()
    cfg.merge_from_file(opt.config_deepsort)

    # 加载pickle文件 - Windows path handling
    pkl_path = os.path.normpath('./mywork/dense_proposals_train_deepsort.pkl')
    if not os.path.exists(pkl_path):
        print(f"Error: Pickle file not found at {pkl_path}")
        print(f"Current working directory: {os.getcwd()}")
        return

    with open(pkl_path, 'rb') as f:
        info = pickle.load(f, encoding='iso-8859-1')

    # tempFileName 用以记录当前所处文件
    tempFileName = ''
    deepsort = None

    print(f"Processing {len(info)} detections...")

    # 循环pkl中的信息
    processed_count = 0
    for i in info:
        dets = info[i]
        tempName = i.split(',')

        if len(tempName) < 2:
            print(f"Warning: Invalid key format: {i}")
            continue

        video_name = tempName[0]
        frame_idx = tempName[1]

        # 如果新开启一个文件，deepsort重新开始检测
        if video_name != tempFileName:
            print(f"Processing video: {video_name}")
            try:
                deepsort = DeepSort(
                    cfg.DEEPSORT.REID_CKPT,
                    max_dist=cfg.DEEPSORT.MAX_DIST,
                    min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                    max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                    max_age=cfg.DEEPSORT.MAX_AGE,
                    n_init=cfg.DEEPSORT.N_INIT,
                    nn_budget=cfg.DEEPSORT.NN_BUDGET,
                    use_cuda=True
                )
                tempFileName = video_name
            except Exception as e:
                print(f"Error initializing DeepSort: {e}")
                print("Please check if the model file is downloaded correctly.")
                return

        # 构建图片路径 - Windows compatible
        frame_number = int(frame_idx) * 30 + 1
        img_path = os.path.normpath(os.path.join(source, video_name, f"{video_name}_{frame_number:06d}.jpg"))

        if not os.path.exists(img_path):
            print(f"Warning: Image not found: {img_path}")
            continue

        # 读取图片
        tempImg = cv2.imread(img_path)
        if tempImg is None:
            print(f"Warning: Could not load image: {img_path}")
            continue

        # 获取图片大小 (height, width, channels)
        imgsz = tempImg.shape

        if len(dets) == 0:
            continue

        # 转换坐标格式
        xyxys = torch.FloatTensor(len(dets), 4)
        confs = torch.FloatTensor(len(dets))
        clss = torch.FloatTensor(len(dets))

        for index, det in enumerate(dets):
            # 检查detection格式
            if len(det) < 5:
                print(f"Warning: Invalid detection format: {det}")
                continue

            # 将相对坐标转换为绝对坐标
            xyxys[index][0] = det[0] * imgsz[1]  # x1
            xyxys[index][1] = det[1] * imgsz[0]  # y1
            xyxys[index][2] = det[2] * imgsz[1]  # x2
            xyxys[index][3] = det[3] * imgsz[0]  # y2
            confs[index] = float(det[4])
            clss[index] = 0.  # person class

        # 转换为中心坐标和宽高格式
        xywhs = xyxy2xywh(xyxys)

        # 加载图片用于DeepSort
        im0 = np.array(Image.open(img_path))

        # DeepSort追踪
        outputs = deepsort.update(xywhs, confs, clss, im0)

        # 处理输出结果
        if len(outputs) > 0:
            for output in outputs:
                # 转换回相对坐标
                x1 = output[0] / imgsz[1]
                y1 = output[1] / imgsz[0]
                x2 = output[2] / imgsz[1]
                y2 = output[3] / imgsz[0]

                # 确保坐标在有效范围内
                x1 = max(0, min(1, x1))
                y1 = max(0, min(1, y1))
                x2 = max(0, min(1, x2))
                y2 = max(0, min(1, y2))

                person_id = int(output[4])

                # 存储结果 [video_name, frame_idx, x1, y1, x2, y2, person_id]
                result_dict = [video_name, frame_idx, x1, y1, x2, y2, person_id]
                dicts.append(result_dict)

        processed_count += 1
        if processed_count % 100 == 0:
            print(f"Processed {processed_count}/{len(info)} detections")

    # 保存结果到CSV
    output_csv = opt.output_csv if hasattr(opt, 'output_csv') else '../Dataset/train_personID.csv'

    # 处理Windows路径
    output_csv = os.path.normpath(output_csv)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_csv, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        # 写入标题行
        writer.writerow(['video_name', 'frame_idx', 'x1', 'y1', 'x2', 'y2', 'person_id'])
        writer.writerows(dicts)

    print(f"Results saved to: {output_csv}")
    print(f"Total detections with person IDs: {len(dicts)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--deep_sort_weights', type=str,
                        default='deep_sort_pytorch/deep_sort/deep/checkpoint/ckpt.t7',
                        help='ckpt.t7 path')
    parser.add_argument('--source', type=str, default='0', help='source path to frames')
    parser.add_argument('--output_csv', type=str, default='../Dataset/train_personID.csv',
                        help='output CSV file path')
    parser.add_argument('--save-txt', action='store_true',
                        help='save MOT compliant results to *.txt')
    parser.add_argument('--classes', nargs='+', type=int,
                        help='filter by class: --class 0, or --class 16 17')
    parser.add_argument("--config_deepsort", type=str,
                        default="deep_sort_pytorch/configs/deep_sort.yaml")

    opt = parser.parse_args()

    with torch.no_grad():
        detect(opt)