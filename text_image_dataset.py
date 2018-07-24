import io
from torch.utils.data import Dataset
import numpy as np
from PIL import Image
import torch
import h5py
import random
import os
import config

class Text2ImageDataset(Dataset):

    def __init__(self, sentence_embedding_file, image_ids_file, image_dir, dataset_type="flickr8k"):
        self.sentence_embedding_file = sentence_embedding_file
        self.image_ids_file = image_ids_file
        self.image_dir = image_dir
        self.sentence_embeddings = None
        self.image_ids = None
        self.images = None
        self.dataset_type = dataset_type

    def __len__(self):
        sentence_embeddings = h5py.File(self.sentence_embedding_file, 'r')
        # load the sentence embeddings ;size: n * 6000
        self.sentence_embeddings = sentence_embeddings['vectors_']
        length = self.sentence_embeddings.shape[0]
        print(length)
        return length

    def __getitem__(self, idx):
        if self.sentence_embeddings is None:
            sentence_embeddings = h5py.File(self.sentence_embedding_file, 'r')
            # load the sentence embeddings ;size: n * 6000
            self.sentence_embeddings = np.asarray(sentence_embeddings['vectors_'])

        if self.image_ids is None:
            image_ids = []
            image_ids_h5py = h5py.File(self.image_ids_file, 'r')
            hdf5_objects = image_ids_h5py['image_ids']
            length = hdf5_objects.shape[1]
            for i in range(length):
                image_ids.append(''.join([chr(v[0]) for v in image_ids_h5py[hdf5_objects[0][i]].value]))
            # image ids (n * 1)
            self.image_ids = image_ids

        # find all images for train
        # self.find_all_images()

        sentence_embedding = self.sentence_embeddings[idx]
        right_image = self.find_right_image(idx)
        right_image = np.array(right_image, dtype=float)
        wrong_image = self.find_wrong_image(idx)
        wrong_image = np.array(wrong_image, dtype=float)

        right_image = self.validate_image(right_image)
        wrong_image = self.validate_image(wrong_image)

        sample = {
            'sentence_embedding': torch.FloatTensor(sentence_embedding),
            'right_image': torch.FloatTensor(right_image),
            # sample a wrong image from images
            'wrong_image': torch.FloatTensor(wrong_image),
        }

        return sample

    def find_wrong_image(self, idx):
        new_idx = random.randint(0, self.sentence_embeddings.shape[0]-1)
        while abs(new_idx - idx) < 10:
            new_idx = random.randint(0, self.sentence_embeddings.shape[0]-1)

        return self.find_image(self.image_ids[new_idx])

    def find_right_image(self, idx):
        return self.find_image(self.image_ids[idx])

    def find_image(self, image_id):
        if self.dataset_type == 'flickr8k':
            return self.find_flickr8k_image(image_id)
        elif self.dataset_type == 'flickr30k':
            return self.find_all_flickr30k_images(image_id)
        elif self.dataset_type == 'mscoco':
            return self.find_all_mscoco_images(image_id)
        else:
            raise Exception("the dataset %s does no been provided! please make sure arguments", self.dataset_type)

    def find_all_images(self):
        if self.dataset_type == 'flickr8k':
            self.find_all_flickr8k_images()
        elif self.dataset_type == 'flickr30k':
            self.find_all_flickr30k_images()
        elif self.dataset_type == 'mscoco':
            self.find_all_mscoco_images()
        else:
            print("the dataset %s does no been provided! please make sure arguments", self.dataset_type)
            exit()

    def find_flickr8k_image(self, image_id):
        image_path = os.path.join(self.image_dir, image_id)
        image = Image.open(image_path).resize((64, 64))
        image.save('tmp.jpg', 'jpeg')
        return image


    def validate_image(self, img):
        # img = np.array(img, dtype=float)
        # if len(img.shape) < 3:
        #     rgb = np.empty((64, 64, 3), dtype=np.float32)
        #     rgb[:, :, 0] = img
        #     rgb[:, :, 1] = img
        #     rgb[:, :, 2] = img
        #     img = rgb
        #
        # return img.transpose(2, 0, 1)
        return img


