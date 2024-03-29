import os, cv2, glob
import numpy as np
import pandas as pd
import torch
import torch.utils.data as data
from torchvision import datasets, models, transforms
from PIL import Image
import settings

from albumentations import (
    HorizontalFlip, IAAPerspective, ShiftScaleRotate, CLAHE, RandomRotate90, RandomBrightnessContrast,
    Transpose, ShiftScaleRotate, Blur, OpticalDistortion, GridDistortion, HueSaturationValue, RandomSizedCrop,
    IAAAdditiveGaussianNoise, GaussNoise, MotionBlur, MedianBlur, IAAPiecewiseAffine, VerticalFlip,
    IAASharpen, IAAEmboss, RandomContrast, RandomBrightness, Flip, OneOf, Compose, RandomGamma, ElasticTransform, ChannelShuffle,RGBShift, Rotate
)

DATA_DIR = settings.DATA_DIR


def img_augment(p=.8):
    return Compose([
        HorizontalFlip(.5),
        OneOf([
                CLAHE(clip_limit=2),
                IAASharpen(),
                IAAEmboss(),
                RandomContrast(),
                RandomBrightness(),
            ], p=0.3),
        #
        ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=20, p=.75 ),
        Blur(blur_limit=3, p=.33),
        OpticalDistortion(p=.33),
        GridDistortion(p=.33),
        #HueSaturationValue(p=.33)
    ], p=p)

class ImageDataset(data.Dataset):
    def __init__(self, df, img_dir, train_mode=True, test_data=False):
        self.input_size = 224
        self.df = df
        self.img_dir = img_dir
        self.train_mode = train_mode
        self.test_data = test_data

    def __getitem__(self, index):
        row = self.df.iloc[index]
        if self.test_data:
            fn = os.path.join(self.img_dir, os.path.basename(row['file_name']))
        else:
            fn = os.path.join(self.img_dir, row['types'], str(row['category_id']), os.path.basename(row['file_name']))
        #print(fn)
        
        # cv2 and albumentations
        img = cv2.imread(fn)
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.train_mode:
            aug = img_augment(p=0.8)
            img = aug(image=img)['image']
        
        img = transforms.functional.to_tensor(img)
        img = transforms.functional.normalize(img, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        
        if self.test_data:
            return img
        else:
            return img, row['category_id']

    def __len__(self):
        return len(self.df)

    def collate_fn(self, batch):
        if self.test_data:
            return torch.stack(batch)
        else:
            imgs = torch.stack([x[0] for x in batch])
            labels = torch.tensor([x[1] for x in batch])
            return imgs, labels

def get_train_val_loaders(batch_size=4, dev_mode=False, val_num=6000, val_batch_size=256):
    train_df = pd.read_csv(os.path.join(DATA_DIR, 'train.csv'))
    val_df = pd.read_csv(os.path.join(DATA_DIR, 'val.csv'))
    
    if dev_mode:
        train_df = train_df[:10]
        val_df = val_df[:10]
    
    #print('train df:', train_df.shape)
    #print('val df:', len(val_df))
    #print(val_df.head())
    #print(val_df.iloc[0])

    train_set = ImageDataset(train_df, settings.TRAIN_IMG_DIR, train_mode=True)
    val_set = ImageDataset(val_df, settings.TRAIN_IMG_DIR, train_mode=False)
    
    train_loader = data.DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=8, collate_fn=train_set.collate_fn, drop_last=True)
    train_loader.num = len(train_set)

    val_loader = data.DataLoader(val_set, batch_size=val_batch_size, shuffle=False, num_workers=8, collate_fn=val_set.collate_fn, drop_last=False)
    val_loader.num = len(val_set)

    return train_loader, val_loader

def get_test_loader(batch_size=1024, dev_mode=False):
    df = pd.read_csv(os.path.join(DATA_DIR, 'test.csv'))
    if dev_mode:
        df = df[:10]
    test_set = ImageDataset(df, settings.TEST_IMG_DIR, train_mode=False, test_data=True)
    test_loader = data.DataLoader(test_set, batch_size=batch_size, shuffle=False, num_workers=8, collate_fn=test_set.collate_fn, drop_last=False)
    test_loader.num = len(test_set)

    return test_loader


def test_train_val_loader():
    train_loader, val_loader = get_train_val_loaders(dev_mode=True)
    for img, label in val_loader:
        print(img.size(), img)
        print(label)
        break

def test_test_loader():
    test_loader = get_test_loader(batch_size=4, dev_mode=True)
    for img in test_loader:
        print(img.size(), img)


if __name__ == '__main__':
    #test_train_val_loader()
    test_test_loader()
