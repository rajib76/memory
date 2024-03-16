import ast
import json
import os

import zmq
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

stm_prompt = """Reflect on the question, context and the answer provided.
Extract the main entities that connect the question, context and the answer. 
Then create *SYNTACTICALLY CORRECT* CYPHER QUERY LANGUAGE to create and connect the entities. 
Please use MERGE as the entities may or may not exist in the database.
*REMEMBER* to return only the CYPHER QUERY LANGUAGE. Do not add anything else to the response.
{question}
{context}
"""


class LongTermMemory():
    def __init__(self):
        self.module = __name__
        self.port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % self.port)

    def convert_to_pattern_and_store(self, question, context):
        prompt = ChatPromptTemplate.from_template(stm_prompt)
        model = ChatOpenAI(model_name="gpt-4")
        chain = prompt | model
        resp = chain.invoke({"question": question,
                             "context": context})

        print(resp.content)
        kg = Neo4jGraph(
            url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD
        )

        result = kg.query(resp.content)
        print(result)
        return result

    def run(self):
        print("Long term memory is activated")
        while True:
            msg = self.socket.recv()
            print(msg)
            msg_json = ast.literal_eval(json.loads(json.dumps(msg.decode("utf-8"))))
            question = msg_json['question']
            context = msg_json['context']
            result = self.convert_to_pattern_and_store(question, context)
            print(result)


if __name__ == "__main__":
    ltm = LongTermMemory()
    ltm.run()
