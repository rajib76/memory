from memory.short_term_memory import ShortTermMemory

if __name__=="__main__":

    # question='What is TajMahal?'
    # question = 'Where is TajMahal?'
    # question = 'When was TajMahal Built?'
    question = 'Who has built TajMahal?'
    stm = ShortTermMemory()
    retrieved_context = stm.context_retrieval(question)
    print(retrieved_context)
