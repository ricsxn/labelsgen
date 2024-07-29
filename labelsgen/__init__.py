from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
import argparse
import json
import qrcode
import os
import sys
import webbrowser



def qr_draw(c, q, qs, x, y):
    qr_size = int(qs * inch)
    # Create a QR code with adjusted box_size for proper scaling
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=qr_size,
        border=1,
    )
    qr.add_data(q, optimize=False)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Draw the QR code image on the canvas
    c.drawInlineImage(qr_img, x, y, width=qr_size, height=qr_size)


def qr_page(n, c, q, tl, tb, tr):
    # Create a QR code with adjusted box_size for proper scaling
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=20,
        border=3,
    )
    qr.add_data(q, optimize=False)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Calculate the positioning of the QR code to center it within the page
    qr_size = config['qr_size'] * inch  # Adjust as needed
    qr_x = (inch - qr_size) / 2
    qr_y = (inch - qr_size) / 2

    # Draw the QR code image on the canvas
    c.drawInlineImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # Set the position for the left text
    text_left_x = inch * config['text_left_x']  # Adjust as needed
    text_left_y = inch / 2

    # Set the position for the bottom text
    text_bottom_x = inch / 2
    text_bottom_y = inch * config['text_bottom_y']  # Adjust as needed

    # Prepare text output
    c.setFont(config['font'], config['font_size'])
    c.rotate(90)
    # Draw left and bottom text on the PDF
    if(tl is not None and len(tl) > 0):
        c.drawCentredString(text_left_y, -text_left_x, tl)
    if(tr is not None and len(tr) > 0):
        # Set the position for the bottom text
        text_right_x = inch * config['text_right_x']
        text_right_y = inch / 2  # Adjust as needed
        c.drawCentredString(text_right_y, -text_right_x, tr)
    if(tb is not None and len(tb) > 0):
        c.rotate(-90)
        c.drawCentredString(text_bottom_x, text_bottom_y, tb)


def make_canvas(pdf_file, page_size):
    if page_size is None:
        page_width = int(pages[config['page']][0] * inch)
        page_heigth = int(pages[config['page']][1] * inch)
    else:
        page_width = int(page_size[0] * inch)
        page_heigth = int(page_size[1] * inch)

    return canvas.Canvas(pdf_file, pagesize=(page_width, page_heigth))


def generate_labels(starting_number, num_labels):
    pdf_file = config['sequence_labels']
    c = make_canvas(pdf_file, None)

    for n in range(starting_number, starting_number + num_labels):
        qr_data = f"{config['qr_url_prefix']}{config['qr_url_product_prefix']}{n}"
        qr_bottom_text = f"{config['qr_url_product_prefix']}{n}"
        qr_right_text = f"{n}"

        qr_page(n, c, qr_data, None , qr_bottom_text, qr_right_text)
        c.showPage()

    c.save()
    print(f"Generated {n-starting_number+1} labels and saved to: '{pdf_file}'")
    return pdf_file


def generate_file_labels(upi_file):
    pdf_file = config['file_labels']
    c = make_canvas(pdf_file, None)
    try:
        with open(upi_file) as f:
            n = 1
            for upi_file_record in f:
                pserial = ''
                upi_record = upi_file_record.split()
                if len(upi_record) > 1:
                    pserial = upi_record[1]
                upi = upi_record[0]
                if len(upi) > 1:
                    upi = upi.strip()
                    ver_n_serial = ''
                    upi_parts = upi.split('/')
                    if len(upi_parts) >=3:
                        ver_n_serial = upi_parts[2]
                    qr_page(n, c, f'{config['qr_url_product_prefix']}{upi}', ver_n_serial, upi, pserial)
                    c.showPage()
                    n+=1
    except IOError as e:
        print(f"Unable to process UPI file: '{upi_file}'")
        sys.exit(1)

    c.save()
    print(f"Generated {n-1} labels and saved to: '{pdf_file}'")
    return pdf_file


def show_usage():
    cmd = os.path.basename(sys.argv[0])
    print(
f"""This utility creates a PDF file containing label pages including products QR codes 
    Usage: {cmd} <first_product_number> [number_of_products=1]
                 -v
                 -f <file_labels>
                 -s <schema_labels>
                 -h|--help show this page

    Where:
      -v open the generated QR labels file
      'file_labels' is a text file containing a single product data and optionally a text placed on the right side
      'schema_labels' file containing the description of the labels to generate

    The utility can be configured changing the 'labelsgen_conf.json' file
"""
    )


def json_load(json_path):
    with open(json_path, 'r') as file:
        json_data = json.load(file)
    return json_data


def schema_drawing(schema_json):
    page_size = (pages[schema_json['page']][0],
                 pages[schema_json['page']][1])
    schemas = schema_json['pages']
    pdf_file = config['schema_labels']
    c = make_canvas(pdf_file, page_size)
    p = 0
    n = 0
    try:
        for schema in schemas:
            print(f"Processing page {p+1}")
            for key, value in schema.items():
                print(f"  element: '{key}':")
                type = value['type']
                if(type == 'label'):
                    text = value['text']
                    font = value['font']
                    font_size = value['font_size']
                    x = value['x'] * inch
                    y = value['y'] * inch
                    rotation = value.get('rotation', 0)
                    print(f"    Drawing text '{text}' at ({y}, {x})")
                    c.setFont(font, font_size)
                    if rotation != 0:
                        c.saveState()
                        c.translate(x, y)
                        c.rotate(rotation)
                        x = y = 0
                    c.drawCentredString(x, y, text)
                    if rotation != 0:
                        c.restoreState()
                    n = n + 1
                elif(type == 'qr'):
                    text = value['text']
                    qr_size = value['qr_size']
                    x = value['x'] * inch - (qr_size * inch/2)
                    y = value['y'] * inch - (qr_size * inch/2)
                    print(f"    Drawing QR '{text}' at ({y}, {x})")
                    qr_draw(c, text, qr_size, x, y)
                elif(type == 'image'):
                    path = value['path']
                    width = value['width'] * inch
                    height = value['height'] * inch
                    x = value['x'] * inch - (width/2)
                    y = value['y'] * inch - (height/2)
                    c.drawImage(path, x, y, width, height, preserveAspectRatio=True)
                else:
                    print(f"Skipping unknown element type: '{type}' at ({x},{y})")
            c.showPage()
            p = p + 1
    except IOError as e:
        print(f"Unable to process schema file: '{schema}'")
        sys.exit(1)

    c.save()
    print(f"Generated {p} pages made of {n} elements and saved to: '{pdf_file}'")
    return pdf_file


def load_pages():
    pages = {}
    for page in config['pages']:
        pages[page['name']] = (page['width'], page['height'])
    return pages

# Load qrcode configuration file
config = json_load('labelsgen_conf.json')
view_pdf = False
pages = load_pages()

def main():
    pdf_files = []

    parser = argparse.ArgumentParser(description='Command line tool to create PDF files containing label pages including products QR codes', add_help=False)
    parser.add_argument('first_product_number', nargs='?', type=int, help='The first product number (integers only)')
    parser.add_argument('number_of_products', nargs='?', type=int, default=1, help='The number of products (default is 1)')
    parser.add_argument('-v', '--view', action='store_true', help='Open the generated QR labels file')
    parser.add_argument('-f', '--file', help='Generate labels taking data from a file')
    parser.add_argument('-s', '--schema', help='Generate lables from a specified schema file')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    args = parser.parse_args()

    if  len(sys.argv) == 1 or args.help:
        show_usage()
        sys.exit(0)

    view_pdf = args.view

    if args.file:
        pdf_files.append(generate_file_labels(args.file))

    if args.schema:
        schema = json_load(args.schema)
        pdf_files.append(schema_drawing(schema))

    if args.first_product_number is not None:
        num_labels = 1
        starting_number = args.first_product_number
        if args.number_of_products is not None:
            num_labels = args.number_of_products
        pdf_files.append(generate_labels(starting_number, num_labels))

    if view_pdf and len(pdf_files) > 0:
        for pdf_file in pdf_files:
            webbrowser.open('file://' + os.path.realpath(pdf_file))

    sys.exit(0)


if __name__ == "__main__":
    main()

