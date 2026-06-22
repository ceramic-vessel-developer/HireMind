import pdfplumber

def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
              text += f"\n{page_text}"
        return text

if __name__ =="__main__":
    print(extract_text(r"C:\Users\kacper\PycharmProjects\HireMind\backend\src\cv.pdf"))