from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index import ServiceContext, VectorStoreIndex, StorageContext, load_index_from_storage, SimpleDirectoryReader, Document
from llama_hub.file.unstructured.base import UnstructuredReader
from llama_index.llms import OpenAI
from llama_index.indices.postprocessor import (
    MetadataReplacementPostProcessor,
    SentenceTransformerRerank
)
from llama_index.node_parser import SentenceWindowNodeParser
from llama_index.embeddings import OpenAIEmbedding
from llama_index.agent import OpenAIAgent


import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def build_sentence_window_index(
    documents,
    llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    sentence_window_size=3,
    save_dir="sentence_index",
):
    # create the sentence window node parser w/ default settings
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=sentence_window_size,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    sentence_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model,
        node_parser=node_parser,
    )
    if not os.path.exists(save_dir):
        sentence_index = VectorStoreIndex.from_documents(
            documents, service_context=sentence_context
        )
        sentence_index.storage_context.persist(persist_dir=save_dir)
    else:
        sentence_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=save_dir),
            service_context=sentence_context,
        )

    return sentence_index


def get_sentence_window_query_engine(sentence_index, similarity_top_k=6, rerank_top_n=2):
    # define postprocessors
    postproc = MetadataReplacementPostProcessor(target_metadata_key="window")
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n, model="BAAI/bge-reranker-base"
    )

    sentence_window_engine = sentence_index.as_query_engine(
        similarity_top_k=similarity_top_k, node_postprocessors=[
            postproc, rerank]
    )
    return sentence_window_engine


def get_index(input_files, save_dir):
    documents = SimpleDirectoryReader(
        input_files=input_files,
        file_extractor={
            ".pdf": UnstructuredReader(),
            ".html": UnstructuredReader(),
            ".txt": UnstructuredReader(),
        }
    ).load_data()
    document = Document(text="\n\n".join([doc.text for doc in documents]))
    print("finish loading data")
    index = build_sentence_window_index(
        [document],
        llm=OpenAI(model="gpt-4", temperature=0.2),
        save_dir=save_dir,
        embed_model=OpenAIEmbedding(model="text-embedding-ada-002"),
    )
    return index


def get_agent(slide_inputs, homework_inputs, syllabus_inputs, slide_index_dir, homework_index_dir, syllabus_index_dir, course_code, course_title, instructor_prompt=""):
    tools = []
    print(slide_inputs, homework_inputs, syllabus_inputs)
    print(slide_index_dir, homework_index_dir, syllabus_index_dir)
    if len(slide_inputs) != 0:
        slide_index = get_index(input_files=slide_inputs,
                                save_dir=slide_index_dir)
        slide_query_engine = get_sentence_window_query_engine(
            slide_index, similarity_top_k=6)
        slide_query_engine_tool = QueryEngineTool(
            query_engine=slide_query_engine,
            metadata=ToolMetadata(
                name="lecture_question_query_engine",
                description=f"useful for when you want to answer queries related to concepts of {course_title}, lecture content, etc.",
            ),
        )
        tools.append(slide_query_engine_tool)
    if len(homework_inputs) != 0:
        practice_index = get_index(
            input_files=homework_inputs, save_dir=homework_index_dir)
        practice_query_engine = get_sentence_window_query_engine(
            practice_index, similarity_top_k=6)
        practice_query_engine_tool = QueryEngineTool(
            query_engine=practice_query_engine,
            metadata=ToolMetadata(
                name="practice_question_query_engine",
                description="useful for when you want to answer queries related to practice questions, homework, etc.",
            ),
        )
        tools.append(practice_query_engine_tool)
    if len(syllabus_inputs) != 0:
        syllabus_index = get_index(
            input_files=syllabus_inputs, save_dir=syllabus_index_dir)
        syllabus_query_engine = get_sentence_window_query_engine(
            syllabus_index, similarity_top_k=6)
        syllabus_query_engine_tool = QueryEngineTool(
            query_engine=syllabus_query_engine,
            metadata=ToolMetadata(
                name="syllabus_question_query_engine",
                description=f"useful for when you want to answer queries related to syllabus, course logistics, exam and due dates of {course_code} etc.",
            ),
        )
        tools.append(syllabus_query_engine_tool)
    if len(tools) == 0:
        return None

    SYSTEM_PROMPT = f"""
    You are a teaching assistant of course {course_code}: {course_title}.
    You are answering a question from a student to help them better understand the course content.
    You should only answer questions related to this course.
    You should consult the course slides, homework, and syllabus to answer the question.
    You should consult course syllabus for logistic questions.
    """ if instructor_prompt == "" else f"""
    You are a teaching assistant of course {course_code}: {course_title}.
    You are answering a question from a student to help them better understand the course content.
    You should only answer questions related to this course.
    You should consult the course slides, homework, and syllabus to answer the question.
    You should consult course syllabus for logistic questions.
    You should also following the instructor's guidance: \n{instructor_prompt}
    """
    agent = OpenAIAgent.from_tools(tools, llm=OpenAI(
        model="gpt-4"), system_prompt=SYSTEM_PROMPT, verbose=True)
    return agent

