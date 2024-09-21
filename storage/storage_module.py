import cv2
import h5py
import wave
import numpy as np
import os
from typing import Any, List
from models import FrameDataModel
from datetime import datetime
import threading
import time


class StorageModule:
    pass