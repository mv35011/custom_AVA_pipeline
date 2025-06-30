_base_ = [
    '/workspace/mmaction2/configs/_base_/datasets/ava_kinetics-rgb.py',
    '/workspace/mmaction2/configs/_base_/default_runtime.py'
]

# Model settings - Using TimeSformer as alternative or train MViT from scratch
model = dict(
    type='AVAFastRCNN',
    backbone=dict(
        type='TimeSformer',  # Alternative that's more stable
        img_size=224,
        patch_size=16,
        embed_dims=768,
        in_channels=3,
        num_frames=8,
        attention_type='divided_space_time',
        norm_cfg=dict(type='LN', eps=1e-6),
        pretrained=None,  # Train from scratch or use available weights
    ),
    roi_head=dict(
        type='AVARoIHead',
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor3D',
            roi_layer_type='RoIAlign3D',
            output_size=8,
            with_temporal_pool=True,
        ),
        bbox_head=dict(
            type='BBoxHeadAVA',
            in_channels=768,
            num_classes=80,  # Adjust based on your classes
            multilabel=True,
            dropout_ratio=0.5,
        ),
    ),
    data_preprocessor=dict(
        type='ActionDataPreprocessor',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        format_shape='NCTHW',
    ),
    train_cfg=dict(
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssignerAVA',
                pos_iou_thr=0.9,
                neg_iou_thr=0.9,
                min_pos_iou=0.9,
            ),
            sampler=dict(
                type='RandomSampler',
                num=32,
                pos_fraction=1,
                neg_pos_ub=-1,
                add_gt_as_proposals=True,
            ),
        )
    ),
    test_cfg=dict(rcnn=dict(action_thr=0.002))
)

# Dataset settings (same as before)
dataset_type = 'AVADataset'
data_root = '/workspace/data/ava/rawframes'
anno_root = '/workspace/data/ava/annotations'
ann_file_train = f'{anno_root}/ava_train_v2.2.csv'
ann_file_val = f'{anno_root}/ava_val_v2.2.csv'
exclude_file_train = f'{anno_root}/ava_train_excluded_timestamps_v2.2.csv'
exclude_file_val = f'{anno_root}/ava_val_excluded_timestamps_v2.2.csv'
label_file = f'{anno_root}/ava_action_list_v2.2_for_activitynet_2019.pbtxt'
proposal_file_train = '/workspace/data/ava/proposals/ava_dense_proposals_train.FAIR.recall_93.9.pkl'
proposal_file_val = '/workspace/data/ava/proposals/ava_dense_proposals_val.FAIR.recall_93.9.pkl'

train_pipeline = [
    dict(type='SampleAVAFrames', clip_len=8, frame_interval=8),
    dict(type='RawFrameDecode'),
    dict(type='RandomRescale', scale_range=(256, 320)),
    dict(type='RandomCrop', size=224),
    dict(type='Flip', flip_ratio=0.5),
    dict(type='FormatShape', input_format='NCTHW', collapse=True),
    dict(type='PackActionInputs')
]

val_pipeline = [
    dict(type='SampleAVAFrames', clip_len=8, frame_interval=8, test_mode=True),
    dict(type='RawFrameDecode'),
    dict(type='Resize', scale=(-1, 256)),
    dict(type='CenterCrop', crop_size=224),
    dict(type='FormatShape', input_format='NCTHW', collapse=True),
    dict(type='PackActionInputs')
]

train_dataloader = dict(
    batch_size=4,  # Reduced for stability
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type=dataset_type,
        ann_file=ann_file_train,
        exclude_file=exclude_file_train,
        pipeline=train_pipeline,
        label_file=label_file,
        proposal_file=proposal_file_train,
        data_prefix=dict(img=data_root),
    )
)

val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type=dataset_type,
        ann_file=ann_file_val,
        exclude_file=exclude_file_val,
        pipeline=val_pipeline,
        label_file=label_file,
        proposal_file=proposal_file_val,
        data_prefix=dict(img=data_root),
        test_mode=True,
    )
)

test_dataloader = val_dataloader

# Evaluation settings
val_evaluator = dict(
    type='AVAMetric',
    ann_file=ann_file_val,
    label_file=label_file,
    exclude_file=exclude_file_val
)
test_evaluator = val_evaluator

# Training settings
train_cfg = dict(
    type='EpochBasedTrainLoop',
    max_epochs=20,
    val_interval=2,
)

val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')

# Optimizer settings
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=1e-4, weight_decay=0.05),
    paramwise_cfg=dict(norm_decay_mult=0.0, bias_decay_mult=0.0),
    clip_grad=dict(max_norm=1.0),
)

# Learning rate scheduler
param_scheduler = [
    dict(
        type='LinearLR',
        start_factor=0.1,
        by_epoch=True,
        begin=0,
        end=2,
        convert_to_iter_based=True
    ),
    dict(
        type='CosineAnnealingLR',
        T_max=18,
        eta_min=0,
        by_epoch=True,
        begin=2,
        end=20,
        convert_to_iter_based=True
    )
]

# Runtime settings
default_hooks = dict(
    checkpoint=dict(type='CheckpointHook', interval=2, max_keep_ckpts=3, save_best='auto'),
    logger=dict(type='LoggerHook', interval=20, ignore_last=False),
)

# Working directory
work_dir = '/workspace/work_dirs/timesformer_ava_custom'

# No pretrained model - train from scratch
load_from = None
