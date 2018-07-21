
pipeOutput = None

def setPipe(connection):
    global pipeOutput
    pipeOutput = connection

def log(text):
    print(text)
    
    if pipeOutput:
        pipeOutput.send(text + '\n')
