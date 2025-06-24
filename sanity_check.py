import os, cv2, pandas as pd

df = pd.read_csv("Dataset/annotations/ava_train.csv")
for video_id in df.video_id.unique():
    for ts in df[df.video_id == video_id].timestamp.unique():
        frame_path = f"frames/{video_id}/img_{ts+1:05d}.jpg"  # because timestamp = frame_idx - 1
        frame = cv2.imread(frame_path)
        if frame is None: continue
        h, w = frame.shape[:2]
        temp_df = df[(df.video_id == video_id) & (df.timestamp == ts)]
        for _, row in temp_df.iterrows():
            x1, y1 = int(row.x1 * w), int(row.y1 * h)
            x2, y2 = int(row.x2 * w), int(row.y2 * h)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.imwrite(f"sanity_vis/vid{video_id}_ts{ts}.jpg", frame)
