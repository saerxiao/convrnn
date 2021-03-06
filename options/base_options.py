import argparse
import os
from util import util
import torch
import sys

class BaseOptions():
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.initialized = False

    def initialize(self):
        self.parser.add_argument('--dataroot', help='path to images (should have subfolders train, valid, test)')
        self.parser.add_argument('--valid_folder', type=str, default='valid', help='validation data folder, valid|val')
        self.parser.add_argument('--name', type=str, default='experiment_name', help='name of the experiment. It decides where to store samples and models')
        self.parser.add_argument('--target_type', type=str, default='pdd', help='pdd | fa | mra')
        ### Input options
        self.parser.add_argument('--batchSize', type=int, default=1, help='input batch size')
        self.parser.add_argument('--T', type=int, default=3, help='number of slices in the input slab')
        self.parser.add_argument('--fineSize', type=int, default=256, help='then crop to this size')
        self.parser.add_argument('--input_nc', type=int, default=3, help='# of input image channels')
        self.parser.add_argument('--output_nc', type=int, default=3, help='# of output image channels')
        self.parser.add_argument('--which_direction', type=str, default='AtoB', help='AtoB or BtoA')
        self.parser.add_argument('--serial_batches', action='store_true', help='if true, takes images in order to make batches, otherwise takes them randomly')
        self.parser.add_argument('--max_dataset_size', type=int, default=float("inf"),
                                 help='Maximum number of samples allowed per dataset. If the dataset directory contains more than max_dataset_size, only a subset is loaded.')
        self.parser.add_argument('--no_flip', action='store_true', help='if specified, do not flip the images for data augmentation')
        self.parser.add_argument('--input_channels', nargs='+', help='select input channels, not set meaning all channels')
        self.parser.add_argument('--output_channels', nargs='+', help='Only used when target_type is MRA. select output channels, 0|1|2')
        self.parser.add_argument('--random_rotation', action='store_true', help='if specified, do random rotation on the image')
        self.parser.add_argument('--same_hemisphere', action='store_true', help='if specified flip all channels so that all vectors are in the same hemishere as x1>=0. Specific transformation for PDD')
        self.parser.add_argument('--gaussian', type=float, default=0, help='number of pixels for the blur radius')
        self.parser.add_argument('--minus_gaussian', action='store_true', help='input = original - image with gaussian blurred')
        self.parser.add_argument('--in_protocal', type=str, default='DTI-00', help='input protocal for DTI translation, Not tested for this repo')
        self.parser.add_argument('--out_protocal', type=str, default='T1', help='output protocal for DTI translation, Not tested for this repo')
        ### model options
        self.parser.add_argument('--model', type=str, default='resnet_9blocks',
                                 help='chooses which model to use. resnet_9blocks | resnet_9blocks_3d | resnet_6blocks | unet_128 | unet_128_tanhoff | unet_256 | my_unet | unet_256_3d | unet_128_3d | vae_fc | vae_conv')
        self.parser.add_argument('--ngf', type=int, default=64, help='# of gen filters in first conv layer')
        self.parser.add_argument('--ndf', type=int, default=64, help='# of discrim filters in first conv layer')
        self.parser.add_argument('--which_model_netG', type=str, default='resnet_9blocks', help='selects model to use for netG')
        self.parser.add_argument('--norm', type=str, default='None', help='normalization options: batch (2d) | instance | batch_3d | None')
        self.parser.add_argument('--no_dropout', action='store_true', help='no dropout for the generator')
        self.parser.add_argument('--init_type', type=str, default='normal', help='network initialization [normal|xavier|kaiming|orthogonal]')
        self.parser.add_argument('--use_tanh', action='store_true', help='if specified use tanh after the last layer of decoder in convrnn')
        self.parser.add_argument('--conv_type', type=str, default='2d', help='convolution layer type, 2d|3d')
        self.parser.add_argument('--n_per_conv_layer', type=float, default=1, help='number of layers per conv layer. Only used for VAE')
        self.parser.add_argument('--eval_for_test', action='store_true', help='if specified use eval mode at validation or test')
        ### For GAN only
        self.parser.add_argument('--which_model_netD', type=str, default='basic', help='For GAN only, selects model to use for netD')
        self.parser.add_argument('--n_layers_D', type=int, default=3, help='For GAN only. only used if which_model_netD==n_layers')
        ### Objective options
        self.parser.add_argument('--gan_only', action='store_true', help='if specified, do not include content loss')
        self.parser.add_argument('--content_only', action='store_true', help='if specified, do not include gan loss')
       
        ### System options 
        self.parser.add_argument('--gpu_ids', type=str, default='0', help='gpu ids: e.g. 0  0,1,2, 0,2. use -1 for CPU')
        self.parser.add_argument('--nThreads', default=2, type=int, help='# threads for loading data')
        
        ### Output options
        self.parser.add_argument('--checkpoints_dir', type=str, default='./checkpoints', help='models are saved here')
        self.parser.add_argument('--display_winsize', type=int, default=256, help='display window size')
        self.parser.add_argument('--display_id', type=int, default=0, help='window id of the web display')
        self.parser.add_argument('--display_port', type=int, default=8097, help='visdom port of the web display')
        self.parser.add_argument('--predict_idx_type', type=str, default='last', help='specify which slice to predict for T > 1, first|middle|last')
        self.initialized = True

    def parse(self, argv = sys.argv[1:]):
        if not self.initialized:
            self.initialize()
        self.opt = self.parser.parse_args(argv)
        self.opt.isTrain = self.isTrain   # train or test

        str_ids = self.opt.gpu_ids.split(',')
        self.opt.gpu_ids = []
        for str_id in str_ids:
            id = int(str_id)
            if id >= 0:
                self.opt.gpu_ids.append(id)

        # set gpu ids
        if len(self.opt.gpu_ids) > 0:
            torch.cuda.set_device(self.opt.gpu_ids[0])

        args = vars(self.opt)

        print('------------ Options -------------')
        for k, v in sorted(args.items()):
            print('%s: %s' % (str(k), str(v)))
        print('-------------- End ----------------')

        # save to the disk
        expr_dir = os.path.join(self.opt.checkpoints_dir, self.opt.name)
        util.mkdirs(expr_dir)
        file_name = os.path.join(expr_dir, 'opt.txt')
        with open(file_name, 'wt') as opt_file:
            opt_file.write('------------ Options -------------\n')
            for k, v in sorted(args.items()):
                opt_file.write('%s: %s\n' % (str(k), str(v)))
            opt_file.write('-------------- End ----------------\n')
        return self.opt
