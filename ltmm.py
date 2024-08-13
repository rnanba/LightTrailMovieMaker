#!/usr/bin/env python
import sys
import glob
import os.path
import platform
import math
import numpy as np
import argparse
import av
import cv2
from PIL import Image, ImageDraw, ImageFont

#import logging
#logging.basicConfig()
#av.logging.set_level(logging.DEBUG)

FONTS = {
    "Linux": "Courier_New.ttf",
    "Windows": "cour.ttf",
    "Darwin": "Courier.ttc"
}
TEXT_ANCHORS = {
    "top-left": "la",
    "top-middle": "ma",
    "top-right": "ra",
    "bottom-left": "ld",
    "bottom-middle": "md",
    "bottom-right": "rd"
}
IMAGE_FORMAT_EXT_LIST = [ ".jpg", ".jpeg", ".png", ".tif", ".tiff" ]
BAYER_PATTERNS = {
    "RGGB": cv2.COLOR_BAYER_RGGB2RGB,
    "GRBG": cv2.COLOR_BAYER_GRBG2RGB,
    "GBRG": cv2.COLOR_BAYER_GBRG2RGB,
    "BGGR": cv2.COLOR_BAYER_BGGR2RGB
}

def is_image_file(filename):
    lower_name = filename.lower()
    for ext in IMAGE_FORMAT_EXT_LIST:
        if lower_name.endswith(ext):
            return True
    return False

class Frames:
    def __init__(self):
        self.width = None
        self.height = None
        self.index = 0
        self.total = 0
        self.average_rate = None
    
    def __iter__(self):
        return self

    def __next__(self):
        if self.index < self.total:
            np_img = self.get_np_image()
            self.index += 1
            return np_img
        else:
            raise StopIteration()

    def skip(self, n):
        self.index += n
        
    def get_np_image(self):
        return None
    
    def image_width(self):
        return self.width
    
    def image_height(self):
        return self.height

    def frame_index(self):
        return self.index

    def total_count(self):
        return self.total

    def average_rate(self):
        return self.average_rate

    def close(self):
        return None

class MovieFrames(Frames):
    def __init__(self, dir):
        super().__init__()
        self.container_in = av.open(input)
        self.stream_in = self.container_in.streams.video[0]
        self.total = self.stream_in.frames
        self.width = self.stream_in.codec_context.width
        self.height = self.stream_in.codec_context.height
        self.average_rate = self.stream_in.average_rate
        self.frame_iter = self.container_in.decode(video=0)

    def skip(self, n):
        for _ in range(n):
            self.frame_iter.__next__()
            self.index += 1
    
    def get_np_image(self):
        frame = self.frame_iter.__next__()
        return frame.to_ndarray(format="rgb24")

    def close(self):
        return self.container_in.close()

class Photos(Frames):
    def __init__(self, dir):
        super().__init__()
        self.dir = dir
        self.files  = list(filter(is_image_file, os.listdir(dir)))
        self.files.sort()
        img = self.get_np_image()
        self.height, self.width = img.shape
        self.total = len(self.files)

    def get_np_image(self):
        file = os.path.join(self.dir, self.files[self.index])
        return  np.array(Image.open(file))

    def get_filename(self, frame_number):
        return self.files[frame_number-1]

def convert(input, args, font):
    frames = None
    if os.path.isdir(input):
        frames = Photos(input)
    else:
        frames = MovieFrames(input)
        
    name = ""
    if os.path.isdir(input):
        name = os.path.split(os.path.abspath(os.path.join(input, ".")))[-1]
    else:
        name = os.path.splitext(os.path.basename(input))[0]
    
    range_file = ""
    range_display = ""
    if args.start_frame > 1 or args.end_frame is not None:
        range_file = f"-{args.start_frame}_{args.end_frame}"
        if os.path.isdir(input):
            first = os.path.basename(frames.get_filename(args.start_frame))
            last = os.path.basename(frames.get_filename(args.end_frame))
            range_display = f"({first} - {last})"
        else:
            range_display = f"({args.start_frame}:{args.end_frame})"
    output = os.path.join(args.out_dir, f"{name}-max{range_file}{args.out_ext}")
    print(f"{input}{range_display} -> {output}")
    
    WIDTH = frames.image_width()
    HEIGHT = frames.image_height()
    crop_w = 0
    crop_h = 0
    if args.video_codec == "libx264":
        if WIDTH % 2 == 1:
            crop_w = 1
        if HEIGHT % 2 == 1:
            crop_h = 1
    average_rate = args.frame_rate
    if average_rate is None:
        if frames.average_rate is None:
            print("ERROR: Frame rate of input not detected."\
                  " Specify --frame-rate.", file=sys.stderr)
            sys.exit(1)
        average_rate = str(stream_in.average_rate)

    TEXT_POSITIONS = {
        "top-left": (0, 0),
        "top-middle": (WIDTH/2, 0),
        "top-right": (WIDTH-crop_w, 0),
        "bottom-left": (0, HEIGHT-crop_h),
        "bottom-middle": (WIDTH/2, HEIGHT-crop_h),
        "bottom-right": (WIDTH-crop_w, HEIGHT-crop_h)
    }
    if args.text_position not in TEXT_ANCHORS:
        pos_keys = None
        for pos_key in TEXT_ANCHORS.keys():
            if pos_keys is None:
                pos_keys = ""
            else:
                pos_keys += ", "
            pos_keys += f"'{pos_key}'"
        print(f"ERROR: Unknown text position: '{args.text_position}'."\
              f" Specify {pos_keys}.", file=sys.stderr)
        sys.exit(1)
    text_anchor = TEXT_ANCHORS[args.text_position]
    text_pos = TEXT_POSITIONS[args.text_position]

    container_out = av.open(output, mode="w")
    stream_out = container_out.add_stream(args.video_codec, rate=args.frame_rate)
    bit_rate = None
    if args.video_bit_rate.endswith('M'):
        bit_rate = int(float(args.video_bit_rate[0:-1]) * 1000 * 1000)
    else:
        bit_rate = int(float(args.video_bit_rate))
    stream_out.bit_rate = bit_rate
    stream_out.width = WIDTH - crop_w
    stream_out.height = HEIGHT - crop_h
    stream_out.pix_fmt = "yuv420p"
    max_frame_array = None
    
    if args.start_frame > 1:
        frames.skip(args.start_frame - 1)
    
    for frame_array in frames:
        if args.debayer_image is not None:
            frame_array = cv2.cvtColor(frame_array,
                                       BAYER_PATTERNS[args.debayer_image])
        if max_frame_array is None:
            max_frame_array = frame_array
        else:
            max_frame_array = np.maximum(frame_array, max_frame_array)

        out_image = None
        if crop_w > 0 or crop_h > 0:
            out_image = Image.fromarray(max_frame_array[0:HEIGHT-crop_h,
                                                        0:WIDTH-crop_w])
        else:
            out_image = Image.fromarray(max_frame_array)

        draw = ImageDraw.Draw(out_image)
        draw.text(text_pos, f"{frames.frame_index()} / {frames.total_count()}",
                  args.font_color, font=font, anchor=text_anchor)
        out_frame = av.VideoFrame.from_image(out_image)
        for packet in stream_out.encode(out_frame):
            container_out.mux(packet)
        
        if args.end_frame is None:
            continue
        elif frames.frame_index() >= args.end_frame:
            break
        
    for packet in stream_out.encode():
        container_out.mux(packet)
    container_out.close()
    frames.close()

parser = argparse.ArgumentParser(description="Light Trail Movie Maker")
parser.add_argument("input_files_or_dirs", nargs="+",
                    help="Input files for movies, or dirs for images.")
parser.add_argument("--out-dir", default=".",
                    help="Output directory.")
parser.add_argument("--out-ext", default=".mp4",
                    help="Output format extension.")
parser.add_argument("--start-frame", type=int, default=1,
                    help="Start frame count (positive integer).")
parser.add_argument("--end-frame", type=int, default=None,
                    help="Last frame count (positive integer).")
parser.add_argument("--frame-rate", default=None,
                    help="Output frame rate.")
parser.add_argument("--font", default=None,
                    help="Font filename of frame count text.")
parser.add_argument("--font-size", type=int, default=24,
                    help="Font size (pixels) of frame count text.")
parser.add_argument("--font-color", default="#FF8888",
                    help="Font color of frame count text.")
parser.add_argument("--text-position", default="top-left",
                    help="Position of frame count text. The options 'top-left',"\
                    " 'top-middle', 'top-right', 'bottom-left', 'bottom-middle',"\
                    " and 'bottom-right' can be specified.")
parser.add_argument("--video-codec", default="mpeg4",
                    help="Output video codec.")
parser.add_argument("--video-bit-rate", default="12M",
                    help="Output video bit rate(bps)."\
                    " Suffix 'M' can be specified.")
parser.add_argument("--debayer-image", default=None,
                    help="Bayer pattern to debayer input images. The options"\
                    " 'RGGB', 'GRBG', 'GBRG', and 'BGGR' can be specified.")
args = parser.parse_args()

font_file = args.font
if font_file is None:
    if platform.system() not in FONTS:
        print("ERROR: Default font of OS is not detected."\
              " Please specify font filename with --font.",
              file=sys.stderr)
        sys.exit(1)
    font_file = FONTS[platform.system()]
font = ImageFont.truetype(font_file, args.font_size)

if not os.path.exists(args.out_dir):
    os.makedirs(args.out_dir)

for input_pattern in args.input_files_or_dirs:
    for input in glob.glob(input_pattern):
        convert(input, args, font)
