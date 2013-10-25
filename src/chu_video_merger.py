'''
Created on May 3, 2013

@author: mkopersk
'''
import sys
import os
import argparse
from ncu.reader import Chain
from ncu.reader import FramesHelper
from ncu.writer import VideoWriter
import logging

def main(argv=None):
    try:
        logging.basicConfig(filename="chu.log", level=logging.INFO)
        parser = argparse.ArgumentParser()
        parser.add_argument("folder",
                            help="Folder with frames to process")

        #parser.add_argument("-r", "--rgb", action="store_true",
        #                    help="Add rgb image to output.")
        #parser.add_argument("-d", "--depth", action="store_true",
        #                    help="Add depth map to output.")
        #parser.add_argument("-s", "--skeleton", action="store_true",
        #                    help="Add skeleton to output.")
        #parser.add_argument('-e','--eee',choices=[ i for sublist in map(lambda x: ["".join(l) for l in list(itertools.permutations(x))],['rsd','rs','rd','r','s','d']) for i in sublist],default='rg')

        parser.add_argument("-q", "--quiet", action="store_true",
                            help="Do not print messages.")

        args = parser.parse_args()

        chain = Chain([Chain.READERS['image'],Chain.READERS['skeleton']])

        if args.folder is not '-':
            video_folders = [os.path.normpath(args.folder)]
        else:
            video_folders = [os.path.normpath(l.replace('\n','')) for l in sys.stdin]

        for i, video_folder in enumerate(video_folders):
            frame_folders = FramesHelper(video_folder)
            writer = VideoWriter(str(i))
            for frame_folder in frame_folders:
                #print frame_folder
                if not os.path.exists(os.path.join(frame_folder,'raw','skeleton.xml')):
                    logging.info('[Missing Skeleton File]\t%s' % frame_folder)
                    continue
                img = chain.process(frame_folder)
                writer.write(img)
            writer.finish()

        return

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        None

if __name__ == "__main__":
    sys.exit(main())