import logging
import multiprocessing
import os.path
import time
from threading import Thread
from urllib.parse import urlparse

import PIL
import asyncio
import aiofiles
import aiohttp
from PIL import Image

FORMAT = "[%(threadName)s, %(asctime)s, %(levelname)s] %(message)s"
logging.basicConfig(filename='logfile.log', format=FORMAT,
                    level=logging.DEBUG, handlers=[logging.StreamHandler()])


class ThumbnailMakerService(object):
    def __init__(self, home_dir='.'):
        self.home_dir = home_dir
        self.input_dir = self.home_dir + os.path.sep + 'incoming'
        self.output_dir = self.home_dir + os.path.sep + 'outgoing'
        self.img_queue = multiprocessing.JoinableQueue()

    async def download_image_coro(self, session, url):
        img_file_name = urlparse(url).path.split('/')[-1]
        img_file_path = self.input_dir + os.path.sep + img_file_name

        async with session.get(url) as response:
            async with aiofiles.open(img_file_path, 'wb') as f:
                content = await response.content.read()
                await f.write(content)
        self.img_queue.put(img_file_name)

    async def download_images_coro(self, img_url_list):
        async with aiohttp.ClientSession() as session:
            for url in img_url_list:
                await self.download_image_coro(session, url)
    def download_images(self, img_url_list):
        # validate inputs
        if not img_url_list:
            return
        os.makedirs(self.input_dir, exist_ok=True)
        logging.info("beginning image download")

        start = time.perf_counter()
        # download each image and save to the input dir
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.download_images_coro(img_url_list))
        finally:
            loop.close()

        end = time.perf_counter()

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

    def make_thumbnails(self, img_url_list):
        logging.info("START make_thumbnails")
        start = time.perf_counter()
        #
        # dl_queue = Queue()
        #
        # for img_url in img_url_list:
        #     dl_queue.put(img_url)
        #
        # num_dl_thread = 4
        # for _ in range(num_dl_thread):
        #     t1 = Thread(target=self.download_image)
        #     t1.start()

        num_processes = multiprocessing.cpu_count()
        for _ in range(num_processes):
            process = Thread(target=self.perform_resizing)
            process.start()

        self.download_images(img_url_list)

        for _ in range(num_processes):
            self.img_queue.put(None)

        end = time.perf_counter()
        logging.info("END make_thumbnails in {} seconds".format(end - start))
