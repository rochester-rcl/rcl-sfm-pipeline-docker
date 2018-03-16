import cv2
import os
import argparse
import subprocess
import sys
import time
import shutil


class SFMPipeline:
    OPEN_MVS_DIR = '/usr/local/bin/OpenMVS'
    EXTENSIONS = {'.jpg', '.jpeg', '.JPG', '.png', '.tiff'}
    OPEN_MVS_EXTENSIONS = {'.dmap', '.log'}
    SENSOR_DB = '/home/openMVG/src/openMVG/exif/sensor_width_database/sensor_width_camera_database.txt'

    def __init__(self, input_dir, output_dir, **kwargs):

        # sniff into input_dir, get first image and calculate focal length
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.dirs = self.init_subdirs()
        self.f = self.compute_focus()
        try:
            self.n_views = kwargs['n_views_fuse']
        except KeyError:
            self.n_views = 0  # all

    def compute_focus(self):
        for dirname, dirnames, filenames in os.walk(self.input_dir):
            for filename in filenames:
                if os.path.splitext(filename)[1] in self.EXTENSIONS:
                    im = cv2.imread(os.path.abspath(os.path.join(dirname, filename)))
                    w, h, channels = im.shape
                    return 1.1 * max(w, h)

    def cleanup(self):
        for filename in os.listdir(os.getcwd()):
            if os.path.splitext(filename)[1] in self.OPEN_MVS_EXTENSIONS:
                shutil.move(os.path.abspath(filename), os.path.abspath(os.path.join(self.dirs['mvs'], filename)))

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
                    self.dirs['matches'], '-f', str(self.f)]
        SFMPipeline.do_processing(commands)

    def compute_features(self):
        commands = ['openMVG_main_ComputeFeatures', '-i',
                    '{}/sfm_data.json'.format(self.dirs['matches']), '-o', self.dirs['matches'], '-p', 'HIGH']
        SFMPipeline.do_processing(commands)

    def compute_matches(self):
        commands = ['openMVG_main_ComputeMatches', '-i', '{}/sfm_data.json'.format(self.dirs['matches']), '-o',
                    self.dirs['matches'], ]
        SFMPipeline.do_processing(commands)

    def incremental_sfm(self):
        commands = ['openMVG_main_IncrementalSfM', '-i', '{}/sfm_data.json'.format(self.dirs['matches']), '-m',
                    self.dirs['matches'], '-o', self.dirs['reconstruction'], ]
        SFMPipeline.do_processing(commands)

    def compute_structure_from_known_poses(self):
        commands = ['openMVG_main_ComputeStructureFromKnownPoses', '-i',
                    '{}/sfm_data.bin'.format(self.dirs['reconstruction']), '-m', self.dirs['matches'], '-o',
                    '{}/robust.json'.format(self.dirs['reconstruction'])]
        SFMPipeline.do_processing(commands)

    def compute_sfm_data_color(self):
        commands = ['openMVG_main_ComputeSfM_DataColor', '-i', '{}/robust.json'.format(self.dirs['reconstruction']),
                    '-o', '{}/sfm_colored.ply'.format(self.dirs['reconstruction'])]
        SFMPipeline.do_processing(commands)

    def open_mvg_to_open_mvs(self):
        commands = ['openMVG_main_openMVG2openMVS', '-i', '{}/robust.json'.format(self.dirs['reconstruction']), '-o',
                    '{}/scene.mvs'.format(self.dirs['mvs']), '-d', self.dirs['mvs'], ]
        SFMPipeline.do_processing(commands)

    def densify_cloud(self):
        commands = ['{}/DensifyPointCloud'.format(self.OPEN_MVS_DIR), '{}/scene.mvs'.format(self.dirs['mvs']),
                    '--number-views-fuse', str(self.n_views)]
        SFMPipeline.do_processing(commands)

    def reconstruct_mesh(self):
        commands = ['{}/ReconstructMesh'.format(self.OPEN_MVS_DIR), '{}/scene_dense.mvs'.format(self.dirs['mvs'])]
        SFMPipeline.do_processing(commands)

    # NOT BOTHERING WITH REFINEMENT FOR NOW -- TOO MEMORY INTENSIVE FOR WHAT WE'RE DOING
    def refine_mesh(self):
        commands = ['{}/ReconstructMesh'.format(self.OPEN_MVS_DIR), '{}/scene_dense_mesh.mvs'.format(self.dirs['mvs'])]
        SFMPipeline.do_processing(commands)

    def texture_mesh(self):
        commands = ['{}/TextureMesh'.format(self.OPEN_MVS_DIR), '{}/scene_dense_mesh.mvs'.format(self.dirs['mvs']),
                    '--export-type', 'obj', '--empty-color', '00000000']
        SFMPipeline.do_processing(commands)

    def run_all(self):
        start = time.time()
        self.init_image_listing()
        self.compute_features()
        self.compute_matches()
        self.incremental_sfm()
        self.compute_structure_from_known_poses()
        self.compute_sfm_data_color()
        self.open_mvg_to_open_mvs()
        self.densify_cloud()
        self.reconstruct_mesh()
        self.texture_mesh()
        end = time.time()
        print("Successfully completed SFM pipeline in {} seconds".format(end - start))
        print("Cleaning up working directory")
        self.cleanup()
        print("Done")

    @staticmethod
    def do_processing(commands):
        process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while process.poll() is None:
                print(process.stdout.readline().decode('utf-8'))
            print(process.stdout.read().decode('utf-8'))
        except subprocess.CalledProcessError as error:
            print(error)
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scripted example of OpenMVG - OpenMVS SfM Pipeline")
    parser.add_argument('-d', '--dir', help='input directory of images', required=True)
    parser.add_argument('-o', '--out_dir', help='output directory to save everything in', required=True)
    parser.add_argument('-n', '--n_views', help='the number of matching views to use for constructing the dense cloud',
                        required=False, default=0)
    args = vars(parser.parse_args())

    in_dir = args['dir']
    out_dir = args['out_dir']
    n_views = args['n_views']

    sfm = SFMPipeline(in_dir, out_dir, n_views=n_views)
    sfm.run_all()
