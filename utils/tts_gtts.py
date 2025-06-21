








import os
import re
import requests
from urllib.parse import quote

MAX_WORDS_LENGTH = 199


def split_under_199_letters(text):

    result = []
    index = 0
    
    while index < len(text):
        end_index = index + MAX_WORDS_LENGTH
        
        if end_index < len(text) and re.match(r'\S', text[end_index]):
            while end_index > index and re.match(r'\S', text[end_index]):
                end_index -= 1
        
        result.append(text[index:end_index])
        
        index = end_index
        
        while index < len(text) and re.match(r'\s', text[index]):
            index += 1
    
    return result


def convert_any_text_to_audio(text, language, full_path_with_filename):

    arr_strings = split_under_199_letters(text)
    print(f"Try to convert arr_strings in length: {len(arr_strings)} ..")
    
    directory = os.path.dirname(full_path_with_filename)
    
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f'Directory created: {directory}')
    
    output_file = f"{full_path_with_filename}.mp3"
    
    with open(output_file, 'wb') as file:
        for i, chunk in enumerate(arr_strings):
            encoded_text = quote(chunk)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={language}&q={encoded_text}"
            
            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
                try:
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        file.write(response.content)
                        break
                    else:
                        raise Exception(f"Server responded with status {response.status_code}")
                        
                except Exception as error:
                    attempts += 1
                    if attempts >= max_attempts:
                        break
    
    print('text to audio from gtts done !')


