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

extraction_prompt_instruction = """
    You are an expert in Graph Databases. You extract entities and relationships from data and
    convert it into a graph database. You follow the below rules while creating the graph.
    <RULES>
    1. Create a set of Nodes as [ENTITY_ID, TYPE, PROPERTIES]
    2. Create relationships between Nodes as [ENTITY_ID_1, RELATIONSHIP, ENTITY_ID_2, PROPERTIES]
    3. For each Node and relationship, create a label that describes the entity or the relationship
    4. Output must be a dictionary type
    </RULES>
    
    Here is an example for you to follow:
    <EXAMPLE>
    Input: Rajib, a software engineer is 40 years old. Rajat works with Rajib. Rajat is a data scientist. Rajat owns a blue Ferari and Rajib drives a grey Toyota.
    Output:
    {"Nodes": ["rajib","Person",{"age":40,"occupation":"software engineer","name":"Rajib"}],["rajat","Person",{"occupation":"data scientist","name":"rajat"}],["ferari","Car",{}],["toyota","Car",{}],
    "Edges": ["rajib", "colleague", "rajat", {}],["rajib", "drives", "toyota",{"color":"grey}],["rajat","drives","ferari",{"color":"blue"}]
    }
    </EXAMPLE>
    """

extraction_prompt = """
{extraction_prompt_instruction}
{question}
{context}
"""
extraction_prompt_cql = """Reflect on the provided output. It has nodes and edges. Each node has a label.
Create *SYNTACTICALLY CORRECT* CYPHER QUERY LANGUAGE to create and connect the entities. 
*ENSURE* to use the label for the entity.
Please use MERGE as the entities may or may not exist in the database.
*REMEMBER* to return only the CYPHER QUERY LANGUAGE. Do not add anything else to the response.
{output}
"""


class LongTermMemory():
    def __init__(self):
        self.module = __name__
        self.port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % self.port)

    def extract_noded(self,state):
        pass

    def convert_to_pattern_and_store(self, question, context):
        prompt = ChatPromptTemplate.from_template(extraction_prompt)
        prompt_cql = ChatPromptTemplate.from_template(extraction_prompt_cql)
        model = ChatOpenAI(model_name="gpt-4")
        chain = prompt | {"output": model} | prompt_cql | model
        resp = chain.invoke({"extraction_prompt_instruction": extraction_prompt_instruction,
                             "question": question,
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
    # question = "What is blockchain"
    # context = "A blockchain is a distributed ledger with growing lists of records (blocks) that are securely linked together via cryptographic hashes.[1][2][3][4] Each block contains a cryptographic hash of the previous block, a timestamp, and transaction data (generally represented as a Merkle tree, where data nodes are represented by leaves). Since each block contains information about the previous block, they effectively form a chain (compare linked list data structure), with each additional block linking to the ones before it. Consequently, blockchain transactions are irreversible in that, once they are recorded, the data in any given block cannot be altered retroactively without altering all subsequent blocks."
    # ltm.convert_to_pattern_and_store(question,context)
    ltm.run()
