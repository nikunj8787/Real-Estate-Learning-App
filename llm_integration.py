import requests
import json
import streamlit as st

class DeepSeekChat:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def get_response(self, user_input, context="general"):
        """Get response from DeepSeek API"""
        
        # Prepare the prompt with context
        system_prompt = self._get_system_prompt(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return "Sorry, I'm having trouble connecting to the AI service. Please try again later."
        except KeyError as e:
            st.error(f"Response Error: {str(e)}")
            return "Sorry, I received an unexpected response. Please try again."
        except Exception as e:
            st.error(f"Unexpected Error: {str(e)}")
            return "Sorry, something went wrong. Please try again."
    
    def _get_system_prompt(self, context):
        """Get system prompt based on context"""
        
        base_prompt = """You are an expert Real Estate Education Assistant specializing in Indian real estate laws, regulations, and practices. You provide accurate, helpful, and educational responses about:

- RERA (Real Estate Regulation and Development Act) compliance
- Property valuation methods and techniques
- Legal documentation and procedures
- Investment strategies and market analysis
- Construction and technical aspects
- Taxation and financial planning
- Property measurements and standards
- Dispute resolution and consumer rights

Always provide practical, actionable advice while mentioning relevant legal frameworks and current market conditions in India."""

        if context == "real estate education":
            return base_prompt + "\n\nFocus on educational content that helps users learn and understand real estate concepts step by step."
        elif context == "assessment":
            return base_prompt + "\n\nHelp users understand assessment questions and provide explanations for correct answers."
        elif context == "practice":
            return base_prompt + "\n\nProvide practice scenarios and case studies to help users apply their knowledge."
        else:
            return base_prompt

    def get_assessment_feedback(self, question, user_answer, correct_answer):
        """Get detailed feedback for assessment answers"""
        
        prompt = f"""
        Question: {question}
        User's Answer: {user_answer}
        Correct Answer: {correct_answer}
        
        Please provide detailed feedback explaining:
        1. Whether the user's answer is correct or incorrect
        2. Why the correct answer is right
        3. Key concepts the user should understand
        4. Additional tips or resources for improvement
        """
        
        return self.get_response(prompt, context="assessment")
    
    def generate_quiz_questions(self, topic, difficulty="intermediate", count=5):
        """Generate quiz questions for a specific topic"""
        
        prompt = f"""
        Generate {count} multiple-choice questions about {topic} in Indian real estate.
        
        Difficulty level: {difficulty}
        
        For each question, provide:
        1. Question text
        2. Four options (A, B, C, D)
        3. Correct answer
        4. Brief explanation
        
        Focus on practical knowledge and current regulations.
        Format as JSON with this structure:
        {{
            "questions": [
                {{
                    "question": "Question text",
                    "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                    "correct_answer": "A",
                    "explanation": "Brief explanation"
                }}
            ]
        }}
        """
        
        response = self.get_response(prompt, context="assessment")
        
        try:
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"questions": []}
        except:
            return {"questions": []}
    
    def get_personalized_learning_path(self, user_level, interests, goals):
        """Generate personalized learning recommendations"""
        
        prompt = f"""
        Create a personalized learning path for a real estate student with:
        
        Current Level: {user_level}
        Interests: {interests}
        Goals: {goals}
        
        Provide a structured learning plan with:
        1. Recommended modules in order
        2. Estimated time for each module
        3. Key skills to develop
        4. Practical exercises
        5. Assessment milestones
        
        Focus on Indian real estate context and current market conditions.
        """
        
        return self.get_response(prompt, context="real estate education")
