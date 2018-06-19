## load T continuous slices at each __getitem__
import torch.utils.data as data
from PIL import Image
import torch
import random
import torchvision.transforms as transforms
import os.path
import glob
import re

def _get_subject_slice(filepath):
  m = re.match(r'(.*)-(\d+).png', os.path.basename(filepath))
  return m.group(1), int(m.group(2))

class SliceDataset(data.Dataset):
  def __init__(self, opt):
    super(SliceDataset, self).__init__()
    self.dir_AB = os.path.join(opt.dataroot, opt.phase)
    subjects = {}
    files = glob.glob("{}/*.png".format(self.dir_AB))
    for f in files:
      subject, slice_id = _get_subject_slice(f)
      if subject in subjects:
        info = subjects[subject]
        min_id, max_id = info['min'], info['max']
        if slice_id < info['min']:
          min_id = slice_id
        if slice_id > info['max']:
          max_id = slice_id
        cnt = info['cnt'] + 1
      else:
        min_id = slice_id
        max_id = slice_id
        cnt = 1
      subjects[subject] = {'min':min_id, 'max':max_id, 'cnt':cnt}
      #print(subjects[subject])
    
    indices = []
    subject_lookup = []
    i = 0
    for subject, info in subjects.items():
      assert(info['max'] - info['min'] + 1 == info['cnt'])
      subject_lookup.append(subject)
      for j in range(info['cnt']-opt.T+1):
        indices.append([i,info['min'] + j])
      i = i + 1
  
    self.indices = indices
    self.subject_lookup = subject_lookup
    self.T = opt.T
    self.opt = opt
    if opt.predict_idx_type == 'last':
      self.predict_idx = opt.T - 1
    elif opt.predict_idx_type == 'middle':
      self.predict_idx = int(opt.T / 2)
    
    print("---------------- {} dataset contains {} samples ----------------".format(opt.phase, self.__len__()))

  def __getitem__(self, idx):
    subject = self.subject_lookup[self.indices[idx][0]]
    slice_start = self.indices[idx][1]
    ABs = []
    for i in range(self.T):
      fname = "%s/%s-%03d.png" % (self.dir_AB, subject, slice_start + i)
      if i == self.predict_idx:
        AB_path = fname
      img = Image.open(fname).convert('RGB')
      AB = transforms.ToTensor()(img)
      AB = transforms.Normalize((0.5, 0.5, 0.5),(0.5, 0.5, 0.5))(AB)
      ABs.append(AB)

    AB = torch.stack(ABs, 0)  ## AB: [T,C,H,W], tensor, value in [-1,1]
    w_total = AB.size(3)
    w = int(w_total / 2)
    h = AB.size(2)
    w_offset = random.randint(0, max(0, w - self.opt.fineSize - 1))
    h_offset = random.randint(0, max(0, h - self.opt.fineSize - 1))
    A = AB[:, :, h_offset:h_offset + self.opt.fineSize,
             w_offset:w_offset + self.opt.fineSize]
    B = AB[:, :, h_offset:h_offset + self.opt.fineSize,
             w + w_offset:w + w_offset + self.opt.fineSize]

    A_original = A.clone()
    if self.opt.input_channels:
      if len(self.opt.input_channels) == 1:
        A[:, 0, ...] = A_original[:, int(self.opt.input_channels[0]), ...]
        A[:, 1, ...] = A[:, 0, ...]
        A[:, 2, ...] = A[:, 0, ...]
      elif len(self.opt.input_channels) == 2:
        A[:, 0, ...] = A_original[:, int(self.opt.input_channels[0]), ...]
        A[:, 1, ...] = A_original[:, int(self.opt.input_channels[1]), ...]
        A[:, 2, ...] = A_original[:, 0, ...] * 0.5 + A_original[:, 1, ...] * 0.5

    if self.opt.output_channels:
      # assume output only has at most one channel
      if len(self.opt.output_channels) == 1:
        B[:, 0, ...] = A_original[:, int(self.opt.output_channels[0]), ...]
        B[:, 1, ...] = B[:, 0, ...]
        B[:, 2, ...] = B[:, 0, ...]
    
    if self.opt.which_direction == 'BtoA':
      input_nc = self.opt.output_nc
      output_nc = self.opt.input_nc
    else:
      input_nc = self.opt.input_nc
      output_nc = self.opt.output_nc   

    if input_nc == 1:  # RGB to gray
      tmp = A[:, 0, ...] * 0.299 + A[:, 1, ...] * 0.587 + A[:, 2, ...] * 0.114
      A = tmp.unsqueeze(1)

    if output_nc == 1:  # RGB to gray
      tmp = B[:, 0, ...] * 0.299 + B[:, 1, ...] * 0.587 + B[:, 2, ...] * 0.114
      B = tmp.unsqueeze(1)

    return {'A': A, 'B': B, 'AB_path':AB_path} ## AB_path is the path of the last slice
      
  def __len__(self):
    return len(self.indices)

  def name(self):
    return 'SliceDataset' 