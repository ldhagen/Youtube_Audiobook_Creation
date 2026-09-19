import os
import re

import os
import re

def split_text(file_path, target_word_count=8500):
    with open(file_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Find the end of the TOC. 
    # Usually, the TOC ends and then there's a large gap before the first BOOK or CHAPTER.
    # We'll look for the FIRST occurrence of "BOOK ONE: 1805" that is followed by actual content, 
    # or just find the SECOND occurrence of "BOOK ONE: 1805".
    all_book_ones = list(re.finditer(r'BOOK ONE: 1805', full_content))
    if len(all_book_ones) > 1:
        content_start = all_book_ones[1].start()
    else:
        # Fallback: look for a large gap or a specific pattern
        content_start = full_content.find('*** START')
        if content_start == -1: content_start = 0

    content = full_content[content_start:]

    # Find all chapter/book markers in the actual content
    # Headers in the text are usually capitalized and on their own line
    # Pattern: newline, optional space, BOOK/CHAPTER/EPILOGUE, then something, then two or more newlines
    marker_pattern = r'\n\s*(BOOK|CHAPTER|FIRST EPILOGUE|SECOND EPILOGUE) [IVXLCDM0-9 :\-]+\n'
    markers = list(re.finditer(marker_pattern, content))
    
    segments = []
    current_start = 0
    current_word_count = 0
    
    for i in range(len(markers)):
        marker = markers[i]
        # Calculate words in the section before this marker
        section_text = content[current_start:marker.start()]
        section_words = len(section_text.split())
        
        # We split if we've reached the target word count AND we are at a marker
        if current_word_count + section_words > target_word_count and current_word_count > 0:
            segments.append(content[current_start:marker.start()])
            current_start = marker.start()
            current_word_count = 0
        
        current_word_count += section_words

    # Add the last segment
    segments.append(content[current_start:])
    
    return segments

def clean_segment(text):
    # Join lines to avoid pauses at newlines, but keep double newlines for paragraph breaks
    # First, replace single newlines with spaces
    # We can do this by looking for single \n that aren't preceded or followed by another \n
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def main():
    input_file = 'warandpeace.txt'
    output_dir = 'war_and_peace_segments'
    os.makedirs(output_dir, exist_ok=True)
    
    segments = split_text(input_file)
    print(f"Split into {len(segments)} segments.")
    
    for i, segment in enumerate(segments):
        cleaned = clean_segment(segment)
        output_path = os.path.join(output_dir, f'segment_{i+1:03d}.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Wrote {output_path}")

if __name__ == "__main__":
    main()
