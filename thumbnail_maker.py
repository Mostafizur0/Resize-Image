import logging
import multiprocessing
import os.path
import time
from queue import Queue
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlretrieve

import PIL
from PIL import Image

FORMAT = "[%(threadName)s, %(asctime)s, %(levelname)s] %(message)s"
logging.basicConfig(filename='logfile.log', format=FORMAT,
                    level=logging.DEBUG, handlers=[logging.StreamHandler()])


class ThumbnailMakerService(object):
    def __init__(self, home_dir='.'):
        self.home_dir = home_dir
        self.input_dir = self.home_dir + os.path.sep + 'incoming'
        self.output_dir = self.home_dir + os.path.sep + 'outgoing'
        self.img_list = []

    def download_image(self, dl_queue):
        while not dl_queue.empty():
            try:
                url = dl_queue.get(block=False)
                img_file_name = urlparse(url).path.split('/')[-1]
                urlretrieve(url, self.input_dir + os.path.sep + img_file_name)
                self.img_list.append(img_file_name)

                dl_queue.task_done()
            except Queue.Empty:
                logging.info("Queue empty")

    def download_images(self, img_url_list):
        # validate inputs
        if not img_url_list:
            return
        os.makedirs(self.input_dir, exist_ok=True)
        logging.info("beginning image download")

        start = time.perf_counter()
        # download each image and save to the input dir
        #for url in img_url_list:
            # img_file_name = urlparse(url).path.split('/')[-1]
            # urlretrieve(url, self.input_dir + os.path.sep + img_file_name)
            # self.img_queue.put(img_file_name)
        end = time.perf_counter()
        self.img_queue.put(None)

        logging.info("downloaded {} images in {} seconds".format(len(img_url_list), end - start))

    def perform_resizing(self):
        os.makedirs(self.output_dir, exist_ok=True)

        logging.info("beginning image resizing")
        target_sizes = [32, 64, 200]
        num_images = len(os.listdir(self.input_dir))

        start = time.perf_counter()
        while True:
            filename = self.img_queue.get()
            if filename:
                logging.info("resizing image {}".format(filename))
                orig_img = Image.open(self.input_dir + os.path.sep + filename)
                for baseWidth in target_sizes:
                    img = orig_img
                    # calculate target height of the resized image to maintain the aspect ratio
                    wpercent = (baseWidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    # perform resizing
                    img = img.resize((baseWidth, hsize), PIL.Image.LANCZOS)

                    # save the resized image to the output dir with a modified file name
                    new_filename = os.path.splitext(filename)[0] + \
                                   '_' + str(baseWidth) + os.path.splitext(filename)[1]
                    img.save(self.output_dir + os.path.sep + new_filename)

                os.remove(self.input_dir + os.path.sep + filename)
                logging.info("done resizing image {}".format(filename))
                self.img_queue.task_done()
            else:
                self.img_queue.task_done()
                break
        end = time.perf_counter()

        logging.info("created {} thumbnails in {} seconds".format(num_images, end - start))

    def resize_image(self, filename):
        target_sizes = [32, 64, 200]
        logging.info("resizing image {}".format(filename))
        orig_img = Image.open(self.input_dir + os.path.sep + filename)
        for baseWidth in target_sizes:
            img = orig_img
            # calculate target height of the resized image to maintain the aspect ratio
            wpercent = (baseWidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            # perform resizing
            img = img.resize((baseWidth, hsize), PIL.Image.LANCZOS)

            # save the resized image to the output dir with a modified file name
            new_filename = os.path.splitext(filename)[0] + \
                           '_' + str(baseWidth) + os.path.splitext(filename)[1]
            img.save(self.output_dir + os.path.sep + new_filename)

        os.remove(self.input_dir + os.path.sep + filename)
        logging.info("done resizing image {}".format(filename))
        self.img_queue.task_done()
    def make_thumbnails(self, img_url_list):
        logging.info("START make_thumbnails")
        start = time.perf_counter()
        dl_queue = Queue()

        for img_url in img_url_list:
            dl_queue.put(img_url)

        num_dl_thread = 4
        for _ in range(num_dl_thread):
            t1 = Thread(target=self.download_image, args=(dl_queue,))
            t1.start()

        dl_queue.join()
        pool = multiprocessing.Pool()
        start_resize = time.perf_counter()
        pool.map(self.resize_image, self.img_list)
        end_resize = time.perf_counter()
        pool.close()
        pool.join()

        end = time.perf_counter()
        logging.info("Created {} thumbnails in {} seconds".format(len(self.img_list), end_resize - start_resize))
        logging.info("END make_thumbnails in {} seconds".format(end - start))
