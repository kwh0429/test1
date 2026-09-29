import os
import sys

# 현재 파일 위치(api/)의 부모 폴더(프로젝트 루트)를 파이썬 경로에 추가
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
