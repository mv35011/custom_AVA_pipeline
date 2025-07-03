### Install the dependencies
```bash
pip install -r requirements.txt
```
#### Now there might be some numpy and pytorch gpu issues so run these(Dont run the installation from other readme if this is run)
```bash
pip install opencv-python-headless==4.11.0.86

# Uninstall existing PyTorch (if any)
pip uninstall torch torchvision torchaudio

# Install PyTorch with CUDA support
pip install torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install numpy==1.26.4
```
