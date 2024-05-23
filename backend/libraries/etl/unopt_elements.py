from libraries.llm.groq.groq_llm import Groq
from libraries.llm.groq import groq_utils
import time


class EleParse:

    @staticmethod
    def first_reorg(parsed_doc):
        reorg = {}
        for var in parsed_doc:
            total_append = []
            full_text = ""
            full_table = ""
            table_without_text = True
            text_without_table = True
            for ele in parsed_doc[var]:
                if ele["type"] == "text":
                    table_without_text = False
                    if len(full_table) > 0:
                        total_append.append({"table": f"Table: {full_table}"})
                        full_table = ""
                    full_text += ele["text"]
                elif ele["type"] == "table":
                    text_without_table = False
                    if len(full_text) > 0:
                        texts = groq_utils.split_text(full_text)
                        for text in texts:
                            total_append.append({"text": text})
                        full_text = ""
                    for row in ele["data"]:
                        full_table += "\t" + "\t".join(row)
            if table_without_text:
                total_append.append({"table": f"Table: {full_table}"})
            elif text_without_table:
                texts = groq_utils.split_text(full_text)
                for text in texts:
                    total_append.append({"text": text})
            reorg[var] = total_append
        return reorg

    @staticmethod
    def edgar_doc_w_filter(reorg):
        llama3_70 = Groq()

        collect_chunks = []
        for page in reorg:
            count = 0
            for item in reorg[page]:
                if "text" in item:
                    time.sleep(3)
                    tags = llama3_70.struct_output(item["text"])
                    filtered_tags = [tag.value for tag in tags.tags]
                    doc_json = {
                        "content": item["text"],
                        "page": page,
                        "section_number": count,
                        "type": "text",
                        "fin_tags": filtered_tags,
                    }
                    collect_chunks.append(doc_json)
                elif "table" in item:
                    time.sleep(3)
                    tags = llama3_70.struct_output(item["table"])
                    filtered_tags = [tag.value for tag in tags.tags]
                    doc_json = {
                        "content": item["table"],
                        "page": page,
                        "section_number": count,
                        "type": "table",
                        "fin_tags": filtered_tags,
                    }
                    collect_chunks.append(doc_json)
                count += 1
        return collect_chunks

    @staticmethod
    def edgar_doc(reorg):

        collect_chunks = []
        for page in reorg:
            count = 0
            for item in reorg[page]:
                if "text" in item:
                    doc_json = {
                        "content": item["text"],
                        "page": page,
                        "section_number": count,
                        "type": "text",
                    }
                    collect_chunks.append(doc_json)
                elif "table" in item:
                    doc_json = {
                        "content": item["table"],
                        "page": page,
                        "section_number": count,
                        "type": "table",
                    }
                    collect_chunks.append(doc_json)
                count += 1
        return collect_chunks
