"""
WhmcsApi
"""
import sys, pprint

from errors import *
from manager import VendorManager, RequestTranslator
from webclient import WebClient
from walker import XMLWalker

class WhmcsApi:
    """
    This class will some day be an adapter for WHMCS External Api.
    """
    import re, json
    import config

    vendor = 'WHMCS'
    products = [ 'WHMCS' ]

    res_field_dict = {}
    req_field_dict = {}

    response_dict = {}
    request_dict = {}

