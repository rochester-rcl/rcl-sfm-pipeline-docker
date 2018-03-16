# using jromphf/python3-opencv-ffmpeg
FROM jromphf/python3-opencv-ffmpeg:0.0.6

CMD ["/sbin/my_init"]

RUN apt-get update \
  && apt-get install --no-install-recommends -y libcgal-dev \
  libglu1-mesa-dev \
  libxxf86vm1 \
  libxxf86vm-dev \
  libxi-dev \
  libxrandr-dev \
  libcgal-qt5-dev \
  freeglut3-dev \
  libglew-dev \
  libglfw3-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

  WORKDIR /home
  # NEED TO REBUILD CERES w/ older Eigen than one in base image

  RUN git clone https://github.com/eigenteam/eigen-git-mirror.git eigen \
  && cd eigen \
  && git checkout tags/3.2.9 \
  && cd /home \
  && mkdir /usr/include/eigen3/3.2.9 \
  && cp -r eigen/Eigen /usr/include/eigen3/3.2.9 \
  && cp -r eigen/unsupported /usr/include/eigen3/3.2.9 \
  && rm -rf ceres-solver/build \
  && mkdir ceres-solver/build \
  && cd ceres-solver/build \
  && cmake .. -DEIGEN_INCLUDE_DIR_HINTS=/usr/include/eigen3/3.2.9 \
  && make -j4 \
  && make install \
  && cd /home \
  && git clone https://github.com/cdcseacave/VCG.git vcglib \
  && git clone --recursive https://github.com/openMVG/openMVG.git \
  && mkdir openMVG_build \
  && cd openMVG_build \
  && cmake -DCMAKE_BUILD_TYPE=RELEASE ../openMVG/src/ \
  && make -j4 \
  && make install \
  && cd /home \
  && git clone https://github.com/cdcseacave/openMVS.git openMVS \
  && mkdir openMVS_build \
  && cd openMVS_build \
  && cmake ../openMVS -DCMAKE_BUILD_TYPE=Release -DEIGEN_DIR=/usr/include/eigen3/3.2.9 -DVCG_DIR="/home/vcglib" -DOpenMVS_USE_CUDA=OFF \
  && make -j4 \
  && make install

  COPY sfm_pipeline /home/sfm_pipeline
  WORKDIR /home/sfm_pipeline
  RUN python3 setup.py sdist \
  && pip3 install -e .
  WORKDIR /home
