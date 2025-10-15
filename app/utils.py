# import re
# import math
# import datetime
# import requests
# import random
# import string
# import pytz
# import json
# import hmac
# import hashlib
# import io
# import sys
# import csv
# from io import StringIO
# from django.core.files.base import ContentFile
# from Crypto.Cipher import AES
# from Crypto.Util.Padding import pad, unpad
# from base64 import b64decode, b64encode
# from django.utils.translation import ugettext_lazy as _
# from django.utils import timezone
# from django.conf import settings
# from django.utils import translation
# from essentials.env import get_ev
# from django.core.files.uploadedfile import InMemoryUploadedFile



# class CipherUtils:

#     @staticmethod
#     def hash_string(txt):
#         return hashlib.sha256(txt.encode('utf-8')).digest()

#     @staticmethod
#     def get_cipher(secret=None):
#         return AES.new(secret or settings.AUTH_SECRET, AES.MODE_CBC, iv=settings.AUTH_IV)

#     @classmethod
#     def encrypt(cls, data: dict, secret=None):
#         ct = cls.get_cipher(secret).encrypt(pad(json.dumps(data).encode('utf-8'), AES.block_size))
#         return b64encode(hmac.new(secret or settings.AUTH_SECRET, ct, hashlib.sha256).digest() + ct).hex()

#     @classmethod
#     def decrypt(cls, data: str, secret=None):
#         try:
#             data = b64decode(bytes.fromhex(data))
#         except ValueError:
#             return
#         if len(data) <= 32:
#             return
#         if not hmac.compare_digest(data[:32], hmac.new(secret or settings.AUTH_SECRET, data[32:], hashlib.sha256).digest()):
#             return
#         return json.loads(unpad(cls.get_cipher(secret).decrypt(data[32:]), AES.block_size).decode('utf-8'))
