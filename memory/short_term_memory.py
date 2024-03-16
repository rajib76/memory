import zmq


class ShortTermMemory():
    def __init__(self):
        self.port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://127.0.0.1:%s" % self.port)

    def context_retrieval(self,question):
        if str(question).lower() == "What is TajMahal?".lower():
            content ={'question':question,'context':'TajMahal is a monument which embodies love'}
        elif str(question).lower() == "Where is TajMahal?".lower():
            content ="{'question':'Where is TajMahal?','context':'TajMahal, a monument, was built by ShahJahan. It is situated in Agra, UttarPradesh'}"
        elif str(question).lower() == "When was TajMahal Built?".lower():
            content ="{'question':'When was TajMahal Built?','context':'TajMahal, which is a monument was built in 1632.'}"
        else:
            content = "{'question':'Who has built TajMahal?','context':'The TajMahal, a monument was built by ShahJahan.'}"
        content = content.__str__()

        self.send_to_long_term_memory(content)
        return content

    def send_to_long_term_memory(self,content):
        self.socket.send_string(content)



