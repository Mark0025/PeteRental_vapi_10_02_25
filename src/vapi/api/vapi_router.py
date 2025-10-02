"""
VAPI Router
==========

FastAPI router for VAPI-specific endpoints including chat completions,
webhooks, and persona management.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, Annotated, List
from datetime import datetime
import time
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import logger
from ai.model_manager import ModelManager
from config.model_settings import model_settings
from vapi.models.webhook_models import (
    VAPIChatRequest, VAPIChatResponse, VAPIMessage,
    Persona, PersonaModel
)
from vapi.services.provider_service import ProviderService

class VAPIRouter:
    """Router class for VAPI endpoints"""
    
    def __init__(self, model_manager: ModelManager, vapi_api_key: str):
        self.router = APIRouter(prefix="/vapi", tags=["vapi"])
        self.model_manager = model_manager
        self.vapi_api_key = vapi_api_key
        self.provider_service = ProviderService()
        self._setup_routes()
    
    def verify_vapi_auth(self, authorization: Annotated[str, Header()] = None):
        """Verify VAPI API key from Authorization header"""
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # Handle both "Bearer token" and "token" formats
        token = authorization.replace("Bearer ", "").strip()
        
        if token != self.vapi_api_key:
            logger.warning(f"Invalid VAPI API key attempt: {token[:10]}...")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return token
    
    def _setup_routes(self):
        """Setup VAPI-specific routes"""
        
        @self.router.get("/personas", response_model=List[Persona])
        async def personas():
            """Return list of personas filtered by model settings and current provider."""
            try:
                # Get current provider to determine which models to show
                try:
                    provider_settings = model_settings.get_provider_settings()
                    current_provider = provider_settings.get('default_provider', 'ollama')
                except Exception as e:
                    logger.warning(f"Failed to get provider settings: {e}, defaulting to ollama")
                    current_provider = 'ollama'
                
                logger.info(f"📋 Serving models for provider: {current_provider}")
                
                # Use provider service to get personas
                return await self.provider_service.get_personas_for_provider(current_provider)
                
            except Exception as e:
                logger.error(f"Error getting personas: {e}")
                # Return fallback personas
                return self.provider_service._get_fallback_personas()
        
        @self.router.post("/chat/completions", response_model=VAPIChatResponse)
        @self.router.post("/v1/chat/completions", response_model=VAPIChatResponse)
        async def vapi_chat_completions(
            request: VAPIChatRequest, 
            api_key: str = Depends(self.verify_vapi_auth)
        ):
            """VAPI Custom LLM endpoint - OpenAI-compatible chat completions"""
            try:
                start_time = time.time()
                
                # Extract the latest user message from the conversation
                user_messages = [msg for msg in request.messages if msg.role == "user"]
                if not user_messages:
                    raise HTTPException(status_code=400, detail="No user messages found")
                
                current_message = user_messages[-1].content
                
                # Build conversation context from message history
                context = ""
                for msg in request.messages[:-1]:  # All except the last message
                    if msg.role == "system":
                        context += f"System: {msg.content}\n\n"
                    elif msg.role == "user":
                        context += f"User: {msg.content}\n"
                    elif msg.role == "assistant":
                        context += f"Assistant: {msg.content}\n"
                
                # Use the specified model or fall back to the best Jamie model
                model_to_use = request.model
                if not model_to_use:
                    # Get the best Jamie model from settings
                    ui_models = model_settings.get_ui_models()
                    jamie_models = [m for m in ui_models if m.is_jamie_model]
                    model_to_use = jamie_models[0].name if jamie_models else "llama3:latest"
                
                # Get current provider from system config for comprehensive logging
                try:
                    from src.config.system_config import system_config
                    current_provider = system_config.config.default_provider
                    logger.info(f"🗣️ VAPI Chat Completion - Provider: {current_provider}, Model: {model_to_use}")
                    logger.info(f"📝 Message: {current_message[:50]}...")
                except Exception as e:
                    logger.warning(f"Could not get provider info: {e}")
                    logger.info(f"🗣️ VAPI Chat Completion - Model: {model_to_use}, Message: {current_message[:50]}...")
                
                # Generate AI response using the model manager
                ai_response = self.model_manager.generate_response(
                    current_message, 
                    model_name=model_to_use,
                    context=context
                )
                
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)
                
                # Get actual provider and model info for comprehensive logging
                try:
                    from src.config.system_config import system_config
                    actual_provider = system_config.config.default_provider
                    logger.info(f"✅ VAPI Chat Completion completed - Provider: {actual_provider}, Model: {model_to_use}")
                    logger.info(f"⏱️ Duration: {duration_ms}ms, Response length: {len(ai_response)} chars")
                except Exception as e:
                    logger.warning(f"Could not get provider info for logging: {e}")
                    logger.info(f"✅ VAPI Chat Completion completed - {duration_ms}ms, Model: {model_to_use}")
                
                # Log the interaction for training data with provider info
                try:
                    self._store_vapi_interaction({
                        'messages': [msg.dict() for msg in request.messages],
                        'model_used': model_to_use,
                        'provider_used': actual_provider if 'actual_provider' in locals() else 'unknown',
                        'response': ai_response,
                        'duration_ms': duration_ms,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Could not store interaction: {e}")
                
                # Create OpenAI-compatible response
                chat_response = VAPIChatResponse(
                    id="chatcmpl-" + str(hash(ai_response))[:8],
                    created=int(time.time()),
                    model=model_to_use,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ai_response
                        },
                        "finish_reason": "stop"
                    }],
                    usage={
                        "prompt_tokens": len(context.split()) + len(current_message.split()),
                        "completion_tokens": len(ai_response.split()),
                        "total_tokens": len(context.split()) + len(current_message.split()) + len(ai_response.split())
                    }
                )
                
                return chat_response
                
            except Exception as e:
                logger.error(f"VAPI chat completion error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/webhook")
        async def vapi_webhook(request: Request):
            """Main VAPI webhook endpoint"""
            try:
                # Get request body
                body = await request.json()
                
                # Log the incoming request
                logger.info(f"VAPI webhook received: {body.get('type', 'unknown')}")
                
                # Handle different VAPI event types
                event_type = body.get('type')
                
                if event_type == 'function-call':
                    return await self._handle_function_call(body)
                elif event_type == 'conversation-update':
                    return await self._handle_conversation_update(body)
                elif event_type == 'end-of-call-report':
                    return await self._handle_end_of_call(body)
                else:
                    logger.warning(f"Unknown VAPI event type: {event_type}")
                    return {"status": "ignored"}
            
            except Exception as e:
                logger.error(f"VAPI webhook error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/test/message")
        async def test_message(request: Request):
            """Test endpoint for direct message testing"""
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')  # optional specific model
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")
                
                # Generate AI response (model_name can be None)
                response = self.model_manager.generate_response(message, model_name=model_name)
                model_used = model_name or (
                    self.model_manager.custom_model_name 
                    if self.model_manager.is_model_available(self.model_manager.custom_model_name) 
                    else self.model_manager.model_name
                )
                
                # Store training data from this interaction
                self._store_training_data({
                    'conversation_id': f"test_{datetime.now().isoformat()}",
                    'message_index': 0,
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.now().isoformat(),
                    'model_used': model_used,
                    'validation_passed': True,
                    'similarity_score': 0.0
                })
                
                # Store AI response
                self._store_training_data({
                    'conversation_id': f"test_{datetime.now().isoformat()}",
                    'message_index': 1,
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat(),
                    'model_used': model_used,
                    'validation_passed': True,
                    'similarity_score': 0.0
                })
                
                return {
                    "user_message": message,
                    "ai_response": response,
                    "model_used": model_used
                }
            
            except Exception as e:
                logger.error(f"Test message error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/test/stream")
        async def test_stream(request: Request):
            """Stream AI response token-by-token (chunked plain text)."""
            import json
            
            start_time = time.time()
            request_id = f"req_{int(start_time)}_{hash(time.time()) % 10000}"
            
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")

                # Log request start
                logger.info(f"🔄 BENCHMARK [{request_id}] Starting stream - Model: {model_name}, Message: {message[:50]}...")
                
                # Collect the full response for logging
                full_response = ""
                token_count = 0
                first_token_time = None

                def token_iter():
                    nonlocal full_response, token_count, first_token_time
                    
                    for token in self.model_manager.generate_stream(message, model_name=model_name):
                        if first_token_time is None:
                            first_token_time = time.time()
                        
                        full_response += token
                        token_count += 1
                        yield token
                    
                    # Log complete response after streaming
                    end_time = time.time()
                    total_duration = end_time - start_time
                    first_token_latency = (first_token_time - start_time) if first_token_time else 0
                    
                    # Calculate performance metrics
                    tokens_per_second = token_count / total_duration if total_duration > 0 else 0
                    response_length = len(full_response)
                    words_count = len(full_response.split())
                    
                    # Create benchmark data
                    benchmark_data = {
                        "request_id": request_id,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "model": model_name or "unknown",
                        "user_message": message,
                        "ai_response": full_response,
                        "performance": {
                            "total_duration_ms": int(total_duration * 1000),
                            "first_token_latency_ms": int(first_token_latency * 1000),
                            "tokens_per_second": round(tokens_per_second, 2),
                            "token_count": token_count,
                            "response_length_chars": response_length,
                            "word_count": words_count
                        },
                        "quality_metrics": {
                            "response_relevance": "auto_analyze",
                            "response_completeness": "complete" if response_length > 50 else "brief",
                            "estimated_quality_score": min(10, max(1, (response_length / 100) + (words_count / 20)))
                        },
                        "source": "ui",
                        "status": "success"
                    }
                    
                    logger.info(f"📊 BENCHMARK [{request_id}] Complete - Duration: {total_duration:.2f}s, Tokens: {token_count}, TPS: {tokens_per_second:.2f}")
                    logger.info(f"📝 BENCHMARK [{request_id}] Response: {full_response[:100]}...")
                    
                    # Save to benchmark log file
                    self._save_benchmark_data(benchmark_data)
                
                return StreamingResponse(token_iter(), media_type='text/plain')
                
            except Exception as e:
                end_time = time.time()
                error_duration = end_time - start_time
                
                # Log error with benchmark data
                error_data = {
                    "request_id": request_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "model": model_name,
                    "user_message": message,
                    "error": str(e),
                    "duration_ms": int(error_duration * 1000),
                    "status": "error"
                }
                
                logger.error(f"❌ BENCHMARK [{request_id}] Error after {error_duration:.2f}s: {str(e)}")
                self._save_benchmark_data(error_data)
                
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _handle_function_call(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VAPI function call"""
        try:
            # Extract function call details
            function_call = body.get('functionCall', {})
            function_name = function_call.get('name')
            parameters = function_call.get('parameters', {})
            
            logger.info(f"Function call: {function_name} with params: {parameters}")
            
            # Handle property management functions
            if function_name == 'answer_property_question':
                question = parameters.get('question', '')
                caller_info = parameters.get('caller_info', {})
                
                # Generate AI response
                ai_response = self.model_manager.generate_response(question)
                
                return {
                    "result": {
                        "response": ai_response,
                        "action": "continue_conversation"
                    }
                }
            
            # Handle website search function
            elif function_name == 'search_website' or function_name == 'api_request_tool':
                website = parameters.get('website', '')
                
                if not website:
                    return {
                        "result": {
                            "response": "I need a website URL to search for rental properties. Please provide a website.",
                            "action": "continue_conversation"
                        }
                    }
                
                logger.info(f"🔍 Searching website: {website}")
                
                try:
                    # Import DuckDuckGo search
                    from duckduckgo_search import DDGS
                    
                    # Try multiple search strategies
                    search_queries = [
                        f"site:{website} rental properties available",
                        f"site:{website} apartments rent",
                        f"{website} rental listings",
                        f"properties for rent {website.split('//')[1] if '//' in website else website}"
                    ]
                    
                    all_results = []
                    
                    # Search with multiple strategies
                    for query in search_queries:
                        try:
                            with DDGS() as ddgs:
                                results = list(ddgs.text(query, max_results=3))
                                for result in results:
                                    if result not in all_results:
                                        all_results.append(result)
                        except Exception as search_error:
                            logger.warning(f"Search query failed: {query} - {search_error}")
                            continue
                    
                    if all_results:
                        # Format results for voice response
                        domain = website.replace('https://', '').replace('http://', '').split('/')[0]
                        response = f"I found {len(all_results)} listings related to {domain}. "
                        
                        # Add top 3 results with key details
                        for i, result in enumerate(all_results[:3], 1):
                            title = result.get('title', 'Property listing')
                            snippet = result.get('body', '')
                            
                            # Extract rent info if available
                            import re
                            rent_match = re.search(r'\$[\d,]+', snippet)
                            bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', snippet.lower())
                            
                            response += f"{i}. {title[:50]}{'...' if len(title) > 50 else ''}. "
                            
                            if rent_match or bed_match:
                                details = []
                                if rent_match:
                                    details.append(f"Rent {rent_match.group()}")
                                if bed_match:
                                    details.append(f"{bed_match.group(1)} bedroom")
                                response += f"{', '.join(details)}. "
                        
                        response += "Would you like more details about any of these properties?"
                        
                        logger.info(f"✅ Search successful: {len(all_results)} results for {website}")
                        
                        return {
                            "result": {
                                "response": response,
                                "action": "continue_conversation"
                            }
                        }
                    else:
                        # Fallback: general area search
                        domain = website.replace('https://', '').replace('http://', '').split('/')[0]
                        fallback_query = f"rental properties apartments {domain}"
                        
                        try:
                            with DDGS() as ddgs:
                                fallback_results = list(ddgs.text(fallback_query, max_results=3))
                                
                            if fallback_results:
                                response = f"I couldn't find specific listings on {domain}, but I found {len(fallback_results)} rental resources in the area. "
                                response += "These might help you find available properties. Would you like me to search for more specific criteria?"
                            else:
                                response = f"I wasn't able to find current rental listings for {domain}. The website might not have publicly searchable content, or there may not be available properties right now. I recommend contacting them directly for the most up-to-date availability."
                                
                        except Exception:
                            response = f"I'm having trouble accessing rental information for {domain} right now. I recommend visiting their website directly or calling them for current availability."
                        
                        return {
                            "result": {
                                "response": response,
                                "action": "continue_conversation"
                            }
                        }
                        
                except Exception as e:
                    logger.error(f"❌ Website search error: {str(e)}")
                    return {
                        "result": {
                            "response": "I'm having trouble searching for rental properties right now. Please try again in a moment, or I can help you with other property management questions.",
                            "action": "continue_conversation"
                        }
                    }
            
            else:
                return {
                    "result": {
                        "response": "I can help you with property management questions. What would you like to know?",
                        "action": "continue_conversation"
                    }
                }
        
        except Exception as e:
            logger.error(f"Function call error: {str(e)}")
            return {
                "result": {
                    "response": "I'm experiencing technical difficulties. Please try again.",
                    "action": "continue_conversation"
                }
            }
    
    async def _handle_conversation_update(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation updates"""
        try:
            conversation = body.get('conversation', {})
            logger.info(f"Conversation update: {len(conversation.get('messages', []))} messages")
            
            # Store conversation in database for learning
            self._store_conversation_update(conversation)
            
            return {"status": "recorded"}
        
        except Exception as e:
            logger.error(f"Conversation update error: {str(e)}")
            return {"status": "error"}
    
    async def _handle_end_of_call(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle end of call reporting"""
        try:
            call_data = body.get('call', {})
            logger.info(f"Call ended: {call_data.get('id')} duration: {call_data.get('duration')}s")
            
            # Store complete call data for analysis
            self._store_call_data(call_data)
            
            return {"status": "recorded"}
        
        except Exception as e:
            logger.error(f"End of call error: {str(e)}")
            return {"status": "error"}
    
    def _store_conversation_update(self, conversation: Dict[str, Any]):
        """Store conversation update in database for training data capture"""
        try:
            # Extract conversation data
            messages = conversation.get('messages', [])
            conversation_id = conversation.get('id', 'unknown')
            timestamp = conversation.get('timestamp', datetime.now().isoformat())
            
            # Store each message for training analysis
            for i, message in enumerate(messages):
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                
                # Store training data
                self._store_training_data({
                    'conversation_id': conversation_id,
                    'message_index': i,
                    'role': role,
                    'content': content,
                    'timestamp': timestamp,
                    'model_used': conversation.get('model', 'unknown'),
                    'validation_passed': conversation.get('validation_passed', False),
                    'similarity_score': conversation.get('similarity_score', 0.0)
                })
            
            logger.info(f"💾 Stored {len(messages)} messages from conversation {conversation_id}")
        
        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}")
    
    def _store_call_data(self, call_data: Dict[str, Any]):
        """Store complete call data for analysis"""
        try:
            call_id = call_data.get('id', 'unknown')
            duration = call_data.get('duration', 0)
            transcript = call_data.get('transcript', '')
            
            # Store call metadata
            call_metadata = {
                'call_id': call_id,
                'duration': duration,
                'transcript': transcript,
                'timestamp': datetime.now().isoformat(),
                'model_used': call_data.get('model', 'unknown'),
                'validation_passed': call_data.get('validation_passed', False),
                'similarity_score': call_data.get('similarity_score', 0.0)
            }
            
            # Store training data
            self._store_training_data(call_metadata)
            
            logger.info(f"💾 Stored call data: {call_id} ({duration}s)")
        
        except Exception as e:
            logger.error(f"Error storing call data: {str(e)}")
    
    def _store_training_data(self, data: Dict[str, Any]):
        """Store training data in database for model improvement"""
        # This would normally use a proper database service
        # For now, just log the data
        logger.info(f"Training data stored: {data}")
    
    def _store_vapi_interaction(self, data: Dict[str, Any]):
        """Store VAPI chat completion interaction for analysis"""
        # This would normally use a proper database service
        # For now, just log the data
        logger.info(f"VAPI interaction stored: {data}")
    
    def _save_benchmark_data(self, benchmark_data: dict):
        """Save benchmark data to log file for analysis"""
        import json
        import os
        from pathlib import Path
        
        try:
            # Ensure logs directory exists
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Create benchmark log file with date
            log_file = logs_dir / f"benchmark_{time.strftime('%Y-%m-%d')}.jsonl"
            
            # Append benchmark data as JSON line
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(benchmark_data) + '\n')
                
            logger.info(f"💾 SAVED BENCHMARK: {benchmark_data['model']} - {benchmark_data['performance']['total_duration_ms']}ms")
                
        except Exception as e:
            logger.error(f"Failed to save benchmark data: {e}")

def create_vapi_router(model_manager: ModelManager, vapi_api_key: str) -> APIRouter:
    """Factory function to create VAPI router"""
    vapi_router = VAPIRouter(model_manager, vapi_api_key)
    return vapi_router.router
