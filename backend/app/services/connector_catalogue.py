"""Explicit connector capabilities. No execution paths or secret handling in this milestone."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

ConnectorKind = Literal['sql','nosql','cloud','object_storage','api','mcp','documents']
Provider = Literal['postgresql','mysql','sqlserver','mongodb','dynamodb','aws','azure','gcp','s3','azure_blob','gcs','generic_api','mcp_server','uploaded_documents']
PROVIDERS: dict[str, str] = {
 'postgresql':'sql','mysql':'sql','sqlserver':'sql','mongodb':'nosql','dynamodb':'nosql',
 'aws':'cloud','azure':'cloud','gcp':'cloud','s3':'object_storage','azure_blob':'object_storage',
 'gcs':'object_storage','generic_api':'api','mcp_server':'mcp','uploaded_documents':'documents',
}

class ConnectorRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    display_name: str = Field(min_length=2,max_length=120,pattern=r'^[^\x00-\x1f]+$')
    kind: ConnectorKind
    provider: Provider
    purpose: str = Field(default='Demonstration connector metadata', min_length=10, max_length=300, pattern=r'^[^\x00-\x1f]+$')
    data_classification: Literal['public', 'internal', 'confidential', 'restricted'] = 'internal'


def validate_pair(kind: str, provider: str) -> bool:
    return PROVIDERS.get(provider) == kind


def catalogue():
    return [{'provider':p,'kind':k,'registration_supported':True,'execution_supported':False,'credentials_supported':False} for p,k in sorted(PROVIDERS.items())]
