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

instruction = """
    You are a data scientist working for a company that is building a graph database. 
    Your task is to extract information from data and convert it into a graph database.
    Provide a set of Nodes in the form [ENTITY_ID, TYPE, PROPERTIES] 
    and a set of relationships in the form [ENTITY_ID_1, RELATIONSHIP, ENTITY_ID_2, PROPERTIES].
    It is important that the ENTITY_ID_1 and ENTITY_ID_2 exists as nodes with a matching ENTITY_ID. 
    If you can't pair a relationship with a pair of nodes add it.
    When you find a node or relationship you want to add try to create a generic TYPE for it 
    that  describes the entity you can also think of it as a label.
    Note that output must in dictionary type

    Example:
    Input : Alice lawyer and is 25 years old and Bob is her roommate since 2001. Bob works as a journalist. Alice owns a the webpage www.alice.com and Bob owns the webpage www.bob.com.
    Output : 
    { "Nodes": ["alice", "Person", {"age": 25, "occupation": "lawyer", "name":"Alice"}], ["bob", "Person", {"occupation": "journalist", "name": "Bob"}], ["alice.com", "Webpage", {"url": "www.alice.com"}], ["bob.com", "Webpage", {"url": "www.bob.com"}],
      "Edges": ["alice", "roommate", "bob", {"start": 2021}], ["alice", "owns", "alice.com", {}], ["bob", "owns", "bob.com", {}]
    }
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
