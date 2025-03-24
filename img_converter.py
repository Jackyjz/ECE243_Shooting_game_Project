import numpy as np
import cv2
import pyperclip

def convert_img(file_name, img_name, width, height):
    img = cv2.imread(file_name, cv2.IMREAD_UNCHANGED)  # Preserve alpha if present

    if img.shape[2] == 4:
        # Has alpha channel
        b, g, r, a = cv2.split(img)
        alpha_mask = a > 0
        img = cv2.merge((b, g, r))  # Drop alpha for RGB processing
    else:
        # No alpha: consider pure black (0,0,0) as transparent
        alpha_mask = ~(np.all(img == [0, 0, 0], axis=-1))

    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_NEAREST)
    alpha_mask = cv2.resize(alpha_mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST).astype(bool)

    img = img.astype(np.uint16)
    img_r = img[:, :, 2] >> 3
    img_g = img[:, :, 1] >> 2
    img_b = img[:, :, 0] >> 3
    img_rgb565 = (img_r << 11) + (img_g << 5) + img_b

    # Set transparent background pixels to a magic value (e.g., 0xDEAD)
    img_rgb565[~alpha_mask] = 0xDEAD

    img_flat = img_rgb565.flatten()
    img_array = ', '.join(f"0x{x:04X}" for x in img_flat)
    output_code = f"short unsigned int {img_name}[{width * height}] = {{{img_array}}};"
    output_code += "\n\n" + generate_draw_pixel_code(img_name, width, height)
    pyperclip.copy(output_code)
    print("C array copied to clipboard.")


def generate_draw_pixel_code(img_name, width, height):
    return f"""
void plot_image_{img_name}(int x, int y) {{
    for (int i = 0; i < {height}; i++) {{
        for (int j = 0; j < {width}; j++) {{
            unsigned short color = {img_name}[i * {width} + j];
            if (color != 0xDEAD)  // Skip transparent
                plot_pixel(x + j, y + i, color);
        }}
    }}
}}

void erase_image_{img_name}(int x, int y) {{
    for (int i = 0; i < {height}; i++) {{
        for (int j = 0; j < {width}; j++) {{
            if ({img_name}[i * {width} + j] != 0xDEAD)
                plot_pixel(x + j, y + i, 0);
        }}
    }}
}}
"""

if __name__ == '__main__':
    convert_img(
        file_name=r'bg.png',
        img_name='bg',
        width=320,
        height=240
    )
