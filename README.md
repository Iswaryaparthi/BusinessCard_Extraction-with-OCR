# BizCardX: Extracting Business Card Data with OCR 

## Introduction

### With the advent of digital tools and technologies, manual entry of business card details into a database can be time-consuming and prone to errors. To overcome these challenges, developers can leverage the power of optical character recognition (OCR) and databases to automate the process of extracting relevant information from business cards and storing it for easy access.
### One powerful OCR library that facilitates the extraction of text from images is EasyOCR. EasyOCR is an open-source Python library that utilizes deep learning models to accurately recognize and extract text from various languages. By integrating EasyOCR with a MySQL database, developers can streamline the process of capturing business card data and storing it in a structured and organized manner.

### Tools Used

* Virtual environment
* Python 3.11.0 
* MySQL 

### Import Libraries

* import easyocr # (Optical Character Recognition)
* import numpy as np
* from PIL
* from PIL import Image, ImageDraw
* import cv2
* import os
* import re
* import pandas as pd
* import mysql.connector
* import streamlit as st

### Extract data

* Upload the business card and extract the relevant information  using the easyOCR library

### Process and Transform the data

* Process the extracted data based on the user requirements like Company Name, Card Holder, Designation, Mobile Number, Email, Website, Area, City, State, and Pincode
* After the extractions done convert those datas into a data frame for further use

### Load data

* After the transformation process into Dataframe, the data is stored in the MySQL database in tabular format.
* The user can able to update or delete business card data.
* Streamlit Application is used to do all CRUD operations among business cards.

Thank you all!
