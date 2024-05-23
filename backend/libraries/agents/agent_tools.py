import os
import shutil
from pathlib import Path
from os.path import dirname, join
from dotenv import load_dotenv
from libraries.etl.process_doc import TypeConvert
from libraries.edgar_simple.edgar_redirect import RedirectUtils as RU
from libraries.edgar_simple.edgar_interface import Edgar
from datetime import datetime
from libraries.rag.rag_wo_filter import RagWOFilter
from libraries.rag.rag_utils import RagUtils
from langchain_core.tools import tool
from libraries.etl.google_process import DocumentProcess

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(script_dir)))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)


@tool
def edgar_report(
    ticker: str,
    quarter: int,
    year: int,
    form: str = "10-Q",
):
    """
    Tool is used to to add additional ['10-K','10-Q','8-K'] financial filings of a company to database.
    IMPORTANT: this tool provides 0 insights
    :ticker: str - stock symbol of a company
    :quarter: int - [1,2,3,4] the quarter the report is in, use 4 for last quarter.
    :year: int - the year the filing is filed
    :form: str - filing of either ['10-K','10-Q','8-K']
    """
    try:
        save_to = join(backend_dir, "data/something.pdf")
        dump_to = join(backend_dir, "data/something.htm")
        up_till_date_ago = f"{year - 1}-01-01"
        nvidia = Edgar(
            ticker, up_till_date_ago=datetime.strptime(up_till_date_ago, "%Y-%m-%d")
        )
        url = nvidia.get_by(
            quarter=quarter if 0 < quarter <= 4 else 1,
            year=year,
            form=form if form in ["10-Q", "10-K", "8-K"] else "10-Q",
        )
        doc_xml = RU.query_url(url)
        with open(dump_to, "w", encoding="UTF-8") as f:
            f.write(doc_xml)
        file_path = TypeConvert.convert_htm_pdf(
            htm_file_path="sample.htm", save_to=save_to
        )[0]

        response = DocumentProcess.create_rag(file_path)
        if "data is uploaded" in response:
            return f"{form} filing for {ticker} in {year} and quarter {quarter} is now ready for use."
        else:
            return f"{form} filing for {ticker} in {year} and quarter {quarter} is unavailable for use due to {response}"
    except Exception as e:
        print(e)
        print()
        return f"{form} filing for {ticker} in {year} and quarter {quarter} is unavailable."


@tool
def raq_qa_hybrid(query_prompt):
    """
    This RAG tool is used when user naively request for information in our database
    :query_prompt: str - required user's query
    """
    try:
        w_rag = RagWOFilter()
        w_rag.activate_collection()
        results = w_rag.rag_qa_hybrid(query_prompt=query_prompt)
        filtered_results = RagUtils.mean_score_filter(results)
        w_rag.close()
        combined_text = (
            f"These are the relevant context for #Query of \n{query_prompt}:\n\n"
        )
        referenced_text = "References: "
        for idx, r in enumerate(filtered_results):
            combined_text += f"{idx} and confidence score of {r.metadata.score}:\n{r.properties['content']}\n"
            if r.properties["type"] == "text":
                referenced_text += f"text from page {r.properties['page']} and section number of {r.properties['section_number']}.\n"
            else:
                referenced_text += f"table from page {r.properties['page']} and section number of {r.properties['section_number']}.\n"
        combined_text += referenced_text
        return combined_text
    except Exception as e:
        print(e)
        print()
        return f"tool raq_qa_rerank ran into error, you should try using other tools.\nError: {e}"


@tool
def raq_qa_rerank(query_prompt, rerank_query):
    """
    This RAG tool is used when user require deep thought and consideration when they are requesting for information in our database .
    Make sure you create rerank_query which distilled the intentions from query_prompt
    :query_prompt: str - required user's query
    :rerank_query: str - required a condensed version of query_prompt
    """
    try:
        w_rag = RagWOFilter()
        rerank_kwargs = {"prop": "content", "query": rerank_query}
        w_rag.activate_collection()
        results = w_rag.rag_qa_complex(
            query_prompt=query_prompt,
            rerank_kwargs=rerank_kwargs,
        )
        filtered_results = RagUtils.mean_rerank_filter(results)
        w_rag.close()
        combined_text = (
            f"These are the relevant context for #Query of \n{query_prompt}:\n\n"
        )
        referenced_text = "References: "
        for idx, r in enumerate(filtered_results):
            combined_text += f"{idx} and confidence score of {r.metadata.certainty}:\n{r.properties['content']}\n"
            if r.properties["type"] == "text":
                referenced_text += f"text from page {r.properties['page']} and section number of {r.properties['section_number']}.\n"
            else:
                referenced_text += f"table from page {r.properties['page']} and section number of {r.properties['section_number']} which is a table. You must include in your answer a warning that tables are not often accurate and users are to verify the numbers again.\n"
        combined_text += referenced_text
        return combined_text
    except Exception as e:
        print(e)
        print()
        return f"tool raq_qa_rerank ran into error, you should try using other tools.\nError: {e}"


nvidia = Edgar("NVDA", up_till_date_ago=datetime.strptime("2020-01-01", "%Y-%m-%d"))

__all__ = ["raq_qa_rerank", "raq_qa_hybrid", "edgar_report"]
