import fitz
from PIL import Image, ImageOps, ImageTk, ImageDraw
import io
import tkinter as tk
from tkinter import filedialog
from chess_parsing import FEN_to_words


def prompt_for_caption(page_image, current_image, rects, current_index, master):
    """Displays a page with image and prompts for me to manually caption"""
    caption = ""  
    FEN_input = ""

    def on_submit():
        nonlocal caption  
        nonlocal FEN_input
        caption = caption_text.get("1.0", tk.END).strip()
        FEN_input = FEN_text.get("1.0", tk.END).strip()
        caption_window.quit()

    def save_image():
        """Save the currently focused image to a file."""
        filetype = [('PNG files', '*.png'), ('All files', '*.*')]
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetype, parent=caption_window)
        if filename:
            current_image.save(filename)

    caption_window = tk.Toplevel(master)
    caption_window.title("Add Caption")

    photo = ImageTk.PhotoImage(page_image)

    frame = tk.Frame(caption_window)
    frame.pack(fill='both', expand=True, padx=5, pady=5)

    canvas = tk.Canvas(frame, width=page_image.width, height=page_image.height)
    canvas.create_image(0, 0, anchor='nw', image=photo)
    canvas.grid(row=0, column=0, rowspan=4)

    # draw blue rectangles around the text boxes and images
    dr = ImageDraw.Draw(page_image)
    for index, rect in enumerate(rects):
        dr.rectangle([rect.x0, rect.y0, rect.x1, rect.y1], outline="blue", width=2)

    # draw red rectangle around current image
    current_rect = rects[current_index]
    dr.rectangle([current_rect.x0, current_rect.y0, current_rect.x1, current_rect.y1], outline="red", width=2)

    photo = ImageTk.PhotoImage(page_image)
    canvas.create_image(0, 0, anchor='nw', image=photo)

    # box to enter caption
    caption_label = tk.Label(frame, text="Enter Caption:")
    caption_label.grid(row=0, column=1, sticky='nw', padx=5)
    caption_text = tk.Text(frame, width=40, height=5)
    caption_text.grid(row=0, column=1, sticky='nw', padx=5, pady=(0, 5))  # Reduce vertical space
    caption_text.focus_set()

    # box to directly enter FEN if image is of chess position
    fen_label = tk.Label(frame, text="Enter FEN:")
    fen_label.grid(row=2, column=1, sticky='nw', padx=5)
    FEN_text = tk.Text(frame, width=40, height=5)
    FEN_text.grid(row=3, column=1, sticky='nw', padx=5, pady=(0, 5))

    # button for submitting each caption
    submit_button = tk.Button(frame, text="Submit", command=on_submit)
    submit_button.grid(row=1, column=1, sticky='nw', padx=5, pady=(0, 5))  # Position close to entry

    # save button
    save_button = tk.Button(frame, text="Save Image", command=save_image)
    save_button.grid(row=1, column=2, sticky='nw', padx=5, pady=(0, 5))

    # display current image larger on the side
    photo_current = ImageTk.PhotoImage(current_image)
    img_label = tk.Label(frame, image=photo_current)
    img_label.grid(row=2, column=1, sticky='nw', padx=5, pady=(0, 5))  # Reduce vertical space

    caption_window.bind('<Return>', lambda event: on_submit())

    caption_window.mainloop()
    caption_window.destroy()

    if caption == "" and FEN_input == "":
        return ""
    elif FEN_input == "":
        return f'[Image caption: {caption}]'
    print(FEN_input)
    print(FEN_to_words(FEN_input))
    return f'[Image caption: {caption}. Chessboard with FEN: {FEN_input}. Therefore, {FEN_to_words(FEN_input)}]'


def review_text_content(master, page_image, content_positions):
    """Displays the page alongside content for verification before adding to the file."""
    review_window = tk.Toplevel(master)
    review_window.title("Review and Verify")

    frame = tk.Frame(review_window)
    frame.pack(fill='both', expand=True, padx=5, pady=5)

    # display the page of the PDF as image
    photo = ImageTk.PhotoImage(page_image)
    canvas = tk.Canvas(frame, width=page_image.width, height=page_image.height)
    canvas.create_image(0, 0, anchor='nw', image=photo)
    canvas.grid(row=0, column=0, rowspan=10)

    def on_verify():
        review_window.quit()
    
    review_text = tk.Text(frame, width=40, height=20)
    for content, _, _ in content_positions:
        if content.strip():
            review_text.insert(tk.END, content + "\n")
    review_text.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

    # verify button to verify the current page's text is good
    verify_button = tk.Button(frame, text="Verify", command=on_verify)
    verify_button.grid(row=1, column=1, sticky='n')

    review_window.mainloop()

    edited_content_list = [line.strip() for line in review_text.get("1.0", tk.END).splitlines() if line.strip()]

    review_window.destroy()

    return edited_content_list


def extract_text_with_captions(pdf_path, output_text_path):
    document = fitz.open(pdf_path)

    master = tk.Tk()
    master.withdraw()

    with open(output_text_path, 'a', encoding='utf-8') as f:
        for page_number in range(len(document)):
            page = document.load_page(page_number)
            text_blocks = page.get_text("blocks")

            pix = page.get_pixmap()

            page_image = Image.open(io.BytesIO(pix.tobytes()))

            images = page.get_images(full=True)

            content_positions = []
            rects = []

            # extract the positions of each text block from the PDF page
            for block_index, block in enumerate(text_blocks):
                text = block[4].strip()  # Extract text content
                rect = fitz.Rect(block[:4])  # Get bounding box for text
                print(f"Text block {block_index}: {text[:30]}... at y0 = {rect.y0}")
                content_positions.append((text, rect.y0, rect.x0))
                rects.append(rect)

            # extract positions of each image on the page
            for img_index, img_meta in enumerate(images):
                xref = img_meta[0]
                base_image = document.extract_image(xref)
                img_bytes = base_image['image']
                image = Image.open(io.BytesIO(img_bytes))

                # get outer rectangle of image to highlight
                img_rect = page.get_image_rects(xref)
                if img_rect:
                    rect = img_rect[0]
                    rects.append(rect)

                    bbox_x0, bbox_y0 = rect.x0, rect.y0
                    bbox_x1, bbox_y1 = rect.x1, rect.y1

                    # draw rectangle around image
                    dr = ImageDraw.Draw(page_image)
                    dr.rectangle([bbox_x0, bbox_y0, bbox_x1, bbox_y1], outline="red", width=2)

                    # display image and prompt for caption
                    caption = prompt_for_caption(page_image, image, rects, len(rects) - 1, master)
                    
                    content_positions.append((caption, bbox_y0, bbox_x0))

            # sort content on page by vertical then horizontal positions so content is added in correct order
            content_positions.sort(key=lambda x: (x[1], x[2]))

            edited_contents = review_text_content(master, page_image, content_positions)

            # add the content to text file
            for content in edited_contents:
                if content.strip():
                    f.write(content + "\n")
                    f.flush()

    print("Text extraction and image captioning complete.")
    master.destroy()



name = "algebraic_notation_bsa"
pdf_path = f"text_pdfs/{name}.pdf"
output_text_path = f"text_files/{name}1.txt"
extract_text_with_captions(pdf_path, output_text_path)
