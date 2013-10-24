'''
Created on Apr 25, 2013

@author: mkopersk
'''
import urllib2
from xml.dom.minidom import parseString, Node
import os
import Image, ImageDraw
import struct
import numpy
import logging
import re

def __put_alpha__(img,alpha):
    mask=Image.new('L', img.size, color=255)
    draw=ImageDraw.Draw(mask) 
    transparent_area = (0,0,img.size[0],img.size[1])
    draw.rectangle(transparent_area, fill=int(alpha * 255))
    img.putalpha(mask)


class SkeletonReader(object):

    class Skeleton(object):
        JOINT_IDS = {
        'HEAD' : 0,
        'NECK' : 1,
        'TORSO' : 2,
        'WAIST' : 3,
        'LEFT_COLLAR' : 4,
        'LEFT_SHOULDER': 5,
        'LEFT_ELBOW': 6,
        'LEFT_WRIST': 7,
        'LEFT_HAND': 8,
        'LEFT_FINGERTIP': 9,
        'RIGHT_COLLAR': 10,
        'RIGHT_SHOULDER': 11,
        'RIGHT_ELBOW': 12,
        'RIGHT_WRIST': 13,
        'RIGHT_HAND': 14,
        'RIGHT_FINGERTIP': 15,
        'LEFT_HIP': 16,
        'LEFT_KNEE': 17,
        'LEFT_ANKLE': 18,
        'LEFT_FOOT': 19,
        'RIGHT_HIP': 20,
        'RIGHT_KNEE': 21,
        'RIGHT_ANKLE': 22,
        'RIGHT_FOOT': 23
        }

        def __init__(self, points_list):
            self.points_list = points_list

        def get_coords(self,joint_id):
            return self.points_list[joint_id]


    def __read_from_url__(self,url):
        url = os.path.join(url,'raw','skeleton.xml')
        #skeleton_file = urllib2.urlopen('file://' + url)
        skeleton_file = open(url,'r')
        return skeleton_file.read()

    
    def read_skeleton(self, frame_folder):
        xml_string = self.__read_from_url__(frame_folder)
        doc = parseString(xml_string)
        joints_list = [None] * len(self.Skeleton.JOINT_IDS)
        joints = doc.getElementsByTagName('JOINTS')
        for joint in list(joints[0].childNodes):
            if joint.nodeType == Node.ELEMENT_NODE:
                joints_list[self.Skeleton.JOINT_IDS[joint.nodeName]] = self.__read_joint_node__(joint)
        return self.Skeleton(joints_list)
    
    def __read_joint_node__(self,joint):
        coord_3d_node = joint.getElementsByTagName('COORD_3D')[0]
        tuple_3d = (float(coord_3d_node.getAttribute('x')), float(coord_3d_node.getAttribute('y')), float(coord_3d_node.getAttribute('z')))
        coord_2d_node = joint.getElementsByTagName('COORD_2D')[0]
        tuple_2d = (float(coord_2d_node.getAttribute('x')), float(coord_2d_node.getAttribute('y')))
        if tuple_2d[0] < 0 or tuple_2d[1] < 0:
            return None
        else:
            return {'coord_3d' : tuple_3d, 'coord_2d': tuple_2d}

    def create_img(self, image, frame_folder):
        try:
            RADUIS = 3
            skeleton = self.read_skeleton(frame_folder)
            draw = ImageDraw.Draw(image)
            for joint_id in self.Skeleton.JOINT_IDS.values():
                joint = skeleton.get_coords(joint_id)
                if joint is None:
                    continue
                coord_2d = joint['coord_2d']
                bbox = (coord_2d[0] - RADUIS, coord_2d[1] - RADUIS, coord_2d[0] + RADUIS, coord_2d[1] + RADUIS)
                draw.ellipse(bbox, fill=128)
            del draw
        except IOError :
            logging.info('[Missing Skeleton File]\t%s' % frame_folder)
        return  image


class RgbReader(object):
    def __init__(self):
        self.alpha = 1
        None
    
    def __read_from_url__(self,url):
        frame_folder = url
        url = os.path.join(url,'raw')
        rgb_files = [os.path.join(url,each) for each in os.listdir(url) if each.startswith('color')]
        if len(rgb_files) == 0:
            raise IOError()
        elif len(rgb_files) > 1:
            logging.info('[More than one RGB file]\t%s' % frame_folder)
        url = rgb_files[0]
        return Image.open(url)
       
    def create_img(self, image, frame_folder):
        try:
            if image is None:
                return self.__read_from_url__(frame_folder);
            else:
                foreground = self.__read_from_url__(frame_folder)
                foreground = foreground.convert('RGBA')          
                __put_alpha__(foreground, self.alpha)
                image.paste(foreground, (0, 0), foreground)
        except IOError :
            logging.info('[Missing RGB File]\t%s' % frame_folder)
        return image    

class DepthReader(object):
    
    QINT32 = { 'size' : 4}
    
    def __init__(self):
        self.alpha = 1
        None
    
    def __read_from_url__(self,url):
        url = os.path.join(url,'raw','depth.raw')
        input_file = None
        try:
            input_file = open(url, "rb")
            rows = struct.unpack("<i",input_file.read(self.QINT32['size']))[0]
            cols = struct.unpack("<i",input_file.read(self.QINT32['size']))[0]
            arr = numpy.empty((rows*cols))
            for i in range(0, rows*cols):
                arr[i] = (struct.unpack("f",input_file.read(self.QINT32['size']))[0])
        finally:
            if input_file is not None:
                input_file.close()

        return ((cols,rows),arr)
       
    def create_img(self, image, frame_folder):
        try:
            (size,arr) = self.__read_from_url__(frame_folder)
            im = Image.new('RGB',size)
            digit_mat = [int(a * 1000) for a in arr]
            max_val = max(digit_mat)
            min_val = min(digit_mat)
#            digit_mat = [a - 2000 if a - 2000 >= 0 else 0 for a in digit_mat]
#            digit_mat = [a * scale_factor for a in digit_mat]
            digit_color_mat = [self.__pseudocolor__(a, min_val, max_val) for a in digit_mat]
            im.putdata(digit_color_mat)
            if image is None:
                return im.convert('RGB')
        except IOError as e:
            if e.errno == 2:
                logging.info('[Missing Depth File]\t%s' % frame_folder)
            else:
                raise e
        return image
    
    def __pseudocolor__(self,val, minval, maxval):
        # convert val in range minval...maxval to range 0..1
        f = float(val-minval) / (maxval-minval)
        # linearly interpolate that value between the colors red and green
        r, g, b = 1-f, f, 0.
        return (int(r * 255), int(g * 255), int(b * 255))
    
    ARGS_DEF = [('-D', '--depth', 'depth', 'Indicates to use depth map. You can set alpha.')]

class Chain(object):
    READERS = {'depth' : DepthReader, 'image' : RgbReader, 'skeleton' : SkeletonReader}
    def __init__(self,readers):
        self.processors = [r() for r in readers]

    def process(self,frame_folder):
        img = None
        for processor in self.processors:
            img = processor.create_img(img,frame_folder)
        return img
           
    
class FramesHelper(object):

    def __init__(self, video_folder):
        self.frames_folders = [f for f in map(lambda x: os.path.join(video_folder,x),os.listdir(video_folder)) if os.path.isdir(f)]
        self.frames_folders = sorted(self.frames_folders)

    def __iter__(self):
        return iter(self.frames_folders)

    def __len__(self):
        return len(self.frames_folders)

    def __check_missing_frames__(self):
        pattern = re.compile(r'^.*view(\d+)/*$')
        last_frame = None
        for f in self.frames_folders:
            no = int(pattern.search(f).groups()[0])
            if last_frame is None:
                last_frame = no
                continue
            if no - last_frame != 1:
                logging.info('[Missing frames]\t%s' % f)
            last_frame = no