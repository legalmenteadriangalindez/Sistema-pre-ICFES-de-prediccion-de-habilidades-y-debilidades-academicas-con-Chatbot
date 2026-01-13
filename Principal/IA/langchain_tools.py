from langchain_core.tools import Tool

from langchain_experimental.utilities import PythonREPL


python_repl = PythonREPL()

tool = Tool(
    name = "python_repl",
    function = python_repl.run,
    description = "ejecuta codigo en python en un interprete para calculos o logica matematica"
)

output = tool.run("print(2+2)")

print(output)





#--------------------------herramienta prsonalizada-------------
