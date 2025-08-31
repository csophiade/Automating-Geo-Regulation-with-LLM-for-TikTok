import json
import os
from markitdown import MarkItDown
# https://github.com/microsoft/markitdown
# to describe images if needed
# from openai import OpenAI
#client = OpenAI()
#md = MarkItDown(llm_client=client, llm_model="gpt-4o", llm_prompt="optional custom prompt")
#result = md.convert("example.jpg")
#print(result.text_content)
# filename = "Utah_Social_Media_Regulation_Act.pdf"
def get_law_artifacts(result, filename):
    # return an array to be given to the dict
    # nlp parse the result
    return {
        "filename": filename,
        "original_file": f"files/laws/{filename}",
        "md_file": f"files/laws/md/{os.path.splitext(filename)[0]}.md",
        "title": os.path.splitext(filename)[0].replace("_", " "),
        "regulatory_area": "TBD",   
        "jurisdiction": "TBD",      
        "rules": []                 
    }


def convert_to_md():
    artifacts_list = []
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

    pdf_path = os.path.join(PROJECT_ROOT, "files", "laws")
    output_dir = os.path.join(PROJECT_ROOT, "files", "laws", "md")
    os.makedirs(output_dir, exist_ok=True)

    md = MarkItDown() # Set to True to enable plugins
    for filename in os.listdir(pdf_path):
        if filename.endswith(".pdf"):
            print(filename)  # just the filename

            output_file = os.path.join(output_dir, os.path.splitext(filename)[0] + ".md")

            try:
                result = md.convert(os.path.join(pdf_path, filename))

                artifacts_list.append(get_law_artifacts(result, filename))

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result.text_content)
            except Exception as e:
                print(f"❌ Failed on {filename}: {e}")
    
    with open(os.path.join(os.path.join(PROJECT_ROOT, "files", "main"), "directory.json"), "w", encoding="utf-8") as f:
        json.dump(artifacts_list, f, indent=2)

    # output_dir = os.path.join(PROJECT_ROOT, "files", "laws", "md")
    # os.makedirs(output_dir, exist_ok=True)
    # filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
    # output_file = os.path.join(output_dir, filename)
    # 
    # md = MarkItDown() # Set to True to enable plugins
    # result = md.convert(pdf_path)
    # with open(output_file, "w", encoding="utf-8") as f:
    #     f.write(result.text_content)
            
if __name__ == "__main__":
    convert_to_md()            