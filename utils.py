import torch
import os
import torch.nn.functional as F
import h5py
from PIL import Image
import numpy as np
import time
from torchvision import models
from gan import Discriminator,Generator


class Utils(object):

    @staticmethod
    def smooth_label(tensor, offset):
        return tensor + offset

    @staticmethod
    def save_checkpoint(netD, netG, dir_path, subdir_path, epoch):
        path = os.path.join(dir_path, subdir_path)
        if not os.path.exists(path):
            os.makedirs(path)

        torch.save(netD.state_dict(), '{0}/disc_{1}.pth'.format(path, epoch))
        torch.save(netG.state_dict(), '{0}/gen_{1}.pth'.format(path, epoch))

    @staticmethod
    def generator_weights_init(m):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            m.weight.data.normal_(0.0, 0.02)
        elif classname.find('BatchNorm') != -1:
            m.weight.data.normal_(1.0, 0.02)
            m.bias.data.fill_(0)
        elif classname.find('Linear') != -1:
            m.weight.data.normal_(0, 0.01)
            m.bias.data.fill_(0)

    @staticmethod
    def discriminator_weights_init(m):
        classname = m.__class__.__name__
        if classname.find('BatchNorm') != -1:
            m.weight.data.normal_(1.0, 0.02)
            m.bias.data.fill_(0)
        elif classname.find('Linear') != -1:
            m.weight.data.normal_(0, 0.01)
            m.bias.data.fill_(0)

    @staticmethod
    def cosine_similarity(x1, x2, dim=1, eps=1e-8):
        r"""Returns cosine similarity between x1 and x2, computed along dim.

        .. math ::
            \text{similarity} = \dfrac{x_1 \cdot x_2}{\max(\Vert x_1 \Vert _2 \cdot \Vert x_2 \Vert _2, \epsilon)}

        Args:
            x1 (Tensor): First input.
            x2 (Tensor): Second input (of size matching x1).
            dim (int, optional): Dimension of vectors. Default: 1
            eps (float, optional): Small value to avoid division by zero.
                Default: 1e-8

        Shape:
            - Input: :math:`(\ast_1, D, \ast_2)` where D is at position `dim`.
            - Output: :math:`(\ast_1, \ast_2)` where 1 is at position `dim`.

        Example::
            >>> input1 = torch.randn(100, 128)
            >>> input2 = torch.randn(100, 128)
            >>> output = F.cosine_similarity(input1, input2)
            >>> print(output)
        """
        w12 = torch.sum(x1 * x2, dim)
        w1 = torch.norm(x1, 2, dim)
        w2 = torch.norm(x2, 2, dim)
        return w12 / (w1 * w2).clamp(min=eps)

    @staticmethod
    def distance(w1, w2):
        p_w1 = F.pairwise_distance(w1, torch.zeros(w1.size()).cuda())
        p_w2 = F.pairwise_distance(w2, torch.zeros(w2.size()).cuda())
        p_w1_w2 = F.pairwise_distance(w1, w2)
        return p_w1_w2 / (p_w1 * p_w2)

    @staticmethod
    def save_checkpoint(netD, netG, dir_path, subdir_path, postfix):
        path = os.path.join(dir_path, subdir_path)
        if not os.path.exists(path):
            os.makedirs(path)

        torch.save(netD.state_dict(), '{0}/disc_{1}.pth'.format(path, postfix))
        torch.save(netG.state_dict(), '{0}/gen_{1}.pth'.format(path, postfix))

    @staticmethod
    def load_data(image_ids_file, sentence_embedding_file, image_dir):
        # load sentence
        sentence_embeddings = h5py.File(sentence_embedding_file, 'r')
        #
        sentence_embeddings = np.asarray(sentence_embeddings['val_vectors_'])

        # load image ids
        # image ids (n * 1)
        image_ids = []
        image_ids_h5py = h5py.File(image_ids_file, 'r')
        hdf5_objects = image_ids_h5py['val_image_ids']
        length = hdf5_objects.shape[1]
        for i in range(length):
            image_ids.append(''.join([chr(v[0]) for v in image_ids_h5py[hdf5_objects[0][i]].value]))

        images = []
        for i in range(length):
            image_path = os.path.join(image_dir, image_ids[i])
            image = Image.open(image_path).resize((224, 224))
            image = np.array(image, dtype=float)
            image = image.transpose(2, 0, 1)
            images.append(image)
        images = np.array(images, dtype=float)

        return torch.FloatTensor(images), torch.FloatTensor(sentence_embeddings)

    @staticmethod
    def save_results(results, np_path, txt_path):
        # save results

        if os.path.exists(np_path):
            os.remove(np_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)

        np.save(np_path, results)
        np.savetxt(txt_path, results)

    @staticmethod
    def save_image(PILImage, image_directory):
        image_name = str(int(time.time() % (10 ** 5))) + ".jpg"
        PILImage.save(os.path.join(image_directory, image_name))

    @staticmethod
    def save_images(PILImages, image_directory):
        '''
        :param PILImages: tuple or list of PIL image
        :param image_directory: save path
        :return:
        '''
        for PILImage in PILImages:
            image_name = str(int(time.time() % (10 ** 5))) + ".jpg"
            PILImage.save(os.path.join(image_directory, image_name))

    @staticmethod
    def load_validate_data(data_path):
        # load validate data
        val_data_path = os.path.join(data_path, "val")
        val_sentence_embedding_file = os.path.join(val_data_path, "val_vectors_.mat")
        val_image_ids_file = os.path.join(val_data_path, "val_image_ids.mat")
        image_dir = os.path.join(data_path, "images")
        image_tensors, sentence_embedding_tensors = Utils.load_data(val_image_ids_file, val_sentence_embedding_file,
                                                                    image_dir)
        return image_tensors, sentence_embedding_tensors

    @staticmethod
    def extract_image_feature(images):
        pretrained_model = models.vgg16(pretrained=True).features
        image_features = pretrained_model(images)
        image_features = image_features.view(image_features.size(0), 512 * 7 * 7)
        return image_features

    @staticmethod
    def load_generator(generator_model_path):
        # load generator model
        generator = Generator()
        generator = torch.nn.DataParallel(generator.cuda())
        generator.load_state_dict(torch.load(generator_model_path))

        return generator

    @staticmethod
    def load_discriminator(discriminator_model_path):
        # load discriminator model
        discriminator = Discriminator()
        discriminator = torch.nn.DataParallel(discriminator.cuda())
        discriminator.load_state_dict(torch.load(discriminator_model_path))
        return discriminator



