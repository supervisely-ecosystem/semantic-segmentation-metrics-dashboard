FROM supervisely/base-py-sdk:6.35.0
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN python3 -m pip install --upgrade pip

RUN pip3 install torch==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
RUN pip3 install torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
RUN pip3 install cupy-cuda12x
