#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 25 19:26:12 2018

@author: shuvrajit
"""

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import numpy as np
#from scipy.misc import imsave
import os
import shutil
#from PIL import Image
import time
import random
import sys
import mlflow
import mlflow.tensorflow
from layers import *
from model import *
import cv2
import sys
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

img_height = 256
img_width = 256
img_layer = 3

img_size = img_height * img_width

to_train = False
to_test = True
to_restore = False
output_path = "/home/tjc105u/桌面/project/PairedCycleGAN-tf/output"
check_dir = "/home/tjc105u/桌面/project/PairedCycleGAN-tf/output/checkpoints/"

ref_dir = "/home/tjc105u/桌面/project/PairedCycleGAN-tf/data/web_ref"
src_dir = "/home/tjc105u/桌面/project/PairedCycleGAN-tf/data/web_src"
AUTOTUNE = tf.data.experimental.AUTOTUNE

temp_check = 0



EPOCHS = 60
max_images = 1

h1_size = 150
h2_size = 300
z_size = 100
batch_size = 1
pool_size = 60
sample_size = 10
save_training_images = True
ngf = 32
ndf = 64

tf.reset_default_graph()


def preprocess_image(image):
  image = tf.image.decode_jpeg(image, channels=3)
  image = tf.image.resize(image, [192, 192])
  image /= 255.0  # normalize to [0,1] range

  return image

def load_and_preprocess_image(path):
  image = tf.read_file(path)
  return preprocess_image(image)

class CycleGAN():



    def input_setup(self):

        ''' 
        This function basically setup variables for taking image input.

        filenames_A/filenames_B -> takes the list of all training images
        self.image_A/self.image_B -> Input image with each values ranging from [-1,1]
        '''

        filenames_ref = [os.path.join(ref_dir, f) for f in os.listdir(ref_dir)]      
        filenames_src = [os.path.join(src_dir, f) for f in os.listdir(src_dir)]
        self.ref_length_n = tf.size(filenames_ref)
        self.src_length_n = tf.size(filenames_src)
        

        self.ref_path_ds = tf.data.Dataset.from_tensor_slices(filenames_ref)
        self.src_path_ds = tf.data.Dataset.from_tensor_slices(filenames_src)

#        self.ref_image_ds = ref_path_ds.map(load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
#        self.src_image_ds = src_path_ds.map(load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
        
        
        

    def input_read(self, sess):

        # Loading images into the tensors
        

        num_files_A = sess.run(self.ref_length_n)
        num_files_B = sess.run(self.src_length_n)

        self.fake_images_A = np.zeros((pool_size,1,img_height, img_width, img_layer))
        self.fake_images_B = np.zeros((pool_size,1,img_height, img_width, img_layer))


        self.A_input = np.zeros((max_images, batch_size, img_height, img_width, img_layer))
        self.B_input = np.zeros((max_images, batch_size, img_height, img_width, img_layer))
        
        iterator_ref = self.ref_path_ds.make_one_shot_iterator()
        next_element_ref = iterator_ref.get_next()
    
        iterator_src = self.src_path_ds.make_one_shot_iterator()
        next_element_src = iterator_src.get_next()

        for i in range(max_images):
            path = sess.run(next_element_ref)
            image_tensor = tf.read_file(path)
            image_tensor = tf.image.decode_jpeg(image_tensor, channels=3)
            image_tensor = tf.image.resize(image_tensor, [256, 256])
            image_tensor /= 255.0
            image_tensor = sess.run(image_tensor)
            #print("image_tensor", image_tensor.size)
            #if(image_tensor.size() == img_size*batch_size*img_layer):
#            if(image_tensor.size == img_size*batch_size*img_layer):
            self.A_input[i] = image_tensor.reshape((batch_size,img_height, img_width, img_layer))

        for i in range(max_images):
            path = sess.run(next_element_src)
            image_tensor = tf.read_file(path)
            image_tensor = tf.image.decode_jpeg(image_tensor, channels=3)
            image_tensor = tf.image.resize(image_tensor, [256, 256])
            image_tensor /= 255.0
            image_tensor = sess.run(image_tensor)
            #if(image_tensor.size() == img_size*batch_size*img_layer):
#            if(image_tensor.size == img_size*batch_size*img_layer):
            self.B_input[i] = image_tensor.reshape((batch_size,img_height, img_width, img_layer))




    def model_setup(self):

        ''' This function sets up the model to train

        self.input_A/self.input_B -> Set of training images.
        self.fake_A/self.fake_B -> Generated images by corresponding generator of input_A and input_B
        self.lr -> Learning rate variable
        self.cyc_A/ self.cyc_B -> Images generated after feeding self.fake_A/self.fake_B to corresponding generator. This is use to calcualte cyclic loss
        '''

        self.input_A = tf.placeholder(tf.float32, [batch_size, img_width, img_height, img_layer], name="input_A")
        self.input_B = tf.placeholder(tf.float32, [batch_size, img_width, img_height, img_layer], name="input_B")
        
        self.fake_pool_A = tf.placeholder(tf.float32, [None, img_width, img_height, img_layer], name="fake_pool_A")
        self.fake_pool_B = tf.placeholder(tf.float32, [None, img_width, img_height, img_layer], name="fake_pool_B")

        self.global_step = tf.Variable(0, name="global_step", trainable=False)

        self.num_fake_inputs = 0

        self.lr = tf.placeholder(tf.float32, shape=[], name="lr")

        with tf.variable_scope("Model") as scope:
            self.fake_B = build_generator_resnet_9blocks(self.input_A, name="g_A")
            self.fake_A = build_generator_resnet_9blocks(self.input_B, name="g_B")
            self.rec_A = build_gen_discriminator(self.input_A, "d_A")
            self.rec_B = build_gen_discriminator(self.input_B, "d_B")

            scope.reuse_variables()

            self.fake_rec_A = build_gen_discriminator(self.fake_A, "d_A")
            self.fake_rec_B = build_gen_discriminator(self.fake_B, "d_B")
            self.cyc_A = build_generator_resnet_9blocks(self.fake_B, "g_B")
            self.cyc_B = build_generator_resnet_9blocks(self.fake_A, "g_A")

            scope.reuse_variables()

            self.fake_pool_rec_A = build_gen_discriminator(self.fake_pool_A, "d_A")
            self.fake_pool_rec_B = build_gen_discriminator(self.fake_pool_B, "d_B")
    def loss_calc(self):

        ''' In this function we are defining the variables for loss calcultions and traning model

        d_loss_A/d_loss_B -> loss for discriminator A/B
        g_loss_A/g_loss_B -> loss for generator A/B
        *_trainer -> Variaous trainer for above loss functions
        *_summ -> Summary variables for above loss functions'''


        cyc_loss = tf.reduce_mean(tf.abs(self.input_A-self.cyc_A)) + tf.reduce_mean(tf.abs(self.input_B-self.cyc_B))
        
        disc_loss_A = tf.reduce_mean(tf.squared_difference(self.fake_rec_A,1))
        disc_loss_B = tf.reduce_mean(tf.squared_difference(self.fake_rec_B,1))
        
        g_loss_A = cyc_loss*10 + disc_loss_B
        g_loss_B = cyc_loss*10 + disc_loss_A

        d_loss_A = (tf.reduce_mean(tf.square(self.fake_pool_rec_A)) + tf.reduce_mean(tf.squared_difference(self.rec_A,1)))/2.0
        d_loss_B = (tf.reduce_mean(tf.square(self.fake_pool_rec_B)) + tf.reduce_mean(tf.squared_difference(self.rec_B,1)))/2.0

        
        optimizer = tf.train.AdamOptimizer(self.lr, beta1=0.5)

        self.model_vars = tf.trainable_variables()

        d_A_vars = [var for var in self.model_vars if 'd_A' in var.name]
        g_A_vars = [var for var in self.model_vars if 'g_A' in var.name]
        d_B_vars = [var for var in self.model_vars if 'd_B' in var.name]
        g_B_vars = [var for var in self.model_vars if 'g_B' in var.name]
        
        
        
        self.d_A_trainer = optimizer.minimize(d_loss_A, var_list=d_A_vars)
        self.d_B_trainer = optimizer.minimize(d_loss_B, var_list=d_B_vars)
        self.g_A_trainer = optimizer.minimize(g_loss_A, var_list=g_A_vars)
        self.g_B_trainer = optimizer.minimize(g_loss_B, var_list=g_B_vars)

        for var in self.model_vars: print(var.name)

        #Summary variables for tensorboard

        self.g_A_loss_summ = tf.summary.scalar("g_A_loss", g_loss_A)
        self.g_B_loss_summ = tf.summary.scalar("g_B_loss", g_loss_B)
        self.d_A_loss_summ = tf.summary.scalar("d_A_loss", d_loss_A)
        self.d_B_loss_summ = tf.summary.scalar("d_B_loss", d_loss_B)

    def save_training_images(self, sess, epoch):

        if not os.path.exists("./output/imgs"):
            os.makedirs("./output/imgs")

        for i in range(0,max_images):
            fake_A_temp, fake_B_temp, cyc_A_temp, cyc_B_temp = sess.run([self.fake_A, self.fake_B, self.cyc_A, self.cyc_B],feed_dict={self.input_A:self.A_input[i], self.input_B:self.B_input[i]})
            
            fake_A_savepath = './output/imgs/fakeA_{}_{}.jpg'.format(epoch, i)
            fake_A_img = (fake_A_temp[0]*255).astype(np.uint8)
            #cv2.cvtColor(fake_A_img, cv2.COLOR_RGB2BGR)
            
            fake_B_savepath = './output/imgs/fakeB_{}_{}.jpg'.format(epoch, i)
            fake_B_img = (fake_B_temp[0]*255).astype(np.uint8)
            #cv2.cvtColor(fake_B_img, cv2.COLOR_RGB2BGR)
           
            cyc_A_savepath = './output/imgs/cycA_{}_{}.jpg'.format(epoch, i)
            cyc_A_img = (cyc_A_temp[0]*255).astype(np.uint8)
            #cv2.cvtColor(cyc_A_img, cv2.COLOR_RGB2BGR)
            
            cyc_B_savepath = './output/imgs/cycB_{}_{}.jpg'.format(epoch, i)
            cyc_B_img = (cyc_B_temp[0]*255).astype(np.uint8)
            #cv2.cvtColor(cyc_B_img, cv2.COLOR_RGB2BGR)

            input_A_savepath = './output/imgs/inputA_{}_{}.jpg'.format(epoch, i)
            input_A_img = (self.A_input[i][0]*255).astype(np.uint8)
            #cv2.cvtColor(input_A_img, cv2.COLOR_RGB2BGR)
           
            input_B_savepath = './output/imgs/inputB_{}_{}.jpg'.format(epoch, i)
            input_B_img = (self.B_input[i][0]*255).astype(np.uint8)
            #cv2.cvtColor(input_B_img, cv2.COLOR_RGB2BGR)

            cv2.imwrite(fake_A_savepath, fake_A_img)
            cv2.imwrite(fake_B_savepath, fake_B_img)
            cv2.imwrite(cyc_A_savepath, cyc_A_img)
            cv2.imwrite(cyc_B_savepath, cyc_B_img)
            cv2.imwrite(input_A_savepath, input_A_img)
            cv2.imwrite(input_B_savepath, input_B_img)

            
    def fake_image_pool(self, num_fakes, fake, fake_pool):
        ''' This function saves the generated image to corresponding pool of images.
        In starting. It keeps on feeling the pool till it is full and then randomly selects an
        already stored image and replace it with new one.'''

        if(num_fakes < pool_size):
            fake_pool[num_fakes] = fake
            return fake
        else :
            p = random.random()
            if p > 0.5:
                random_id = random.randint(0,pool_size-1)
                temp = fake_pool[random_id]
                fake_pool[random_id] = fake
                return temp
            else :
                return fake


    def train(self):


        ''' Training Function '''


        # Load Dataset from the dataset folder
        self.input_setup()  
        #Build the network
        self.model_setup()
        #Loss function calculations
        self.loss_calc()
        # Initializing the global variables
        saver = tf.train.Saver()
        init = [tf.global_variables_initializer(), tf.local_variables_initializer()]
        with tf.Session() as sess:
            sess.run(init)

            #Read input to nd array
            self.input_read(sess)

            #Restore the model to run the model from last checkpoint
            if to_restore:
                chkpt_fname = tf.train.latest_checkpoint(check_dir)
                saver.restore(sess, chkpt_fname)

            writer = tf.summary.FileWriter("./output/2")

            if not os.path.exists(check_dir):
                os.makedirs(check_dir)

# Training Loop
            for epoch in range(sess.run(self.global_step), EPOCHS):                
                print ("In the epoch ", epoch)
                saver.save(sess,os.path.join(check_dir,"cyclegan"),global_step=epoch)

                # Dealing with the learning rate as per the epoch number
                if(epoch < 40) :
                    curr_lr = 0.0002
                else:
                    curr_lr = 0.0002 - 0.0002*(epoch-100)/100

                if(save_training_images):
                    self.save_training_images(sess, epoch)

                # sys.exit()

                for ptr in range(0,max_images):
                    print("In the iteration ",ptr)
                    print("Starting",time.time()*1000.0)

                    # Optimizing the G_A network

                    _, fake_B_temp, summary_str = sess.run([self.g_A_trainer, self.fake_B, self.g_A_loss_summ],feed_dict={self.input_A:self.A_input[ptr], self.input_B:self.B_input[ptr], self.lr:curr_lr})
                    
                    writer.add_summary(summary_str, epoch*max_images + ptr)                    
                    fake_B_temp1 = self.fake_image_pool(self.num_fake_inputs, fake_B_temp, self.fake_images_B)
                    
                    # Optimizing the D_B network
                    _, summary_str = sess.run([self.d_B_trainer, self.d_B_loss_summ],feed_dict={self.input_A:self.A_input[ptr], self.input_B:self.B_input[ptr], self.lr:curr_lr, self.fake_pool_B:fake_B_temp1})
                    writer.add_summary(summary_str, epoch*max_images + ptr)
                    
                    
                    # Optimizing the G_B network
                    _, fake_A_temp, summary_str = sess.run([self.g_B_trainer, self.fake_A, self.g_B_loss_summ],feed_dict={self.input_A:self.A_input[ptr], self.input_B:self.B_input[ptr], self.lr:curr_lr})

                    writer.add_summary(summary_str, epoch*max_images + ptr)
                    
                    
                    fake_A_temp1 = self.fake_image_pool(self.num_fake_inputs, fake_A_temp, self.fake_images_A)

                    # Optimizing the D_A network
                    _, summary_str = sess.run([self.d_A_trainer, self.d_A_loss_summ],feed_dict={self.input_A:self.A_input[ptr], self.input_B:self.B_input[ptr], self.lr:curr_lr, self.fake_pool_A:fake_A_temp1})

                    writer.add_summary(summary_str, epoch*max_images + ptr)
                    
                    self.num_fake_inputs+=1
            
                        

                sess.run(tf.assign(self.global_step, epoch + 1))

            writer.add_graph(sess.graph)
    '''
    def test(self):


        # Testing Function

        print("Testing the results")

        self.input_setup()

        self.model_setup()
        saver = tf.train.Saver()
        init = tf.global_variables_initializer()

        with tf.Session() as sess:

            sess.run(init)

            self.input_read(sess)

            chkpt_fname = tf.train.latest_checkpoint(check_dir)
            saver.restore(sess, chkpt_fname)

            if not os.path.exists("./output/imgs/test/"):
                os.makedirs("./output/imgs/test/")            

            for i in range(0,100):
                fake_A_temp, fake_B_temp = sess.run([self.fake_A, self.fake_B],feed_dict={self.input_A:self.A_input[i], self.input_B:self.B_input[i]})
                imsave("./output/imgs/test/fakeB_"+str(i)+".jpg",((fake_A_temp[0]+1)*127.5).astype(np.uint8))
                imsave("./output/imgs/test/fakeA_"+str(i)+".jpg",((fake_B_temp[0]+1)*127.5).astype(np.uint8))
                imsave("./output/imgs/test/inputA_"+str(i)+".jpg",((self.A_input[i][0]+1)*127.5).astype(np.uint8))
                imsave("./output/imgs/test/inputB_"+str(i)+".jpg",((self.B_input[i][0]+1)*127.5).astype(np.uint8))
    '''
    def test(self):



        print("Testing the results")

        self.input_setup()

        self.model_setup()
        saver = tf.train.Saver()
        init = tf.global_variables_initializer()

        with tf.Session() as sess:

            sess.run(init)

            self.input_read(sess)

            chkpt_fname = tf.train.latest_checkpoint(check_dir)
            saver.restore(sess, chkpt_fname)

            if not os.path.exists("./output/test/"):
                os.makedirs("./output/test/")            

            for i in range(0,max_images):
                fake_A_temp, fake_B_temp = sess.run([self.fake_A, self.fake_B],feed_dict={self.input_A:self.A_input[i], self.input_B:self.B_input[i]})
                epoch = 1
                
                fake_A_savepath = './output/test/fakeA_{}_{}.jpg'.format(epoch, i)
                fake_A_img = (fake_A_temp[0]*255).astype(np.uint8)
                fake_A_img = cv2.cvtColor(fake_A_img, cv2.COLOR_RGB2BGR)

                fake_B_savepath = './output/test/fakeB_{}_{}.jpg'.format(epoch, i)
                fake_B_img = (fake_B_temp[0]*255).astype(np.uint8)
                fake_B_img = cv2.cvtColor(fake_B_img, cv2.COLOR_RGB2BGR)
                
                input_A_savepath = './output/test/inputA_{}_{}.jpg'.format(epoch, i)
                input_A_img = (self.A_input[i][0]*255).astype(np.uint8)
                input_A_img = cv2.cvtColor(input_A_img, cv2.COLOR_RGB2BGR)

                input_B_savepath = './output/test/inputB_{}_{}.jpg'.format(epoch, i)
                input_B_img = (self.B_input[i][0]*255).astype(np.uint8)
                input_B_img = cv2.cvtColor(input_B_img, cv2.COLOR_RGB2BGR)
                
                cv2.imwrite(fake_A_savepath, fake_A_img)
                cv2.imwrite(fake_B_savepath, fake_B_img)
                cv2.imwrite(input_A_savepath, input_A_img)
                cv2.imwrite(input_B_savepath, input_B_img)
              

def main():
    
    model = CycleGAN()
    if to_train:
        model.train()
    if to_test:
        model.test()



if __name__ == '__main__':

    main()




