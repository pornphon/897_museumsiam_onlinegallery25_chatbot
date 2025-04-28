from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["variable1", "variable2"],  # ชื่อตัวแปรที่จะแทนค่า
    template="สวัสดี {variable1}! วันนี้คุณอยากทำอะไรกับ {variable2}?"
)

ready_prompt = prompt.format(variable1="คุณสมชาย", variable2="แมวของคุณ")
print(ready_prompt)