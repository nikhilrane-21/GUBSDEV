import pymongo
import streamlit_authenticator as stauth
import os
import json
import pymongo
import re
from PIL import Image
import pandas as pd
# import pytesseract
import math
import numpy as np
from typing import Tuple, Union
from deskew import determine_skew
import cv2
from pyPdfToImg import convert_from_bytes
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from pyImgToText import image_to_string, image_to_data
import dbmongo as dbm
# from InvoiceNet import predict

# Intializing Some variables for part3
ref_point = []
total_amount = ""
crop = False
onboard = 0
# flag = 0
shiftx = 0
shifty = 0
shiftw = 0
shifth = 0
datetext = ""
invnotext = ""
billtext = ""
regexbilltext = ""
buyertext = ""
sellertext = ""
file_uploaded = False
found = 0  # variable to check if a matching template is found
matched_doc = ""  # to store the template that has match with the template
curr = 0
image= None


# function to rotate and remove the skew from the image
def rotate(image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]) -> np.ndarray:
    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)
    width = abs(np.sin(angle_radian) * old_height) + \
            abs(np.cos(angle_radian) * old_width)
    height = abs(np.sin(angle_radian) * old_width) + \
             abs(np.cos(angle_radian) * old_height)

    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)


def isValid(total_amount):
    total_amount = total_amount.strip()
    if (len(total_amount) == 0):
        print("tr")
        return False
    elif (len(total_amount) > 0):
        for ch in total_amount:
            if (ch != "." and ch != "," and ch.isdigit() != True):
                return False
    return True


def match_last(orig_string, regex):
    re_lookahead = re.compile(regex)
    match = None
    for match in re_lookahead.finditer(orig_string):
        pass

    if match:
        re_complete = re.compile(regex)
        return re_complete.match(orig_string, match.start())
    return match


def method3():
    global regexbilltext

    # images = convert_from_path(file.name, poppler_path="C:/poppler-0.68.0/bin")
    keyword = matched_doc

    # Getting the mongo db document of the matched template
    matched_invoice = db.invoices.find({"keyword": keyword.strip()})

    start = 0
    count = 0
    for invoice in matched_invoice:
        count += 1
        start = invoice[
            "match_start"]  # Starting word in sandwich technique that will be searched for
        end = invoice[
            "match_end"]  # Ending word in sandwich technique that will be searched for

    # if no starting word can be found
    if (start == "-1"):
        count = 0
    flag = -1

    # Finally searching for the matched starting and ending keyword and returning the amount stored b/w them
    if count == 1:
        text = fullinvoicetext

        # Searching for a string that has start and end and any string stored in between in it in the text of the pdf
        regex = r"(?s)(?<=" + start + r")(.*?)(?=" + end + r")"
        start_end = re.search(regex, text)
        # start_end = match_last(text, regex)
        # if (start_end == None):
        #     pass

        # If the start and end is found
        if (start_end != None):
            flag = 0
            text = start_end.group()

            # regex to get the amount stored between the start and end words
            amount_regex = "[0-9.,]+\n"
            total_amount_3 = match_last(text, amount_regex)

            try:
                total_amount_3 = total_amount_3.group()
                total_amount_3 = total_amount_3.strip()
            except AttributeError:
                print("Error: no match found for amount_regex.")
                total_amount_3 = ""

            # write the result to a file
            try:
                with open('out.txt', 'w') as f:
                    f.write(total_amount_3)
            except IOError:
                print("Error writing to file: out.txt")

        # If no amount is found, write false to indicate in the temporary output file
        if (flag == -1):
            with open('out.txt', 'w') as f:
                f.write("false, no amount")
    else:
        with open('out.txt', 'w') as f:
            f.write("-1, write to file fail")
        print("-1, write to file fail")

    outfile = open("out.txt")
    total_amount_3 = outfile.read()
    regexbilltext = total_amount_3
    outfile.close()
    return total_amount_3


# function  to get the starting parameter and ending paramter for part 3
def getstartend(total_amount, text):
    lines = text.split("\n")
    # remove the empty lines
    non_empty_lines = [line for line in lines if line.strip() != ""]
    string_without_empty_lines = ""
    for line in non_empty_lines:
        string_without_empty_lines += line + "\n"
    text = string_without_empty_lines  # This conatins no empty lines
    with open('textforstartend.txt', 'w') as f:
        f.write(text)
    total_amount = total_amount.strip()

    # regex to match the first word in the line where total amount occurs and the first of the next line of total amount.
    # These are the start and the end parameters respectively
    isAvailable = re.search(f"{total_amount}", text)
    if isAvailable != None:
        start_end = re.search('\n.*?' + f"\s{total_amount}" + '.*?\n\w+',
                              text)

        if (start_end != None):
            start = re.search(r'[a-zA-Z]+', start_end.group())
            start = start.group()
            end = start_end.group().split("\n")[-1].strip()
            return start, end
        else:
            # If no regex matches
            return "-1", "-1"
    else:
        return "-1", "-1"


def read_fields_from_image(image_path, fields, shiftx, shifty, shiftw, shifth):
    results = {}
    img1 = Image.open(image_path)

    for field_name, bbox in fields.items():
        bbox = (bbox["x1"] + shiftx, bbox["y1"] + shifty, bbox["x2"] + shiftw, bbox["y2"] + shifth)
        # img_crop_path = f"{field_name}.png"
        img_crop = img1.crop(bbox)
        # img_crop.save(img_crop_path)
        # img_crop.close()
        text = str(image_to_string(img_crop, lang='eng'))
        results[field_name] = text

    img1.close()
    return results


# function to get the desired fields when a template has been matched for the pdf
def getinf(item):
    global datetext
    global invnotext
    global billtext
    global buyertext
    global sellertext

    # Cropping and saving the rectangle that contains the keyword
    img1 = Image.open("page0.jpg")
    img1 = img1.crop((item["keyword_cordinates"]["x1"] + shiftx,
                      item["keyword_cordinates"]["y1"] + shifty,
                      item["keyword_cordinates"]["x2"] + shiftw,
                      item["keyword_cordinates"]["y2"] + shifth))
    img1.save('img2.png')
    img1.close()

    fields = {
        "Date": item["Date"],
        "Invoice_No": item["Invoice_No"],
        "Total Bill": item["Total Bill"],
        "Buyer": item["Buyer"],
        "Seller": item["Seller"]
    }

    results = read_fields_from_image("page0.jpg", fields, shiftx, shifty, shiftw, shifth)

    datetext = results["Date"]
    invnotext = results["Invoice_No"]
    billtext = results["Total Bill"]
    buyertext = results["Buyer"]
    sellertext = results["Seller"]


    #
    # # Cropping and saving the rectangle that contains the Date of Invoice
    # img1 = Image.open("page0.jpg")
    # img1 = img1.crop((item["Date"]["x1"] + shiftx,
    #                   item["Date"]["y1"] + shifty,
    #                   item["Date"]["x2"] + shiftw,
    #                   item["Date"]["y2"] + shifth))
    # img1.save('date.png')
    # img1.close()
    # # reading text from the cropped image to get the Date of Invoice
    # datetext = str(
    #     pytesseract.image_to_string(Image.open(r"date.png"), lang='eng'))
    #
    # # reading the Invoice No after selecting the bounding box
    # img1 = Image.open("page0.jpg")
    # img1 = img1.crop((item["Invoice_No"]["x1"] + shiftx,
    #                   item["Invoice_No"]["y1"] + shifty,
    #                   item["Invoice_No"]["x2"] + shiftw,
    #                   item["Invoice_No"]["y2"] + shifth))
    # img1.save('invno.png')
    # img1.close()
    # invnotext = str(
    #     pytesseract.image_to_string(Image.open(r"invno.png"), lang='eng'))
    #
    # # reading the Total bill after selecting the bounding box
    # img1 = Image.open("page0.jpg")
    # img1 = img1.crop((item["Total Bill"]["x1"] + shiftx,
    #                   item["Total Bill"]["y1"] + shifty,
    #                   item["Total Bill"]["x2"] + shiftw,
    #                   item["Total Bill"]["y2"] + shifth))
    # img1.save('bill.png')
    # img1.close()
    # billtext = str(
    #     pytesseract.image_to_string(Image.open(r"bill.png"), lang='eng'))
    # total_amount = billtext
    #
    # # reading the Buyer Address after selecting the bounding box
    # img1 = Image.open("page0.jpg")
    # img1 = img1.crop((item["Buyer"]["x1"] + shiftx,
    #                   item["Buyer"]["y1"] + shifty,
    #                   item["Buyer"]["x2"] + shiftw,
    #                   item["Buyer"]["y2"] + shifth))
    # img1.save('buyer.png')
    # img1.close()
    # buyertext = str(
    #     pytesseract.image_to_string(Image.open(r"buyer.png"), lang='eng'))
    #
    # # reading the Seller Address  after selecting the bounding box
    # img1 = Image.open("page0.jpg")
    # img1 = img1.crop((item["Seller"]["x1"] + shiftx,
    #                   item["Seller"]["y1"] + shifty,
    #                   item["Seller"]["x2"] + shiftw,
    #                   item["Seller"]["y2"] + shifth))
    # img1.save('seller.png')
    # img1.close()
    # sellertext = str(
    #     pytesseract.image_to_string(Image.open(r"seller.png"), lang='eng'))

    return billtext


def generate_table(data):
    table = "<table>"
    headings = ["Index", "Vendor Name", "Required Fields", "Training"]
    table += "<tr>"
    for heading in headings:
        table += "<th>" + heading + "</th>"
    table += "</tr>"
    for index, row in enumerate(data):
        table += "<tr>"
        table += "<td>" + str(index + 1) + "</td>"
        for cell in row:
            table += "<td>" + str(cell) + "</td>"
        table += "<td><button>View</button></td>"
        table += "</tr>"
    table += "</table>"
    return table


# def store_info(img, field_name, objects, keyword, db):
#     # get the index of the field in the objects dictionary
#     if field_name=="Date":
#         idx = 0
#     elif field_name=="Invoice_No":
#         idx = 1
#     elif field_name == "Total Bill":
#         idx = 2
#     elif field_name == "Buyer":
#         idx = 3
#     elif field_name == "Seller":
#         idx = 4
#     else:
#         return
#
#     # extract the bounding box for the field
#     crop_box = (objects["left"][idx] * 2,
#                 objects["top"][idx] * 2,
#                 objects["left"][idx] * 2 + objects["width"][idx] * 2,
#                 objects["top"][idx] * 2 + objects["height"][idx] * 2)
#     img3 = img.crop(crop_box)
#
#     # extract the text and store it in the database
#     left = np.int64(objects["left"][idx])
#     left = left.item()
#     top = np.int64(objects["top"][idx])
#     top = top.item()
#     right = np.int64(objects["left"][idx] + objects["width"][idx])
#     right = right.item()
#     bottom = np.int64(objects["top"][idx] + objects["height"][idx])
#     bottom = bottom.item()
#     db.invoices.update_one({"keyword": keyword}, {"$set": {
#         field_name: {"x1": left * 2, "y1": top * 2,
#                      "x2": right * 2, "y2": bottom * 2}}})
#     # img3.save(f"{field_name}.png")
#     # img3.close()
#     # image = Image.open(f"{field_name}.png")
#     # image.close()
#     text = str(pytesseract.image_to_string(img3, lang='eng'))
#     if field_name == "Total Bill":
#         # Storing the word before and after the total bill for part 3
#         wholetext = str(pytesseract.image_to_string(Image.open(r"page0.jpg"), lang='eng'))
#         wholetext = wholetext.strip()
#         match_start, match_end = getstartend(total_amount, wholetext)
#
#         db.invoices.update_one({"keyword": keyword}, {"$set": {"match_start": match_start}})
#         db.invoices.update_one({"keyword": keyword}, {"$set": {"match_end": match_end}})
#
#     return text.strip()


def process_file(file):
    file_type = file.type
    if file_type == "image/png":
        image = file.read()
    else:
        file_bytes = file.read()
        images = convert_from_bytes(file_bytes)
        for i in range(len(images)):
            images[i].save('page' + str(i) + '.jpg', 'JPEG')

        image = cv2.imread('page0.jpg')
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        rotated = rotate(image, angle, (0, 0, 0))
        cv2.imwrite('page0.jpg', rotated)
        image = cv2.imread('page0.jpg')

    return image

st.set_page_config(
    page_title='Invoice Text Extractor',
    page_icon=':robot:',
    layout='wide'
)

hide_st_style = """
                <style>
                    footer {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Connection to db
# MONGO_URI = os.getenv("MONGO_URI")
connection = pymongo.MongoClient("mongodb+srv://nikhil:nikhil@atlascluster.7o742.mongodb.net/?retryWrites=true&w=majority")
db = connection.helloworld


# --- USER AUTHENTICATION ---
users = dbm.fetch_all_users()

# usernames = [user["key"] for user in users]
usernames = [user["username"] for user in users]
names = [user["name"] for user in users]
hashed_passwords = [user["password"] for user in users]

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "ID", "abcdef")

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:

    st.header(f"Welcome {name} to Invoice Text Extractor")

    user_db = connection[username]
    invoices_collection = user_db["invoices"]




    # debugging
    # st.session_state

    authenticator.logout("Logout", "main")


    tab1, tab2, tab3, tab4 = st.tabs(["Vendors", "Orders", "Submissions", "My Profile"])

    with tab1:

        placeholder = st.empty()

    # Replace the chart with several elements:
        with placeholder.container():
            t1col1, t1col2 = st.columns([4,1])

    # with t1col1:
    data = []
    invoices = db.invoices.find()
    for invoice in invoices:
        data.append((invoice["keyword"], "Date, Invoice No."))



    t1col1.markdown(generate_table(data), unsafe_allow_html=True)

    add_vendor_button_pressed = t1col2.button("Add Vendor", key="add_vendor_button")

    if add_vendor_button_pressed:
        st.session_state.add_vendor = True
    if "add_vendor" in st.session_state.keys():
        placeholder.empty()
        # with tab1.placeholder.container():
        t1col1, t1col2 = placeholder.container().columns([4,1])

        # # Get the uploaded file from the session state
        # uploaded_file = st.session_state.get("uploaded_file")
        #
        # # Check if the file has been uploaded
        # if uploaded_file is None:

        file = placeholder.file_uploader("Upload an invoice for onboarding",
                                                  type=["jpg", "jpeg", "png", "pdf", "tiff"])

        if file is not None:
        #     st.session_state["uploaded_file"] = file
        #
        # if "uploaded_file" in st.session_state.keys():

            image = process_file(file)

            # Define the drawing tools
            drawing_tools = ["rect", "transform"]

            # Define the session state
            if 'drawing_mode' not in st.session_state:
                st.session_state.drawing_mode = drawing_tools[0]
            if 'json_data' not in st.session_state:
                st.session_state.json_data = {'objects': []}

            # Display radio buttons for selecting drawing tool
            radio_click = st.radio("Toggle between selecting rectangles and editing them:",
                                                             drawing_tools,
                                                             key="drawing_mode")

            # objects=[]
            # Create a canvas component
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.1)",
                stroke_width=1,
                stroke_color="#000000",
                background_image=Image.fromarray(image),
                height=(image.shape[0]) / 2,
                width=(image.shape[1]) / 2,
                drawing_mode=st.session_state.drawing_mode,
                key="canvas"
            )

            objects = None

            if canvas_result.json_data is not None:
                objects = pd.json_normalize(canvas_result.json_data["objects"])



            # extracting the text of the page1
            # fullinvoicetext = str(pytesseract.image_to_string(Image.fromarray(image), lang='eng'))

            # st.write(fullinvoicetext)

            # if found == 0:
            #     onboard = 1
                # with t1col2:
                    # st.header(
                    #     "No Template found for this Invoice; \nPlease Start the onboarding\n")
                    # st.text(
                    #     "Select boxes on the displayed image in the following order: \n1.Keyword\n2.Date of Invoice\n3.Invoice No.\n4.Buyer Details\n5.Seller Details")
                # objects = canvas.objects
                # If valid selection is made by user while dragging the rectangle, i.e, atleast one rectangle has been selected successfully
            if objects is not None and objects.shape[0] == 6:
                if st.button("Extract data"):

                    # converting the whole pdf to text to match its every word
                    # myimg = Image.open('page0.jpg')
                    data = image_to_data(Image.fromarray(image),
                                                     output_type='dict')
                    img1 = Image.fromarray(image)
                    # cropping and saving only the rectangle portion of the image from where we have to extract the text
                    img3 = img1.crop((objects["left"][0] * 2,
                                      objects["top"][0] * 2,
                                      objects["left"][0] * 2 +
                                      objects["width"][0] * 2,
                                      objects["top"][0] * 2 +
                                      objects["height"][0] * 2))
                    img3.save('keyword.png')
                    img3.close()

                    # image = Image.open('img2.png')
                    # image.close()

                    # text variable contains the text in the bounding box selected
                    text = str(image_to_string(
                        Image.open(r"keyword.png"), lang='eng'))

                    # getting the x and y coordinates of the keyword  from the pdf, for this the text read from the bounding box is matxhed with edvery word
                    # of the pdf and when the word matches we store its x, y coordinates as the keyword's coordinates. This is done to ensure that we dont consider the extra region of the image that ahs not
                    # text , we want a tight bound to x y coordinates for keyword
                    text = text.strip()
                    foundregex = re.search(r'[a-zA-Z]+', text)
                    if (foundregex != None):
                        text = foundregex.group()


                    boxes = len(data['level'])

                    for i in range(boxes):
                        key_to_match = data['text'][i].strip()
                        if (key_to_match != ""):
                            foundregex = re.search(r'[a-zA-Z]+',
                                                   key_to_match)
                            if (foundregex != None):
                                key_to_match = foundregex.group()

                            if key_to_match.strip() == text.strip():
                                break

                    # inserting the new template in the db
                    db.invoices.insert_one({"keyword": text})
                    keyword = text
                    # db.invoices.update_one({"keyword": keyword}, {
                    #     "$set": {"no_of_pages": no_of_pages}})
                    left = np.int64(objects["left"][0])
                    left = left.item()
                    top = np.int64(objects["top"][0])
                    top = top.item()
                    right = np.int64(
                        objects["left"][0] + objects["width"][0])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][0] + objects["height"][0])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {"$set": {
                        "keyword_cordinates": {"x1": left * 2,
                                               "y1": top * 2,
                                               "x2": right * 2,
                                               "y2": bottom * 2}}})

                    # for field_name in ["Date", "Invoice_No", "Total Bill", "Buyer", "Seller"]:
                    #     field_text = store_info(img1, field_name, objects, keyword, db)
                    #     st.write(f"{field_name}: {field_text}")


                    # extracting the date of invoice from the bounding box selected for it and storing its keyword
                    # coordinates in the database
                    img3 = img1.crop((objects["left"][1] * 2,
                                      objects["top"][1] * 2,
                                      objects["left"][1] * 2 +
                                      objects["width"][1] * 2,
                                      objects["top"][1] * 2 +
                                      objects["height"][1] * 2))
                    left = np.int64(objects["left"][1])
                    left = left.item()
                    top = np.int64(objects["top"][1])
                    top = top.item()
                    right = np.int64(
                        objects["left"][1] + objects["width"][1])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][1] + objects["height"][1])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {"$set": {
                        "Date": {"x1": left * 2, "y1": top * 2,
                                 "x2": right * 2, "y2": bottom * 2}}})
                    img3.save('date.png')
                    img3.close()
                    image = Image.open('date.png')
                    image.close()
                    text = str(image_to_string(
                        Image.open(r"date.png"), lang='eng'))
                    datetext = text.strip()

                    # extracting the Invoice No. from the bounding box selected for it and storing its keyword
                    # coordinates in the database
                    img3 = img1.crop((objects["left"][2] * 2,
                                      objects["top"][2] * 2,
                                      objects["left"][2] * 2 +
                                      objects["width"][2] * 2,
                                      objects["top"][2] * 2 +
                                      objects["height"][2] * 2))
                    left = np.int64(objects["left"][2])
                    left = left.item()
                    top = np.int64(objects["top"][2])
                    top = top.item()
                    right = np.int64(
                        objects["left"][2] + objects["width"][2])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][2] + objects["height"][2])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {
                            "Invoice_No": {"x1": left * 2, "y1": top * 2,
                                           "x2": right * 2,
                                           "y2": bottom * 2}}})
                    img3.save('invno.png')
                    img3.close()
                    image = Image.open('invno.png')
                    image.close()
                    text = str(image_to_string(
                        Image.open(r"invno.png"), lang='eng'))
                    invnotext = text.strip()

                    # extracting the Total Bill from the bounding box selected for it and storing its keyword coordinates in the database
                    img3 = img1.crop((objects["left"][3] * 2,
                                      objects["top"][3] * 2,
                                      objects["left"][3] * 2 +
                                      objects["width"][3] * 2,
                                      objects["top"][3] * 2 +
                                      objects["height"][3] * 2))
                    left = np.int64(objects["left"][3])
                    left = left.item()
                    top = np.int64(objects["top"][3])
                    top = top.item()
                    right = np.int64(
                        objects["left"][3] + objects["width"][3])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][3] + objects["height"][3])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {
                            "Total Bill": {"x1": left * 2, "y1": top * 2,
                                           "x2": right * 2,
                                           "y2": bottom * 2}}})
                    img3.save('bill.png')
                    img3.close()
                    image = Image.open('bill.png')
                    image.close()
                    billtext = str(
                        image_to_string(Image.open(r"bill.png"),
                                                    lang='eng'))
                    billtext = billtext.strip()
                    total_amount = billtext

                    # Storing the word before and after the total bill for part 3
                    wholetext = str(image_to_string(
                        Image.open(r"page0.jpg"), lang='eng'))
                    wholetext = wholetext.strip()
                    match_start, match_end = getstartend(total_amount,
                                                         wholetext)

                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {"match_start": match_start}})
                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {"match_end": match_end}})

                    # extracting the Buyer Address from the bounding box selected for it and storing its keyword coordinates in the database
                    img3 = img1.crop((objects["left"][4] * 2,
                                      objects["top"][4] * 2,
                                      objects["left"][4] * 2 +
                                      objects["width"][4] * 2,
                                      objects["top"][4] * 2 +
                                      objects["height"][4] * 2))
                    left = np.int64(objects["left"][4])
                    left = left.item()
                    top = np.int64(objects["top"][4])
                    top = top.item()
                    right = np.int64(
                        objects["left"][4] + objects["width"][4])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][4] + objects["height"][4])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {
                            "Buyer": {"x1": left * 2, "y1": top * 2,
                                      "x2": right * 2, "y2": bottom * 2}}})
                    img3.save('buyer.png')
                    img3.close()
                    image = Image.open('buyer.png')
                    image.close()
                    buyertext = str(image_to_string(
                        Image.open(r"buyer.png"), lang='eng'))
                    buyertext = buyertext.strip()

                    # extracting the Seller Address from the bounding box selected for it and storing its keyword coordinates in the database
                    img3 = img1.crop((objects["left"][5] * 2,
                                      objects["top"][5] * 2,
                                      objects["left"][5] * 2 +
                                      objects["width"][5] * 2,
                                      objects["top"][5] * 2 +
                                      objects["height"][5] * 2))
                    left = np.int64(objects["left"][5])
                    left = left.item()
                    top = np.int64(objects["top"][5])
                    top = top.item()
                    right = np.int64(
                        objects["left"][5] + objects["width"][5])
                    right = right.item()
                    bottom = np.int64(
                        objects["top"][5] + objects["height"][5])
                    bottom = bottom.item()
                    db.invoices.update_one({"keyword": keyword}, {
                        "$set": {"Seller": {"x1": left * 2, "y1": top * 2,
                                            "x2": right * 2,
                                            "y2": bottom * 2}}})
                    img3.save('seller.png')
                    img3.close()
                    image = Image.open('seller.png')
                    image.close()
                    img = cv2.imread("seller.png")
                    # (h, w) = img.shape[:2]
                    # img = cv2.resize(img, (w * 3, h * 5))
                    # gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    # thr = cv2.threshold(gry, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                    #
                    # txt = pytesseract.image_to_string(thr)
                    # cv2.imwrite("seller2.png", thr)
                    #
                    # img3.close()
                    # print(txt)
                    text = str(image_to_string(
                        Image.open(r"seller.png"), lang='eng'))
                    sellertext = text.strip()
                    # sellerkey = sellertext.split("\n")[0]
                    # db.invoices.update_one({"keyword": keyword}, {
                    #     "$set": {"seller_key": sellerkey}})


                    st.header("Extracted Data\n")
                    boxoutputs = {
                        "Invoice Date: ": datetext.strip(),
                        "Invoice Number: ": invnotext.strip(),
                        "Invoice Amount: ": billtext.strip(),
                        "Invoice Buyer: ": buyertext.strip(),
                        "Invoice Seller: ": sellertext.strip(),
                    }
                    st.write(boxoutputs)




    with tab2:
        # placeholder = st.empty()

        # Replace the chart with several elements:
        # with placeholder.container():
            t2col1, t2col2 = st.columns([4, 2])
            with t2col1:
                # Get the uploaded file from the session state
                uploaded_file = st.session_state.get("uploaded_file")

                # Check if the file has been uploaded
                if uploaded_file is None:
                    file = st.file_uploader("Upload an invoice", type=["jpg", "jpeg", "png", "pdf", "tiff"])

                    if file is not None:

                        image = process_file(file)

                        st.image(image)
                        # extracting the text of the page1
                        fullinvoicetext = str(image_to_string(Image.fromarray(image), lang='eng'))

                        # check if a matching template exists with teh same keyword and keyword bounding boxes
                        for document in db.invoices.find():
                            img1 = Image.fromarray(image)
                            img3 = img1.crop((document["keyword_cordinates"]["x1"],
                                              document["keyword_cordinates"]["y1"],
                                              document["keyword_cordinates"]["x2"],
                                              document["keyword_cordinates"]["y2"]))

                            text = str(image_to_string(img3, lang='eng'))
                            text = text.strip()
                            foundregex = re.search(r'[a-zA-Z]+', text)
                            if (foundregex != None):
                                text = foundregex.group()
                            key = document["keyword"].strip()
                            if (text == key):
                                found = 1
                                total_amount = getinf(document)
                                matched_doc = document["keyword"].strip()
                                break

                        # matching every word of the pdf to every keyword to find the shift and confirming by matching with seller key
                        if (found == 0):
                            img = Image.fromarray(image)
                            data = image_to_data(img, output_type='dict')
                            boxes = len(data['level'])
                            for document in db.invoices.find():
                                for i in range(boxes):
                                    if data['text'][i].strip() != ''.strip():
                                        key_to_match = data['text'][i]
                                        foundregex = re.search(r'[a-zA-Z]+', key_to_match)

                                        # Checking only for valid strings
                                        if (foundregex != None):
                                            key_to_match = foundregex.group()

                                            # If keyword matches with a word in the pdf, get the x, y shift of teh keyword coordinates stored
                                        if ((key_to_match) == document["keyword"]):
                                            shiftx = data["left"][i] - \
                                                     document["keyword_cordinates"]["x1"]
                                            shifty = data["top"][i] - \
                                                     document["keyword_cordinates"]["y1"]
                                            shiftw = data["left"][i] - \
                                                     document["keyword_cordinates"]["x1"]
                                            shifth = data["top"][i] - \
                                                     document["keyword_cordinates"]["y1"]
                                            img1 = Image.fromarray(image)
                                            img1 = img1.crop((document["Seller"]["x1"] + shiftx,
                                                              document["Seller"]
                                                              ["y1"] + shifty,
                                                              document["Seller"]["x2"] + shiftw,
                                                              document["Seller"][
                                                                  "y2"] + shifth))
                                            img1.save('img2.png')
                                            img1.close()
                                            found = 1
                                            break

                                if (found == 1):
                                    matched_doc = document["keyword"].strip()
                                    total_amount = getinf(document)
                                    break

                        with t2col2:
                            if file is not None:
                                total_amount = total_amount.strip()
                                total_amount_3 = method3()

                                st.header("Extracted Data\n")
                                boxoutputs = {
                                    "Invoice Date: ": datetext.strip(),
                                    "Invoice Number: ": invnotext.strip(),
                                    "Invoice Amount: ": billtext.strip(),
                                    "Invoice Buyer: ": buyertext.strip(),
                                    "Invoice Seller: ": sellertext.strip(),
                                }
                                st.write(boxoutputs)
                                st.write("Regex Amount: ", regexbilltext)


                                ## ML Method
                                # if st.button("Extract through ML model"):
                                #
                                #     # st.title("InvoiceNet Demo")
                                #
                                #     # field = st.selectbox("Select field to extract",
                                #     #                      options=["Invoice Date", "Invoice Number"])
                                #
                                #     # if st.button("Run Prediction"):
                                #     #     invoice_file = st.file_uploader("Upload invoice file", type=["pdf"])
                                #     # if file:
                                #     #
                                #     #         # st.success("Prediction complete!")
                                #     #     # else:
                                #     #     #     st.error("Please upload an invoice file.")
                                #     #
                                #     # # cmd = 'python InvoiceNet/predict.py --field "Invoice Date" --invoice ' + '"./tempDir/' + file.name + '"'
                                #     # # os.system(cmd)
                                #     #     predict.run_prediction(field="Invoice Date", invoice=file,
                                #     #                    pred_dir='./predictions/')
                                #     #     with open('prediction.json') as f:
                                #     #         data = json.load(f)
                                #     #         datetext = data["Invoice Date"].strip()
                                #     #
                                #     # # cmd = 'python InvoiceNet/predict.py --field "Invoice Number" --invoice ' + '"./tempDir/' + file.name + '"'
                                #     # # os.system(cmd)
                                #     #     predict.run_prediction(field="Invoice Number", invoice=file,
                                #     #                        pred_dir='./predictions/')
                                #     #     with open('prediction.json') as f:
                                #     #         data = json.load(f)
                                #     #         invnotext = data["Invoice Number"].strip()
                                #     #
                                #     # # cmd = 'python InvoiceNet/predict.py --field "Invoice Amount" --invoice ' + '"./tempDir/' + file.name + '"'
                                #     # # os.system(cmd)
                                #     #     predict.run_prediction(field="Invoice Amount", invoice=file,
                                #     #                        pred_dir='./predictions/')
                                #     #     with open('prediction.json') as f:
                                #     #         data = json.load(f)
                                #     #         billtext = data["Invoice Amount"].strip()
                                #     #
                                #     # # cmd = 'python InvoiceNet/predict.py --field "Invoice Buyer" --invoice ' + '"./tempDir/' + file.name + '"'
                                #     # # os.system(cmd)
                                #     #     predict.run_prediction(field="Invoice Buyer", invoice=file,
                                #     #                        pred_dir='./predictions/')
                                #     #     with open('prediction.json') as f:
                                #     #         data = json.load(f)
                                #     #         buyertext = data["Invoice Buyer"].strip()
                                #     #
                                #     # # cmd = 'python InvoiceNet/predict.py --field "Invoice Seller" --invoice ' + '"./tempDir/' + file.name + '"'
                                #     # # os.system(cmd)
                                #     #     predict.run_prediction(field="Invoice Seller", invoice=file,
                                #     #                        pred_dir='./predictions/')
                                #     #     with open('prediction.json') as f:
                                #     #         data = json.load(f)
                                #     #         sellertext = data["Invoice Seller"].strip()
                                #     #
                                #     # st.header("ML model Extracted Data\n")
                                #     # mloutputs = {"Invoice Date: ": datetext.strip(),
                                #     #              "Invoice Number: ": invnotext.strip(),
                                #     #              "Invoice Amount: ": billtext.strip(),
                                #     #              "Invoice Buyer: ": buyertext.strip(),
                                #     #              "Invoice Seller: ": sellertext.strip(),
                                #     #              }
                                #     # st.write(mloutputs)
                                #
                                #
                                #     # Predictions for different fields
                                #     fields = ["Invoice Date", "Invoice Number", "Invoice Amount", "Invoice Buyer",
                                #               "Invoice Seller"]
                                #     predictions = {}
                                #     for field in fields:
                                #         predict.run_prediction(field=field, invoice="", pred_dir='./predictions/')
                                #         with open('prediction.json') as f:
                                #             data = json.load(f)
                                #             predictions[field] = data[field].strip()
                                #
                                #     # Display the predictions
                                #     st.header("ML model Extracted Data\n")
                                #     mloutputs = {"Invoice Date: ": predictions["Invoice Date"],
                                #                  "Invoice Number: ": predictions["Invoice Number"],
                                #                  "Invoice Amount: ": predictions["Invoice Amount"],
                                #                  "Invoice Buyer: ": predictions["Invoice Buyer"],
                                #                  "Invoice Seller: ": predictions["Invoice Seller"]}
                                #     st.write(mloutputs)
                                #
                                #     ### final output
                                #     if boxoutputs["Invoice Date: "] == mloutputs["Invoice Date: "]:
                                #         st.write(boxoutputs["Invoice Date: "])
                                #         temp1 = boxoutputs["Invoice Date: "]
                                #     else:
                                #         st.selectbox("Date", (
                                #         boxoutputs["Invoice Date: "], mloutputs["Invoice Date: "],
                                #         "Input Manually"))
                                #         temp1 = "Input Manually"
                                #     if boxoutputs["Invoice Number: "] == mloutputs[
                                #         "Invoice Number: "]:
                                #         st.write(boxoutputs["Invoice Number: "])
                                #     else:
                                #         st.selectbox("Number", (boxoutputs["Invoice Number: "],
                                #                                 mloutputs["Invoice Number: "],
                                #                                 "Input Manually"))
                                #
                                #     if boxoutputs["Invoice Amount: "] == mloutputs[
                                #         "Invoice Amount: "]:
                                #         st.write(boxoutputs["Invoice Amount: "])
                                #     else:
                                #         st.selectbox("Amount", (boxoutputs["Invoice Amount: "],
                                #                                 mloutputs["Invoice Amount: "],
                                #                                 "Input Manually"))
                                #
                                #     if boxoutputs["Invoice Buyer: "] == mloutputs[
                                #         "Invoice Buyer: "]:
                                #         st.write(boxoutputs["Invoice Buyer: "])
                                #     else:
                                #         st.selectbox("Buyer", (
                                #         boxoutputs["Invoice Buyer: "], mloutputs["Invoice Buyer: "],
                                #         "Input Manually"))
                                #
                                #     if boxoutputs["Invoice Seller: "] == mloutputs[
                                #         "Invoice Seller: "]:
                                #         st.write(boxoutputs["Invoice Seller: "])
                                #     else:
                                #         st.selectbox("Seller", (boxoutputs["Invoice Seller: "],
                                #                                 mloutputs["Invoice Seller: "],
                                #                                 "Input Manually"))
                                #     if st.button("Finalise"):
                                #         if temp1 == "Input Manually":
                                #             st.selectbox()

    with tab3:
        st.header("An owl")
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)

    with tab4:
        st.header("A dog")
        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
