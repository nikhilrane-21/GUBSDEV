## Data extractor for PDF invoices 


INSTRUCTIONS TO RUN:

USAGE:

Python version: Python 3.10.8

For Windows:
1. Download tesseract exe from https://github.com/UB-Mannheim/tesseract/wiki.
Direct link for the tesseract binary : https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.2.0.20220712.exe

2. Install this exe in `C:\Program Files\Tesseract-OCR`

3. OR

4. To make tesseract work, put in the exact path of tesseract in `pytesseract.tesseract_cmd` in file `script_withoutdb.py` line no. 275.

5. Download `'cmake'` from https://cmake.org/download/  

6. Add the `C:\Program Files\CMake\bin` path to systems' environment variables path.

For Ubuntu:
1. Just install packages from packages.txt


Steps to run project:
1. Create the Virtual environment : `python -m venv env`

2. Enable Environment : `.\env\Scripts\activate`

3. Install all the required dependencies : `pip install -r requirementsite.txt`

4. Run the streamlit server: `streamlit run ite.py`


The algorithm uses 3 methods:

**Bounding Boxes:** In this bounding boxes are selected for desired fields that re keyword, Date of Invoice, Invoice No. Total Bill Amount, Buyer Address and Seller Address in the same order. To select a bounding box , click on the left most corner and then hold the mouse button and drag till the rightmost bottom corner. Then release the mouse button.The x and y coordinates for the topleft and bottomright corners are stored in rhe database mapped with their keywords. The next time an invoice is fed into the system, it searches for the matching keyword and if it finds it then it uses the already stored x y coordinates to extract the required fields. If the system is unable to match the keyword it, we have to onboard a new template for that invoice.

The keyword is matched in the following way, 
1. First for every document in the database we check that if in the rectangle bounded by the keyword coordinates eact same keyword is present, if yes the thenkeyword is found.
2. Otherwise every word of the pdf is checked against every keyword present in the database, if a word of the pdf matches with any of the leywords the the first line of the seller address is matched to confirm for the template. If found the that tempalte is considered, otherwise onboarding mode is set on.


**Invoice Net Training Data:** In this method we use pretrained models to predict the total amount from the bill.

**Regex Method:** In this method, part 1 the document matched in part 1 is used. This first extracts the text of the whole pdf and then tries to match the word just after and before the total bill, if these words are matched in the template and the document then the text between that is returned as the total amount.Code for this is contained in method3()


To run the code:

1. Use the command:  
   `streamlit run ite.py`
2. Streamlit webapp will be initialised and will be available at the generated url on CMD
2. A webpage will open login with ID PASS, upload invoice, if the invoice template has not been added before. Select the rectangles in given manner by dragging with help of mouse and when 6 boxes are selected button will be generated to extract data
3. Click Extract Data button and the text will be showed on the webapp.
4. And if the template was added earlier and a document can be matched, the extracted fields are shown in the webapp.
5. Then after method 1 is run and the onboarding mode is not on, the total amount is extracted by method 2. This total amount is returned.
6. After this, method 3 is executed and if the total amount extracted form part 3 id valid it is returned else -1 is returned.

If the pretrained model is not present, first prepare and train the model for method 2.
<br>Use the following commands for this:
<br>1. `python InvoiceNet/prepare_data.py --data_dir InvoiceNet/train_data5/`
<br>2. `python InvoiceNet/train.py --field "Invoice Date" --batch_size 2`

Refer to InvoiceNet documention for more details about part2.


