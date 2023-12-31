import easyocr # (Optical Character Recognition)
import numpy as np
import PIL
from PIL import Image, ImageDraw
import cv2
import os
import re

# [Data frame libraries]
import pandas as pd

# [Database library]
import sqlalchemy
import mysql.connector
from sqlalchemy import create_engine, inspect
from sqlalchemy import create_engine, VARCHAR, TEXT
from sqlalchemy.types import String

# [Dashboard library]
import streamlit as st

# ===================================================   /   /   Dash Board   /   /   ======================================================== # 

# Comfiguring Streamlit GUI 
st.set_page_config(layout='wide')

# Title
st.title(':blue[Business Card Data Extraction]')

# Tabs 
tab1, tab2 = st.tabs(["Data Extraction zone", "Data modification zone"])

# ==========================================   /   /   Data Extraction and upload zone   /   /   ============================================== #

with tab1:
    st.subheader(':red[Data Extraction]')

    # Image file uploaded
    import_image = st.file_uploader('**Select a business card (Image file)**', type =['png','jpg', "jpeg"], accept_multiple_files=False)

    # Note
    st.markdown('''File extension support: **PNG, JPG, TIFF**, File size limit: **2 Mb**, Image dimension limit: **1500 pixel**, Language : **English**.''')

    # --------------------------------      /   Extraction process   /     ---------------------------------- #

    if import_image is not None:
        try:
            # Create the reader object with desired languages
            reader = easyocr.Reader(['en'], gpu=False)

        except:
            st.info("Error: easyocr module is not installed. Please install it.")

        try:
            # Read the image file as a PIL Image object
            if isinstance(import_image, str):
                image = Image.open(import_image)
            elif isinstance(import_image, Image.Image):
                image = import_image
            else:
                image = Image.open(import_image)
            
            image_array = np.array(image)
            text_read = reader.readtext(image_array)

            result = []
            for text in text_read:
                result.append(text[1])

        except:
            st.info("Error: Failed to process the image. Please try again with a different image.")

    # -------------------------      /   Display the processed card with yellow box   /     ---------------------- #

        col1, col2= st.columns(2)

        with col1:
            # Define a funtion to draw the box on image
            def draw_boxes(image, text_read, color='yellow', width=2):

                # Create a new image with bounding boxes
                image_with_boxes = image.copy()
                draw = ImageDraw.Draw(image_with_boxes)
                
                # draw boundaries
                for bound in text_read:
                    p0, p1, p2, p3 = bound[0]
                    draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
                return image_with_boxes

            # Function calling
            result_image = draw_boxes(image, text_read)

            # Result image
            st.image(result_image, caption='Captured text')

    # ----------------------------    /     Data processing and converted into data frame   /   ------------------ #

        with col2:
            # Initialize the data dictionary
            data = {
                "Company_name": [],
                "Card_holder": [],
                "Designation": [],
                "Mobile_number": [],
                "Email": [],
                "Website": [],
                "Area": [],
                "City": [],
                "State": [],
                "Pin_code": [],
                }

            # funtion define
            def get_data(res):
                city = ""  # Initialize the city variable
                for ind, i in enumerate(res):
                    # To get WEBSITE_URL
                    if "www " in i.lower() or "www." in i.lower():
                        data["Website"].append(i)
                    elif "WWW" in i:
                        data["Website"].append(res[ind-1] + "." + res[ind])

                    # To get EMAIL ID
                    elif "@" in i:
                        data["Email"].append(i)

                    # To get MOBILE NUMBER
                    elif "-" in i:
                        data["Mobile_number"].append(i)
                        if len(data["Mobile_number"]) == 2:
                            data["Mobile_number"] = " & ".join(data["Mobile_number"])

                    # To get COMPANY NAME
                    elif ind == len(res) - 1:
                        data["Company_name"].append(i)

                    # To get CARD HOLDER NAME
                    elif ind == 0:
                        data["Card_holder"].append(i)

                    # To get DESIGNATION
                    elif ind == 1:
                        data["Designation"].append(i)

                    # To get AREA
                    if re.findall("^[0-9].+, [a-zA-Z]+", i):
                        data["Area"].append(i.split(",")[0])
                    elif re.findall("[0-9] [a-zA-Z]+", i):
                        data["Area"].append(i)

                    # To get CITY NAME
                    match1 = re.findall(".+St , ([a-zA-Z]+).+", i)
                    match2 = re.findall(".+St,, ([a-zA-Z]+).+", i)
                    match3 = re.findall("^[E].*", i)
                    if match1:
                        city = match1[0]  # Assign the matched city value
                    elif match2:
                        city = match2[0]  # Assign the matched city value
                    elif match3:
                        city = match3[0]  # Assign the matched city value

                    # To get STATE
                    state_match = re.findall("[a-zA-Z]{9} +[0-9]", i)
                    if state_match:
                        data["State"].append(i[:9])
                    elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
                        data["State"].append(i.split()[-1])
                    if len(data["State"]) == 2:
                        data["State"].pop(0)

                    # To get PINCODE
                    if len(i) >= 6 and i.isdigit():
                        data["Pin_code"].append(i)
                    elif re.findall("[a-zA-Z]{9} +[0-9]", i):
                        data["Pin_code"].append(i[10:])

                data["City"].append(city)  # Append the city value to the 'city' array
                
            # Call funtion
            get_data(result)

            # Create dataframe
            data_df = pd.DataFrame(data)

            # Save DataFrame to a CSV file
            #data_df.to_csv('data_df.csv', index=False)

            # Show dataframe
            st.dataframe(data_df.T)

                # Upload button
            #st.write('Click the :red[**Upload to MySQL DB**] button to upload the data')
            #Upload = st.button('**Upload to MySQL DB**', key='upload_button')

            # Connect to the MySQL server
            connect = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Pwd@123456",
                database = "sample_db")
                
            
            mycursor = connect.cursor()
            mycursor.close()
            

        # Define a function to insert data into the MySQL table
        def insert_into_mysql(df, table_name, connection):
            cursor = connection.cursor()

            # Create the table if it doesn't exist
            cursor.execute(f"CREATE TABLE IF NOT EXISTS sample_tbl (Company_name VARCHAR(255), Card_holder VARCHAR(255), Designation VARCHAR(255), Mobile_number VARCHAR(255), Email VARCHAR(255), Website VARCHAR(255), Area VARCHAR(255), City VARCHAR(255), State VARCHAR(255), Pin_code VARCHAR(255));")

            # Insert data into the table
            for index, row in df.iterrows():
                values = tuple(row)
                cursor.execute(f"INSERT INTO sample_tbl VALUES {values};")

            # Commit the changes and close the cursor
            connection.commit()
            cursor.close()

        # Call the function with your DataFrame
        #table_name = 'sample_tbl'
        #insert_into_mysql(data_df, table_name, connect)

                # Button to insert data into MySQL
        if st.button("Insert into MySQL"):
                table_name = 'sample_tbl'
                #table_name = st.text_input("Enter table name:", "sample_tbl")
                insert_into_mysql(data_df, table_name,connect)

                st.success("Data sent to MySQL table successfully!")

       
        # Close the MySQL connection
        connect.close()