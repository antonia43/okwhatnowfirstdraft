import os
from langfuse import Langfuse
from google import genai
from google.genai import types
import streamlit as st
import uuid
import traceback


try:
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
    LANGFUSE_ENABLED = True
    
    print(f"🟢 Langfuse initialized successfully")
    
except Exception as e:
    print(f"🔴 Langfuse initialization failed: {e}")
    LANGFUSE_ENABLED = False


class LangfuseGeminiWrapper:
    """Wrapper for Google Gemini API calls with Langfuse tracing (v3 API)"""
    
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        # fall back to env vars if api_key not passed
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.last_trace_id = None
    
    def generate_content(
        self, 
        prompt: str, 
        system_instruction: str = None,
        temperature: float = 0.3,
        user_id: str = None,
        session_id: str = None,
        metadata: dict = None
    ):
        """Generating content with Langfuse tracing (v3 API)"""
        
        if LANGFUSE_ENABLED:
            try:
                print(f"🔵 Creating generation with v3 API")
                # v3 uses start_generation() with context manager
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="gemini_generate_content",
                    model=self.model,
                    input=prompt,
                    metadata={
                        "temperature": temperature,
                        "system_instruction": system_instruction,
                        **(metadata or {})
                    }
                ) as generation:
                    
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                    
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                    
                    output_text = response.text
                    
                    # Update with output
                    generation.update(output=output_text)
                    
                    # Update trace-level attributes
                    langfuse.update_current_trace(
                        user_id=user_id,
                        session_id=session_id,
                        input=prompt,
                        output=output_text
                    )
                    
                    self.last_trace_id = langfuse.get_current_trace_id()
                    print(f"🟢 Generation logged with trace ID: {self.last_trace_id}")
                    
                    return output_text
                    
            except Exception as e:
                print(f"🔴 Langfuse error: {e}")
                traceback.print_exc()
                # Fallback: run without tracing
        
        # Fallback if Langfuse disabled or error
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        
        return response.text
    
    def generate_content_multimodal(
        self, 
        prompt: str, 
        file_data: bytes, 
        mime_type: str,
        system_instruction: str = None,
        temperature: float = 0.3,
        user_id: str = None,
        session_id: str = None,
        metadata: dict = None
    ):
        """Generate content with multimodal input (file + text) with Langfuse tracing"""
        
        if LANGFUSE_ENABLED:
            try:
                print(f"🔵 Creating multimodal generation with v3 API")
                
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="gemini_generate_content_multimodal",
                    model=self.model,
                    input={"prompt": prompt, "mime_type": mime_type},
                    metadata={
                        "temperature": temperature,
                        "system_instruction": system_instruction,
                        "mime_type": mime_type,
                        **(metadata or {})
                    }
                ) as generation:
                    
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                    )
                    
                    contents = [
                        types.Part.from_bytes(data=file_data, mime_type=mime_type),
                        prompt
                    ]
                    
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    )
                    
                    output_text = response.text
                    
                    generation.update(output=output_text)
                    
                    langfuse.update_current_trace(
                        user_id=user_id,
                        session_id=session_id,
                        input={"prompt": prompt, "mime_type": mime_type},
                        output=output_text
                    )
                    
                    self.last_trace_id = langfuse.get_current_trace_id()
                    print(f"🟢 Multimodal generation logged with trace ID: {self.last_trace_id}")
                    
                    return output_text
                    
            except Exception as e:
                print(f"🔴 Langfuse error: {e}")
                traceback.print_exc()
        
        # Fallback if Langfuse disabled or error
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        
        contents = [
            types.Part.from_bytes(data=file_data, mime_type=mime_type),
            prompt
        ]
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        
        return response.text


class LangfuseChatWrapper:
    """
    Wrapper for Google Gemini Chat API with Langfuse tracing
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.chat = None
        self.trace = None
        self.message_count = 0
        self.trace_id = None
    
    def create_chat(self, system_instruction: str = None, user_id: str = None, session_id: str = None):
        """Creating a new chat session with tracing"""
        
        # Create a trace for the entire chat session if langfuse enabled
        if LANGFUSE_ENABLED:
            try:
                self.trace = langfuse.trace(
                    name="gemini_chat_session",
                    user_id=user_id,
                    session_id=session_id or str(uuid.uuid4()),
                    metadata={
                        "system_instruction": system_instruction,
                        "model": self.model
                    }
                )
                self.trace_id = self.trace.id
            except AttributeError:
                # old version fallback
                self.trace_id = str(uuid.uuid4())
            except Exception as e:
                print(f"Langfuse trace creation failed: {e}")
        
        # creating chat
        self.chat = self.client.chats.create(model=self.model)
        
        if system_instruction:
            self.chat.send_message(system_instruction)
        
        return self.chat
    
    def send_message(
        self, 
        message: str, 
        user_id: str = None,
        metadata: dict = None
    ):
        """Send a message in the chat with tracing"""
        
        if not self.chat:
            raise ValueError("Chat not initialized. Call create_chat() first.")
        
        self.message_count += 1
        
        # log to langfuse if enabled
        generation = None
        if LANGFUSE_ENABLED and self.trace:
            try:
                generation = self.trace.generation(
                    name=f"chat_message_{self.message_count}",
                    model=self.model,
                    input=message,
                    metadata=metadata or {}
                )
            except Exception as e:
                print(f"Langfuse generation failed: {e}")
        
        try:
            response = self.chat.send_message(message)
            output_text = response.text
            
            if generation:
                try:
                    generation.end(
                        output=output_text,
                        level="DEFAULT",
                        status_message="Success"
                    )
                except Exception as e:
                    print(f"Langfuse update failed: {e}")
            
            return output_text
            
        except Exception as e:
            if generation:
                try:
                    generation.end(level="ERROR", status_message=str(e))
                except:
                    pass
            raise e
    
    def get_trace_id(self):
        """Get the current trace ID"""
        return self.trace_id


def log_user_feedback(trace_id: str, score: float, comment: str = None):
    """
    Log user feedback (thumbs up/down) to Langfuse
    """
    if not LANGFUSE_ENABLED or not trace_id:
        return
    
    try:
        langfuse.score(
            trace_id=trace_id,
            name="user_feedback",
            value=score,
            comment=comment
        )
    except Exception as e:
        print(f"Error logging feedback: {e}")


def get_user_id():
    # Try multiple sources, fallback to email
    return (
        st.session_state.get("user_id") or 
        st.session_state.get("username") or
        st.session_state.user.get("email") or  # Full email as fallback
        st.session_state.user.get("display_name") or
        "anonymous"
    )


def get_session_id():
    """Helper to generate a unique session ID"""
    if "langfuse_session_id" not in st.session_state:
        st.session_state.langfuse_session_id = str(uuid.uuid4())
    return st.session_state.langfuse_session_id


def flush_langfuse():
    """Ensuring all traces are sent to Langfuse before app closes"""
    if LANGFUSE_ENABLED:
        try:
            langfuse.flush()
        except Exception as e:
            print(f"Langfuse flush failed: {e}")
