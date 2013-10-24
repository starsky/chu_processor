'''
Created on May 3, 2013

@author: mkopersk
'''
import os
import sys
import inspect
import subprocess


class VideoWriter(object):

    def __init__(self,output_file):
        self.output = output_file + '.mp4'
        if os.environ.has_key('FFMPEG_BIN'):
            bin_path = os.environ['FFMPEG_BIN']
        else:
            bin_path = 'ffmpeg'
        CMD = (bin_path, '-f', 'image2pipe', '-r', '8', '-vcodec', 'png', '-i', '-', '-r', '8', '-c:v', 'libx264', self.output)
        self.p = subprocess.Popen(CMD, stdin=subprocess.PIPE)
        
    def write(self,img):
        img.save(self.p.stdin,format='png')

    def finish(self):
        self.p.terminate()


#class ScreenWriter(object):
#    def write(self,img,name):
#        img.show()
#
#
#class ImageWriter(object):
#
#    def __init__(self,args):
#        self.output = args.image_output
#
#    def write(self,img,name):
#        url = os.path.join(self.output,name + '.png')
#        img.save(url)
#
#    ARGS_DEF = [('-io', '--image-output', 'image_output', 'Place to save frames.')]


#class WriterComposite(object):
#    WRITERS = {'image_output' : ImageWriter, 'video_output' : VideoWriter}
#    def __init__(self,args):
#        self.writers = []
#        for k in self.WRITERS:
#            if args.__getattribute__(k) is not None:
#                self.writers.append(self.WRITERS[k](args))
#        if len(self.writers) == 0 and args.__getattribute__('frame_dir') is not None:
#            self.writers.append(ScreenWriter())
#
#    def write(self,img,name):
#        for w in self.writers:
#            w.write(img,name)
