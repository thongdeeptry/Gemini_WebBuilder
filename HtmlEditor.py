import re
import json
# Function to extract HTML code
def html_extractor(html_string):
    pattern = r'<!DOCTYPE html>[\s\S]*?</html>'
    matches = re.findall(pattern, html_string, re.IGNORECASE)
    if matches:
        return matches[0]
    else:
        return "No HTML content found."

# Function to remove HTML tags
def html_remover(html_string):
    # Remove inline CSS
    clean_css = re.compile('<style.*?>.*?</style>', re.DOTALL)
    html_string = re.sub(clean_css, '', html_string)

    # Remove JavaScript
    clean_js = re.compile('<script.*?>.*?</script>', re.DOTALL)
    html_string = re.sub(clean_js, '', html_string)

    # Remove HTML tags
    clean_html = re.compile('<.*?>')
    cleaned_text = re.sub(clean_html, '', html_string)

    # Remove remaining CSS within HTML attributes
    cleaned_text = re.sub(r'\s?style=("|\').*?("|\')', '', cleaned_text)
    cleaned_text = cleaned_text.replace('```',"")
    return cleaned_text

def beautify_AiResponse(response):
    # Convert **text** to <h2>text</h2>
    response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)
    
    # Convert numbered lists into <ol>...</ol>
    response = re.sub(r'(\d+)\.\s(.*?)(?=(?:\d+\.|\n\n|$))', r'<li>\2</li>', response)
    response = re.sub(r'(<li>.*?</li>)', r'<ol>\1</ol>', response)

    # Convert - text into <li>text</li> and wrap them in <ul>...</ul>
    response = re.sub(r'- (.*?)(?=(?:- |$))', r'<li>\1</li>', response)
    response = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', response)

    # Replace newline with <br> for better formatting
    response = response.replace('\n', '<br>')
    
    return response

def loadJson(response):
    data = []
    try:
        # Find the start and end of the JSON-like content
        start = response.find('<json:') + len('<json:')
        end = response.find('/>', start)
        
        # Extract the JSON-like content
        json_str = response[start:end].strip()
        data = json.loads(json_str)
    except :
        # Find the start and end of the JSON-like content
        start = response.find('```json:') + len('<json:')
        end = response.find('```', start)
        
        # Extract the JSON-like content
        json_str = response[start:end].strip()
        data = json.loads(json_str)
    return data



def compile_html(html_content,projectName):
    try:
        # Regular expressions
        boilerplate_pattern = re.compile(r"<!DOCTYPE html>.*?<body.*?>|</body>\s*</html>", re.DOTALL)
        body_pattern = re.compile(r"<body.*?>(.*?)</body>", re.DOTALL)
        style_pattern = re.compile(r"<style.*?>(.*?)</style>", re.DOTALL)
        
        # Initialize results
        pure_html = ""
        css_content = []

        # Check if the boilerplate is present
        boilerplate_detected = re.search(boilerplate_pattern, html_content)

        if boilerplate_detected:
            # Remove the boilerplate (DOCTYPE, <html>, <head>, <body> tags)
            clean_html_content = boilerplate_pattern.sub('', html_content)
            
            # Extract content inside the <body> tags
            body_content_match = body_pattern.search(clean_html_content)
            if body_content_match:
                body_content = body_content_match.group(1)
            else:
                body_content = clean_html_content
            
            # Extract all <style> blocks within the body content
            style_blocks = style_pattern.findall(body_content)
            
            # Remove the <style> tags and their content from the body content
            pure_html = style_pattern.sub('', body_content).strip()

            # Collect CSS content
            css_content.extend(style_blocks)

        else:
            # Extract all <style> blocks within the HTML content
            style_blocks = style_pattern.findall(html_content)
            
            # Remove the <style> tags and their content from the HTML content
            pure_html = style_pattern.sub('', html_content).strip()
            
            # Collect CSS content
            css_content.extend(style_blocks)
        
        # Compile the final HTML structure
        final_html = "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        final_html += "<meta charset='UTF-8'>\n<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        final_html += f"<title>{projectName}</title>\n"

        # Add the extracted CSS
        if css_content:
            final_html += "<style>\n"
            for css in css_content:
                final_html += css.strip() + "\n"
            final_html += "</style>\n"
        
        final_html += "</head>\n<body>\n"
        final_html += pure_html
        final_html += "\n</body>\n</html>"

        return final_html

    except Exception as e:
        return f"An error occurred: {str(e)}"
