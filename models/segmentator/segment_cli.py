import json
import os
import sys
import time
from .DOMParser import DOMParser
import threading

def main(args):
    #python3 segment_cli.py -u https://www.blogger.com/profile/03668805078631473625
    #-u for url
    #-f for file
    if args[1] == "-u":
        url = args[2]
        dom_document = DOMParser(url)
        print(dom_document.get_segments())

    elif args[1] == "-f":
        url = "file://" + args[2]
        dom_document = DOMParser(url)
        print(dom_document.get_segments())

    elif args[1] == "-i" and args[3] == "-o":
        urls = json.load(open(args[2], "r"))
        driver = None
        segmentation = {}
        for url in urls:
            dom_document = DOMParser(url, driver=driver, killDriver=False)
            driver = dom_document.browser
            segmentation[url] = dom_document.get_segments()
        json.dump(segmentation, open(args[4], "w"))
    
if __name__ == '__main__':
    main(args = sys.argv)
