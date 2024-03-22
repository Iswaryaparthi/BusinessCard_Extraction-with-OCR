import streamlit as st
import pandas as pd
import easyocr
import re
import tempfile
import os
import mysql.connector

# working code as of 20/03/2024

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Connect to MySQL database
db_connection = mysql.connector.connect(
    host="localhost",
    user="username",
    password="password",
    database="bizcardx_db"
)
cursor = db_connection.cursor()

def process_image(image_bytes):
    # Save image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_image:
        temp_image.write(image_bytes.getvalue())
        image_path = temp_image.name
    
    # Read text from image
    result = reader.readtext(image_path, detail=0)

    # Delete temporary file
    os.unlink(image_path)

    return result

def get_data(result):
    data = {
        "card_holder": [],
        "designation": [],
        "mobile_number": [],
        "email": [],
        "website": [],
        "area": [],
        "city": [],
        "state": [],
        "pin_code": [],
        "company_name": []
    }

    for ind, i in enumerate(result):
        # To get WEBSITE_URL
        if "www " in i.lower() or "www." in i.lower():
            data["website"].append(i)
        elif "WWW" in i:
            data["website"].append(result[4] + "." + result[5])

        # To get EMAIL ID
        elif "@" in i:
            data["email"].append(i)

        # To get MOBILE NUMBER
        elif "-" in i:
            data["mobile_number"].append(i)
            if len(data["mobile_number"]) == 2:
                data["mobile_number"] = " & ".join(data["mobile_number"])

        # To get COMPANY NAME  
        elif ind == len(result) - 1:
            data["company_name"].append(i)

        # To get CARD HOLDER NAME
        elif ind == 0:
            data["card_holder"].append(i)

        # To get DESIGNATION
        elif ind == 1:
            data["designation"].append(i)

        # To get AREA
        if re.findall('^[0-9].+, [a-zA-Z]+', i):
            data["area"].append(i.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+', i):
            data["area"].append(i)

        # To get CITY NAME
        match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
        match3 = re.findall('^[E].*', i)
        if match1:
            data["city"].append(match1[0])
        elif match2:
            data["city"].append(match2[0])
        elif match3:
            data["city"].append(match3[0])

        # To get STATE
        state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
        if state_match:
            data["state"].append(i[:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
            data["state"].append(i.split()[-1])
        if len(data["state"]) == 2:
            data["state"].pop(0)

        # To get PINCODE        
        if len(i) >= 6 and i.isdigit():
            data["pin_code"].append(i)
        elif re.findall('[a-zA-Z]{9} +[0-9]', i):
            data["pin_code"].append(i[10:])

    return data

# insert into mysql table

def insert_data_into_mysql(df,image_name):
    cursor = db_connection.cursor()

    # Check if the image name already exists in the table
    cursor.execute("SELECT COUNT(*) FROM card_data_v1 WHERE image_name = %s", (image_name,))
    result = cursor.fetchone()[0]

    # If the image name doesn't exist, proceed with the insertion
    if result == 0:

        for i, row in df.iterrows():
            # Convert lists to strings
            for col in df.columns:
                if isinstance(row[col], list):
                    row[col] = ', '.join(row[col])

            sql = """INSERT INTO card_data_v1 (card_holder, designation, mobile_number, email, website, area, city, 
                                            state, pin_code, company_name, image_name) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, tuple(row) + (image_name,))  # Add image_name as a parameter

        db_connection.commit()
        st.success("Uploaded to database successfully!")
    else:
        st.warning("Data already exists in the table. Skipping insertion.")

# update the inserted data 
        
def update_data_in_db(row_data):
    cursor = db_connection.cursor()
    # Update the data in the database based on the row_data
    sql = """UPDATE card_data_v1 SET designation = %s, mobile_number = %s, email = %s, website = %s,
      area = %s, city = %s, state = %s, pin_code = %s, company_name = %s WHERE card_holder = %s"""
    values = (row_data['designation'], row_data['mobile_number'], row_data['email'], row_data['website'], 
              row_data['area'], row_data['city'], row_data['state'], row_data['pin_code'], 
              row_data['company_name'], row_data['card_holder'])
    cursor.execute(sql, values)
    db_connection.commit()
    st.success("Data updated successfully!")

# delete operation
    
def delete_data_from_db(card_holder):
    cursor = db_connection.cursor()
    try:
        # Delete the data from the database based on the card_holder (assuming card_holder is unique)
        sql = "DELETE FROM card_data_v1 WHERE card_holder = %s"
        cursor.execute(sql, (card_holder,))
        db_connection.commit()
        cursor.fetchall()  # Consume unread result sets
        st.success("Data deleted successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error deleting data: {err}")
    finally:
        cursor.close()

# displaying the existing data in DB
        
def get_existing_data(card_holder):
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM card_data_v1 WHERE card_holder = %s", (card_holder,))
    data = cursor.fetchone()
    return data

# Streamlit app
  
def main():

    selected_card_holder = None

    st.title(":rainbow[BizCard Extraction Using EasyOCR]")

    st.subheader(":green[Introduction]")

    st.markdown('''EasyOCR is a Python computer language Optical Character Recognition (OCR) module that is 
                both flexible and easy to use. OCR technology is useful for a variety of tasks, 
                including data entry automation and image analysis. It enables computers to identify and 
                extract text from cards,pinboards, photographs or scanned documents.''')
    
    st.subheader(":blue[Technologies used]")

    st.markdown(''' Python, Pandas, os, re, EasyOCR, Streamlit''')

    st.sidebar.title(":green[Upload Image]")
    uploaded_file = st.sidebar.file_uploader(":orange[Choose an image...]", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        st.sidebar.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.write("")

        # Process the image and get text
        result = process_image(uploaded_file)

        # Parse the text and create a DataFrame
        parsed_result = get_data(result)
        df = pd.DataFrame([parsed_result])

        # Display the result in a table
        st.write(df)

        # Save to DB button
        if st.button("Save to DB"):
            # Extract the image name
            image_name = uploaded_file.name
            insert_data_into_mysql(df, image_name)

    # Fetch data from the database
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM card_data_v1")
    data = cursor.fetchall()

    # Check if data is fetched
    if data:
        # Display the data fetched from the database
        df_db = pd.DataFrame(data, columns=['id','card_holder', 'designation', 'mobile_number', 'email', 'website',
                                             'area', 'city', 'state', 'pin_code', 'company_name','image_name'])
        st.subheader(":red[View and Modify Data]")
        st.write("Here you can view and modify the data saved in the database.")
        st.write(df_db)

        selected_card_holder = st.selectbox("Select Card Holder to Update or Delete", df_db['card_holder'])

    if selected_card_holder:
        # Fetch existing data for the selected card_holder
        existing_data = get_existing_data(selected_card_holder)

        if existing_data:
            st.write("Existing Data:")
            st.write(existing_data)

            new_designation = st.text_input("New Designation", value=existing_data[1])
            new_mobile_number = st.text_input("New Mobile Number", value=existing_data[2])
            new_email = st.text_input("New Email", value=existing_data[3])
            new_website = st.text_input("New Website", value=existing_data[4])
            new_area = st.text_input("New Area", value=existing_data[5])
            new_city = st.text_input("New City", value=existing_data[6])
            new_state = st.text_input("New State", value=existing_data[7])
            new_pin_code = st.text_input("New Pin Code", value=existing_data[8])
            new_company_name = st.text_input("New Company Name", value=existing_data[9])

            if st.button("Update"):
                # Create a dictionary containing the updated data
                updated_data = {
                    'card_holder': selected_card_holder,
                    'designation': new_designation,
                    'mobile_number': new_mobile_number,
                    'email': new_email,
                    'website': new_website,
                    'area': new_area,
                    'city': new_city,
                    'state': new_state,
                    'pin_code': new_pin_code,
                    'company_name': new_company_name
                }
                # Perform the update operation
                update_data_in_db(updated_data)
                # st.success("Data updated successfully!")

            if st.button("Delete"):
                # Perform the delete operation
                delete_data_from_db(selected_card_holder)
                #st.success("Data deleted successfully!")

if __name__ == "__main__":
    main()
