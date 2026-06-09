"""
Project : Smart Q&A ChatBot
A Production-Ready Question Answering Bot with Structured Output
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from langsmith import traceable, Client
from dotenv import load_dotenv
import os

# -----------------------------------------------------
# Load Environment Variables
# -----------------------------------------------------

load_dotenv()

# -----------------------------------------------------
# Validate OpenAI API Key
# -----------------------------------------------------

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables."
    )

# -----------------------------------------------------
# LangSmith Configuration
# -----------------------------------------------------

if os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault(
        "LANGCHAIN_PROJECT",
        "Smart Q&A Bot Project"
    )

    print(
        f"LangSmith Configured - Project: "
        f"{os.getenv('LANGCHAIN_PROJECT')}"
    )

# -----------------------------------------------------
# Structured Output Schema
# -----------------------------------------------------

class QAResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question.")
    confidence: str = Field(description="Confidence level: high, medium, or low.")
    reasoning: str = Field(description="Reasoning behind the answer.")

    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Related follow-up questions."
    )

    sources_needed: bool = Field(
        default=False,
        description="Whether external sources would improve the answer."
    )


# -----------------------------------------------------
# Smart Q&A Bot
# -----------------------------------------------------

class SmartQABot:

    def __init__(self,model_name: str = "gpt-4o-mini",temperature: float = 0.3):

        self.model = (ChatOpenAI(model=model_name,temperature=temperature).with_structured_output(QAResponse))

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a knowledgeable Q&A assistant.

                    Guidelines:
                    - Answer accurately and concisely.
                    - Be honest about uncertainty.
                    - Use 'low' confidence if unsure.
                    - Provide reasoning.
                    - Suggest useful follow-up questions.
                    - Indicate if external sources would help.

                    Always return helpful and accurate information.
                    """
                ),
                ("human", "{question}")
            ]
        )

        self.chain = self.prompt | self.model

    # -------------------------------------------------

    @traceable(name="ask_question",run_type="chain")
    def ask(self,question: str) -> QAResponse:

        try:

            # Input Validation
            if question is None:
                raise ValueError("Question cannot be None.")

            if not isinstance(question, str):
                raise TypeError("Question must be a string.")

            if not question.strip():
                raise ValueError("Question cannot be empty.")

            response = self.chain.invoke({"question": question})

            return response

        except Exception as e:

            return QAResponse(
                answer=(
                    "I'm sorry, I couldn't process "
                    "your question at this time."
                ),
                confidence="low",
                reasoning=str(e),
                follow_up_questions=["Could you rephrase the question?"],
                sources_needed=True
            )

    # -------------------------------------------------

    @traceable(name="ask_batch",run_type="chain")
    def ask_batch(self,questions: List[str]) -> List[QAResponse]:

        try:
            inputs = [{"question": q} for q in questions]

            responses = self.chain.batch(inputs,return_exceptions=False)

            return responses

        except Exception as e:

            return [
                QAResponse(
                    answer=(
                        "Batch processing failed."
                    ),
                    confidence="low",
                    reasoning=str(e),
                    follow_up_questions=[],
                    sources_needed=True
                )
            ]


# -----------------------------------------------------
# Demo: Individual Questions
# -----------------------------------------------------

@traceable(name="qa_demo",run_type="chain")
def demo_qa_bot():

    bot = SmartQABot()

    questions = [
        "What is the capital of France?",
        "Explain the theory of relativity.",
        "How does photosynthesis work?"
    ]

    print("\n" + "=" * 60)
    print("SMART Q&A BOT DEMO")
    print("=" * 60)

    for question in questions:

        response = bot.ask(question)

        print(f"\nQuestion: {question}")
        print("-" * 40)

        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")
        print(f"Reasoning: {response.reasoning}")

        print(
            f"Follow-up Questions: "
            f"{response.follow_up_questions}"
        )

        print(
            f"Sources Needed: "
            f"{response.sources_needed}"
        )

        print("-" * 60)


# -----------------------------------------------------
# Demo: Batch Processing
# -----------------------------------------------------

@traceable(name="batch_demo",run_type="chain")
def demo_batch_processing():

    bot = SmartQABot()

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?"
    ]

    print("\n" + "=" * 60)
    print("BATCH PROCESSING DEMO")
    print("=" * 60)

    responses = bot.ask_batch(questions)

    for q, r in zip(questions,responses):

        print(f"\nQuestion: {q}")

        print(
            f"Answer: "
            f"{r.answer[:100]}..."
        )

        print(
            f"Confidence: "
            f"{r.confidence}"
        )


# -----------------------------------------------------
# Demo: Error Handling
# -----------------------------------------------------

@traceable(name="error_handling_demo",run_type="chain")
def demo_error_handling():

    bot = SmartQABot()

    print("\n" + "=" * 60)
    print("ERROR HANDLING DEMO")
    print("=" * 60)

    # Test 1: Very Long Question

    long_question = ("What is "+ ("very " * 1000)+ "important?")

    response = bot.ask(long_question)

    print("\nLong Question Test")
    print(
        f"Confidence: "
        f"{response.confidence}"
    )

    print(
        f"Answer: "
        f"{response.answer[:100]}..."
    )

    # Test 2: Empty String

    response = bot.ask("")

    print("\nEmpty Question Test")

    print(
        f"Confidence: "
        f"{response.confidence}"
    )

    print(
        f"Reasoning: "
        f"{response.reasoning}"
    )

    # Test 3: None Input

    response = bot.ask(None)

    print("\nNone Input Test")

    print(
        f"Confidence: "
        f"{response.confidence}"
    )

    print(
        f"Reasoning: "
        f"{response.reasoning}"
    )


# -----------------------------------------------------
# Main
# -----------------------------------------------------

if __name__ == "__main__":

    try:

        demo_qa_bot()

        demo_batch_processing()

        demo_error_handling()

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETED")
        print("=" * 60)

    finally:

        if os.getenv("LANGSMITH_API_KEY"):
            Client().flush()
