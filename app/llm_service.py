"""
LLM Integration Service

This module provides integration with Large Language Model APIs for structured
data extraction from documents. Supports both OpenAI and Anthropic providers
with configurable parameters.

Features:
- Multi-provider support (OpenAI, Anthropic)
- Template-based prompt system
- JSON schema validation
- Robust error handling and response parsing

Author: Generated with Claude Code
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import openai
import anthropic
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration model for LLM service settings."""
    provider: str  # "openai" or "anthropic"
    model: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 4000

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        
        if config.provider == "openai":
            self.client = openai.OpenAI(api_key=config.api_key)
        elif config.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=config.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    def extract_data(
        self, 
        document_text: str, 
        system_prompt: str, 
        user_prompt_template: str, 
        json_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from document using LLM
        
        Args:
            document_text: The text content of the document
            system_prompt: System-level instructions for the LLM
            user_prompt_template: Template for user prompt (can include {document} placeholder)
            json_schema: Expected JSON schema for the output
            
        Returns:
            Dict with extraction results
        """
        start_time = datetime.utcnow()
        
        try:
            # Format the user prompt with document text - handle templates safely
            try:
                user_prompt = user_prompt_template.format(document=document_text)
            except KeyError as e:
                # If template has other braces, use simple replacement
                logger.warning(f"Template formatting failed with KeyError {e}, using simple replacement")
                user_prompt = user_prompt_template.replace("{document}", document_text)
            
            # Add JSON schema instruction to system prompt
            schema_instruction = f"\n\nYou must respond with valid JSON that conforms to this schema:\n{json.dumps(json_schema, indent=2)}"
            full_system_prompt = system_prompt + schema_instruction
            
            if self.config.provider == "openai":
                response = self._call_openai(full_system_prompt, user_prompt)
            elif self.config.provider == "anthropic":
                response = self._call_anthropic(full_system_prompt, user_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Parse and validate JSON response
            try:
                # Clean response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()
                
                logger.info(f"Raw LLM response: {response[:200]}...")
                logger.info(f"Cleaned response: {cleaned_response[:200]}...")
                
                extracted_data = json.loads(cleaned_response)
                self._validate_against_schema(extracted_data, json_schema)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Invalid JSON response from LLM: {e}")
                logger.error(f"Full raw response: {response}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(e)}",
                    "raw_response": response,
                    "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            
            return {
                "success": True,
                "extracted_data": extracted_data,
                "raw_response": response,
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
            }
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        try:
            logger.info(f"Calling OpenAI with model: {self.config.model}")
            logger.info(f"System prompt length: {len(system_prompt)}")
            logger.info(f"User prompt length: {len(user_prompt)}")
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI response received, length: {len(content) if content else 0}")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.config.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.content[0].text
    
    def _validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Basic JSON schema validation"""
        # This is a simplified validation - in production, use jsonschema library
        if "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    raise ValidationError(f"Required field '{field}' missing from response")
        
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in data:
                    expected_type = field_schema.get("type")
                    if expected_type == "string" and not isinstance(data[field], str):
                        raise ValidationError(f"Field '{field}' should be string")
                    elif expected_type == "number" and not isinstance(data[field], (int, float)):
                        raise ValidationError(f"Field '{field}' should be number")
                    elif expected_type == "array" and not isinstance(data[field], list):
                        raise ValidationError(f"Field '{field}' should be array")