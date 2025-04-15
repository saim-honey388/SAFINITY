from PIL import Image, ImageDraw
import os

def create_fallback_flag():
    # Create a new image with a white background
    width = 80
    height = 50
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a simple flag-like pattern
    draw.rectangle([0, 0, width-1, height-1], outline='gray')
    draw.line([0, height//2, width, height//2], fill='gray', width=1)
    draw.line([width//3, 0, width//3, height], fill='gray', width=1)
    
    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'fallback_flag.png')
    image.save(output_path)
    print(f"Created fallback flag at: {output_path}")

if __name__ == '__main__':
    create_fallback_flag()