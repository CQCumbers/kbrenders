import os, time, digitalocean, redis

script = f'''#!/bin/bash
apt-get update -y && \
add-apt-repository ppa:deadsnakes/ppa -y && \
apt-get install -y \
    curl \
    bzip2 \
    git \
    libfreetype6 \
    libgl1-mesa-dev \
    libglu1-mesa \
    libxi6 \
    libxrender1 \
    python3.9 && \
apt-get -y autoremove && \
rm -rf /var/lib/apt/lists/*

wget -O get-pip.py https://bootstrap.pypa.io/get-pip.py && \
python3.9 get-pip.py --no-cache-dir && \
rm -f get-pip.py

export VERSION=2.93
export BLENDER_URL=https://mirror.clarkson.edu/blender/release/Blender2.93/blender-2.93.1-linux-x64.tar.xz
export MODULE_DIR=/usr/local/blender/$VERSION/scripts/modules

mkdir /usr/local/blender && \
curl -SL "$BLENDER_URL" -o blender.tar.xz && \
tar -xvf blender.tar.xz -C /usr/local/blender --strip-components=1 && \
rm blender.tar.xz

git clone --depth 1 {os.environ.get('DROPLET_REPO')} /app
python3.9 -m pip install --no-cache-dir -r /app/requirements.txt && \
    cp -a /usr/local/lib/python3.9/dist-packages/. $MODULE_DIR

export REDIS_URL={os.environ.get('REDIS_EXTERN_URL')}
export MAILGUN_KEY={os.environ.get('MAILGUN_KEY')}
cd app && python3.9 process_queue.py
'''

droplet = digitalocean.Droplet(name='KBRenders',
                               region='nyc1',
                               image='ubuntu-22-04-x64',
                               user_data=script,
                               size_slug='c2-16vcpu-32gb')
queue = redis.from_url(os.environ.get('REDIS_URL'))

while True:
    orders = len(queue.keys('*')) > 0
    if droplet.id and not orders:
        droplet.destroy()
        print(f'Stopping {droplet.id}')
        droplet.id = None
    if not droplet.id and orders:
        droplet.create()
        print(f'Starting {droplet.id}')
    time.sleep(60)
