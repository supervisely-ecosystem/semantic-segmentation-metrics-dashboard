FROM nvidia/cuda:11.1.1-cudnn8-devel-ubuntu20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install python3-pip -y
RUN apt-get install -y git
RUN python3 -m pip install --upgrade pip

RUN pip3 install torch==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
RUN pip3 install torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
RUN pip3 install cupy-cuda111

RUN python3 -m pip install supervisely==6.72.127

RUN apt-get install ffmpeg libgeos-dev libsm6 libxext6 libexiv2-dev libxrender-dev libboost-all-dev -y
RUN pip install opencv-python
