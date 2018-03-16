import cv2
import os
import argparse
import subprocess


class SFMPipeline:
    OPEN_MVS_DIR = '/usr/local/bin/openMVS'
    EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff'}
    SENSOR_DB = '/home/openMVG/src/openMVG/exif/sensor_width_database/sensor_width_camera_database.txt'

    def __init__(self, input_dir, output_dir):

        # sniff into input_dir, get first image and calculate focal length
        self.f = self.compute_focus()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.dirs = self.init_subdirs()

    def compute_focus(self):
        for dirname, dirnames, filenames in os.walk(self.input_dir):
            for filename in filenames:
                if os.path.splitext(filename)[1] in self.EXTENSIONS:
                    im = cv2.imread(os.path.abspath(os.path.join(dirname, filename)))
                    w, h, channels = im.shape
                    return 1.1 * max(w, h)

    def init_subdirs(self):
        dirs = {}
        dirs['matches'] = "{}/matches".format(self.output_dir)
        dirs['reconstruction'] = "{}/reconstruction".format(self.output_dir)
        dirs['mvs'] = "{}/mvs".format(self.output_dir)
        for key in dirs.keys():
            if not os.path.exists(dirs[key]):
                os.makedirs(dirs[key])
        return dirs

    def init_image_listing(self):
        commands = ['openMVG_main_SfMInit_ImageListing', '-i', self.input_dir, '-d', self.SENSOR_DB, '-o',
                    self.dirs['matches'], '-f', self.f]
        SFMPipeline.do_processing(commands)

    @staticmethod
    def do_processing(commands):
        process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            print(process.stdout.readline())
        print(process.stdout.read())

