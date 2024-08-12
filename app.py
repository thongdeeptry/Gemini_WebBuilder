from flask import Flask, request, render_template, jsonify , send_from_directory
from werkzeug.utils import safe_join
import google.generativeai as genai
from HtmlEditor import  html_remover, beautify_AiResponse, loadJson, compile_html
import OrderManegment
from prompts.prompt import SYSTEM_PROMPT_FOR_GEMINI , SYSTEM_PROMPT_FOR_TASK_GENERATOR
import os
import shutil

#Decaliring Some vairibals
ProjectName = ''
page = ''
block = ''
code = ''
# Configure the Generative AI API

genai.configure(api_key="AIzaSyDu9bedhof9Bw92l4jMoTqXEfAgiMgQ5Mk")


app = Flask(__name__)
system_prompt=""""""
# Initialize the Generative AI chat model with initial instructions
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
convo = model.start_chat(history=[
    {"role": "user", "parts": [SYSTEM_PROMPT_FOR_GEMINI]},
    {"role": "model", "parts": ["ok sir, I will do my best to help you with this task."]},
])
taskGenartor = model.start_chat(history=[
    {"role": "user", "parts": [SYSTEM_PROMPT_FOR_TASK_GENERATOR]},
    {"role": "model", "parts": ["ok sir, I will do my best to help you with this task."]},
])
# sp.run("powershell", shell=False
# Route for the homepage
@app.route("/webBuilder")
def webBuilder():
    return render_template("webBuilder.html")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/projectName")
def projectName():
    return jsonify({"ProjectName":ProjectName})

@app.route("/title" , methods=["POST"])
def settitle():
    global ProjectName
    title = request.get_json().get("title")
    # print(request.data)
    ProjectName = title
    if not ProjectName:
        return "False"
    if not os.path.exists(f"./Projects/{ProjectName}"):
        print("yes")
        if not os.path.exists(f"./Projects"):
            os.mkdir("./Projects")
        os.mkdir(f"./Projects/{ProjectName}")
        os.mkdir(f"./Projects/{ProjectName}/bloksData")
    convo.send_message(f"system: user named his Project : {title}")
    print(ProjectName)
    return "True"
# Route for the preview page
@app.route("/preview")
def preview():
    Content = ""
    try:
        with open("./templates/preview.html", "w", encoding='utf-8', errors='ignore') as f:
            f.write(compile_html(Content))
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document</title>
</head>
<body>
  
</body>
</html>
""")
        if not ProjectName or not page:
            return render_template("preview.html")
        page_path = f"./Projects/{ProjectName}/pages/{page}/"
        if not os.path.exists(page_path):
            return render_template("preview.html")
        
        # Read all blocks and concatenate their content
        for block in os.listdir(page_path):
            block_path = os.path.join(page_path, block)
            with open(block_path, "r", encoding='utf-8', errors='ignore') as blok:
                Content += blok.read()
        
        # Write the concatenated content to the preview file
        with open("./templates/preview.html", "w", encoding='utf-8', errors='ignore') as f:
            f.write(compile_html(Content,ProjectName))
        
        return render_template("preview.html")
    except Exception as e:
        # Log the error and return a simple preview page
        print(f"Error in preview route: {str(e)}")
        return render_template("preview.html")

# Route to generate HTML content based on user input
@app.route("/generate", methods=["POST"])
def generate():
    global code
    question = request.get_json().get("question")
    current_code = request.get_json().get("code")
    code=current_code
    print(question)
    html_content = ""
    # Return error if no question is provided
    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Send the question to the AI model
    taskGenartor.send_message(question)
    task=f"user: {question}, /n current_code_in-editor:{current_code} , /n taskGenartor: {taskGenartor.last.text}"
    print(task)
    convo.send_message(task)
    response = convo.last.text
    if "```json" in response:
        convo.send_message("system: Use <json: /> insted of ```json ``` .")
        response = convo.last.text
    print(response)
    try:
        response=loadJson(response)
    except Exception as e:
        convo.send_message(f'{str(e)} you make this error becouse you have not folow these instructions: <{system_prompt}> now give answer to with his this qustion {question} with corrct format')
        response = convo.last.text
        print(str(e))
        response=loadJson(response)
    print(response)
    chat_response=response["chat_response"]
    # response = 'i am running'
    # print(response)
    # Check if the response contains code

    with open("./templates/preview.html", "w") as f:  
        f.write(response["html"])
        html_content=response["html"]
    codeIncluded=response["codeIncluded"]        
    # Clean the response and beautify it for display
    clean_response = html_remover(chat_response)
    # print(clean_response)
    beautifided_response = beautify_AiResponse(clean_response)
    # print(beautifided_response)
    return jsonify({"html": html_content, "codeIncluded":codeIncluded, "chat_response": beautifided_response}), 200

# Route to get the initial content of the preview page
@app.route("/initial_content", methods=["GET"])
def initial_content():
    try:
        with open("./templates/preview.html", "r" ,  encoding='utf-8', errors='ignore') as file:
            content = file.read()
            return jsonify({"html": content}), 200
    except Exception as e:
        print(f"An error occurred while reading initial content: {e}")
        return jsonify({"error": "Failed to load initial content"}), 500

# Route to save edited HTML content
@app.route("/save_edited_code", methods=["POST"])
def save_edited_code():
    data = request.get_json()
    print(data)
    html_content = data.get("code")
    b=data.get("blockName")
    page=data.get("page")
    b=OrderManegment.blockName2id(ProjectName,page,b)
    if not html_content:
        return jsonify({"error": "HTML content is required"}), 400
    try:
        with open(f"./Projects/{ProjectName}/pages/{page}/{b}", "w",encoding="utf-8") as file:
            file.write(html_content)
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"An error occurred while saving edited content: {e}")
        return jsonify({"error": "Failed to save edited content"}), 500
    
# Route to save and export the project as a ZIP file
@app.route("/export")
def export():
    try:
        export_dir = f"./Projects/{ProjectName}/toExport"
        project_zip_path = f"./Projects/{ProjectName}.zip"
        static_zip_path = f"./static/{ProjectName}.zip"

        # Clean up existing export directory and zip file
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        if os.path.exists(static_zip_path):
            os.remove(static_zip_path)

        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)

        # Generate HTML files for each page
        for page in os.listdir(f"./Projects/{ProjectName}/pages"):
            page_content = ""
            page_path = os.path.join(f"./Projects/{ProjectName}/pages", page)
            
            for block in os.listdir(page_path):
                block_path = os.path.join(page_path, block)
                with open(block_path, "r", encoding='utf-8', errors='ignore') as file:
                    page_content += file.read()

            # Save the compiled HTML to the export directory
            with open(f"{export_dir}/{page}.html", "w", encoding='utf-8', errors='ignore') as f:
                f.write(compile_html(page_content,ProjectName))
        
        # Create a ZIP archive of the exported project
        shutil.make_archive(f"./Projects/{ProjectName}", "zip", export_dir)
        shutil.move(project_zip_path, static_zip_path)

        # Send the ZIP file as a downloadable attachment
        directory = safe_join(app.root_path, 'static')
        return send_from_directory(directory, f"{ProjectName}.zip", as_attachment=True)
    
    except Exception as e:
        # Log the error and return an appropriate response
        print(f"Error in export route: {str(e)}")
        return jsonify({"error": "Failed to export the project"}), 500

# Route to get the list of pages
@app.route("/pages", methods=["POST"])
def pages():
    if not os.path.exists(f"./Projects/{ProjectName}/pages"):
        os.mkdir(f"./Projects/{ProjectName}/pages")
    pages = os.listdir(f"./Projects/{ProjectName}/pages")
    return jsonify({"pages": pages}), 200

# Route to Create new pages
@app.route("/CreatePage", methods=["POST"])
def CreatePage():
    try:
        page = request.get_json().get("pageName")
        if not os.path.exists(f"./Projects/{ProjectName}/pages"):
            os.mkdir(f"./Projects/{ProjectName}/pages")
        os.mkdir(f"./Projects/{ProjectName}/pages/{page}")
        
        # Log action
        convo.send_message(f"system: user created a new page named '{page}' in the project '{ProjectName}'!")
        
        return jsonify({"page": page})
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to Create new blocks
@app.route("/CreateBlock", methods=["POST"])
def CreateBlock():
    pageName = request.get_json().get("page")
    blok = request.get_json().get("blockName")
    
    if not os.path.exists(f"./Projects/{ProjectName}/bloksData/{pageName}/order.json"):
        os.mkdir(f"./Projects/{ProjectName}/bloksData/{pageName}")
        with open(f"./Projects/{ProjectName}/bloksData/{pageName}/order.json", "w") as f:
            f.write("[]")
    
    OrderManegment.manageOrder(f"./Projects/{ProjectName}/pages/{pageName}", ProjectName, pageName, blok)
    
    # Log action
    convo.send_message(f"system: user created a block named '{blok}' in the '{pageName}' page of the project '{ProjectName}'!")
    
    return jsonify({"page": pageName})

# Route to Delete pages
@app.route("/DeletePage", methods=["POST"])
def delete_page():
    page = request.get_json().get("pageName")
    page_path = f"./Projects/{ProjectName}/pages/{page}"
    
    if os.path.exists(page_path):
        shutil.rmtree(page_path)  # This deletes the directory and all its contents
        
        # Log action
        convo.send_message(f"system: user deleted the page named '{page}' from the project '{ProjectName}'!")
        
        return jsonify({"page": page}), 200
    else:
        return jsonify({"error": "Page does not exist"}), 404

# Route to Delete Blocks
@app.route("/DeleteBlock", methods=["POST"])
def DeleteBlock():
    page = request.get_json().get("pageName")
    b = request.get_json().get("block")
    b = b.replace(" ", "")
    b = OrderManegment.blockName2id(ProjectName, page, b)
    
    if not os.path.exists(f"./Projects/{ProjectName}/pages"):
        os.mkdir(f"./Projects/{ProjectName}/pages")
    
    OrderManegment.deleteOrder(f"./Projects/{ProjectName}/pages/{page}", ProjectName, page, b)
    os.remove(f"./Projects/{ProjectName}/pages/{page}/{b}")
    
    # Log action
    convo.send_message(f"system: user deleted the block named '{b}' from the '{page}' page in the project '{ProjectName}'!")
    
    return jsonify({"page": page})

# Route to get the list of blocks for a specific page
@app.route("/blocks", methods=["POST"])
def blocks():
    global page
    allbloks=[]
    page = request.get_json().get("page")
    # print(page)
    bloks = OrderManegment.listFiles(f"./Projects/{ProjectName}/pages/{page}")
    # print(bloks)
    for id in bloks:
        allbloks.append(OrderManegment.id2blockName(ProjectName,page,int(id))) 
        print(allbloks)
    convo.send_message(f"system: user selected {page} page from project {ProjectName}")
    return jsonify({"blocks": allbloks}), 200

# Route to get the content of a specific block
@app.route("/blockContent", methods=["POST"])
def blockContent():
    global page
    global block
    page = request.get_json().get("page")
    blokName = OrderManegment.blockName2id(ProjectName, page ,request.get_json().get("block"))
    block = ""
    with open(f"./Projects/{ProjectName}/pages/{page}/{blokName}", "r" ,  encoding='utf-8', errors='ignore') as f:
        block = f.read()
    convo.send_message(f"system: User selected {request.get_json().get('block')} block from {page} page from project {ProjectName}")
    return jsonify({"block": block}), 200


