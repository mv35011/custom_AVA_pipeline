# Use NVIDIA CUDA base image with CUDNN and Ubuntu 20.04
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04

# Set non-interactive mode and timezone
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Update packages and install basic dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ninja-build \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    git \
    vim \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.12.0-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

# Set PATH properly (fix legacy warning)
ENV PATH=/opt/conda/bin:$PATH

# Create Conda environment and install everything inside it
RUN conda create -n mmaction python=3.8 -y && \
    conda run -n mmaction pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117 && \
    conda run -n mmaction pip install openmim && \
    conda run -n mmaction mim install mmengine==0.7.2 && \
    conda run -n mmaction mim install "mmcv>=2.0.0rc4,<2.1.0" && \
    git clone https://github.com/open-mmlab/mmaction2.git /mmaction2 && \
    conda run -n mmaction pip install -e /mmaction2 && \
    conda run -n mmaction pip install ipython Pillow scikit-learn pandas

# Create necessary directories
RUN mkdir -p /mmaction2/data /mmaction2/checkpoints

# Set the working directory
WORKDIR /mmaction2

# Activate the environment automatically when the container starts
CMD ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate mmaction && bash"]
