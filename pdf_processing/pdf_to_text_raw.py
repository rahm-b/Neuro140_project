import fitz  # PyMuPDF

def pdf_to_text(pdf_path, txt_path):

    # open the PDF file
    doc = fitz.open(pdf_path)
    
    # extract text from all pages
    all_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        all_text += page.get_text()
    
    # write the extracted text to text file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"Successful, saved to '{txt_path}'")


name = "think_like_grandmaster_chess"  # I changed the name for each PDF file I was processing
pdf_path = f"text_pdfs/{name}.pdf"
output_text_path = f"text_files/{name}.txt"
pdf_to_text(pdf_path, output_text_path)
