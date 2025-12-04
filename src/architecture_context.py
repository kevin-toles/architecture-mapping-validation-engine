"""
Architecture Context
====================

Static architecture context for the LLM Document Enhancer.
Defines all components, relationships, entities, and processes.

This is observability metadata that describes the system architecture.
It does NOT contain execution logic - only static definitions.

Reference: DESIGN_DOCUMENT.md - Core Components section
"""

import os
import platform
import socket
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .data_classes import (
    Component,
    EntityDefinition,
    ProcessDefinition,
    Relationship,
)


def get_architecture_context() -> Dict[str, List[Any]]:
    """
    Return complete architecture context for the LLM Document Enhancer.
    
    This is static configuration that describes the system architecture.
    
    Returns:
        Dictionary with keys: services, endpoints, databases, 
        external_systems, relationships, entities, processes
    """
    
    # ==========
    # SERVICES
    # ==========
    services = [
        Component(
            component_id="svc_pdf_converter",
            component_kind="Service",
            name="PDF to JSON Converter",
            description="Converts PDF documents to structured JSON with chapter segmentation",
            owner_team="document-processing",
            inputs=["entity_pdf_document"],
            outputs=["entity_json_text", "entity_chapter_segments"]
        ),
        Component(
            component_id="svc_metadata_extractor",
            component_kind="Service",
            name="Metadata Extraction Service",
            description="Extracts keywords, concepts, and summaries using YAKE and Summa",
            owner_team="nlp-platform",
            inputs=["entity_json_text", "entity_chapter_segments"],
            outputs=["entity_book_metadata"]
        ),
        Component(
            component_id="svc_taxonomy_builder",
            component_kind="Service",
            name="Taxonomy Builder Service",
            description="Builds hierarchical taxonomy from extracted metadata",
            owner_team="knowledge-graph",
            inputs=["entity_book_metadata"],
            outputs=["entity_taxonomy"]
        ),
        Component(
            component_id="svc_metadata_enricher",
            component_kind="Service",
            name="Metadata Enrichment Service",
            description="Enriches metadata with cross-book references using TF-IDF similarity",
            owner_team="nlp-platform",
            inputs=["entity_book_metadata", "entity_taxonomy"],
            outputs=["entity_enriched_metadata"]
        ),
        Component(
            component_id="svc_guideline_generator",
            component_kind="Service",
            name="Guideline Generator Service",
            description="Generates base guidelines from enriched metadata",
            owner_team="content-generation",
            inputs=["entity_enriched_metadata"],
            outputs=["entity_base_guideline"]
        ),
        Component(
            component_id="svc_llm_enhancer",
            component_kind="Service",
            name="LLM Enhancement Service",
            description="Enhances guidelines using multiple LLM providers",
            owner_team="llm-platform",
            inputs=["entity_base_guideline"],
            outputs=["entity_enhanced_guideline"]
        ),
        Component(
            component_id="svc_statistical_extractor",
            component_kind="Service",
            name="Statistical Extractor Adapter",
            description="Adapts YAKE and Summa libraries for keyword/concept extraction",
            owner_team="nlp-platform",
            inputs=["entity_chapter_text"],
            outputs=["entity_keywords", "entity_concepts"]
        ),
    ]
    
    # ==========
    # ENDPOINTS (for future HTTP API)
    # ==========
    endpoints = [
        Component(
            component_id="ep_pdf_upload",
            component_kind="Endpoint",
            name="PDF Upload Endpoint",
            description="Accepts PDF file uploads for processing",
            service_id="svc_pdf_converter",
            protocol="http",
            method="POST",
            path="/api/v1/documents/upload",
            consumes=["entity_pdf_document"],
            produces=["entity_json_text"]
        ),
        Component(
            component_id="ep_extract_metadata",
            component_kind="Endpoint",
            name="Metadata Extraction Endpoint",
            description="Triggers metadata extraction for a document",
            service_id="svc_metadata_extractor",
            protocol="http",
            method="POST",
            path="/api/v1/metadata/extract",
            consumes=["entity_json_text"],
            produces=["entity_book_metadata"]
        ),
        Component(
            component_id="ep_enrich_metadata",
            component_kind="Endpoint",
            name="Metadata Enrichment Endpoint",
            description="Triggers cross-book enrichment",
            service_id="svc_metadata_enricher",
            protocol="http",
            method="POST",
            path="/api/v1/metadata/enrich",
            consumes=["entity_book_metadata", "entity_taxonomy"],
            produces=["entity_enriched_metadata"]
        ),
        Component(
            component_id="ep_generate_guideline",
            component_kind="Endpoint",
            name="Guideline Generation Endpoint",
            description="Generates base guideline from enriched metadata",
            service_id="svc_guideline_generator",
            protocol="http",
            method="POST",
            path="/api/v1/guidelines/generate",
            consumes=["entity_enriched_metadata"],
            produces=["entity_base_guideline"]
        ),
        Component(
            component_id="ep_enhance_guideline",
            component_kind="Endpoint",
            name="LLM Enhancement Endpoint",
            description="Enhances guideline using LLMs",
            service_id="svc_llm_enhancer",
            protocol="http",
            method="POST",
            path="/api/v1/guidelines/enhance",
            consumes=["entity_base_guideline"],
            produces=["entity_enhanced_guideline"]
        ),
    ]
    
    # ==========
    # DATABASES
    # ==========
    databases = [
        Component(
            component_id="db_document_store",
            component_kind="Database",
            name="Document Store",
            description="Stores PDF documents and JSON text outputs",
            engine="filesystem"
        ),
        Component(
            component_id="db_metadata_store",
            component_kind="Database",
            name="Metadata Store",
            description="Stores extracted metadata JSON files",
            engine="filesystem"
        ),
        Component(
            component_id="db_taxonomy_store",
            component_kind="Database",
            name="Taxonomy Store",
            description="Stores taxonomy JSON files",
            engine="filesystem"
        ),
        Component(
            component_id="db_guideline_store",
            component_kind="Database",
            name="Guideline Store",
            description="Stores generated guideline documents",
            engine="filesystem"
        ),
        Component(
            component_id="db_llm_cache",
            component_kind="Database",
            name="LLM Response Cache",
            description="Caches LLM API responses",
            engine="filesystem"
        ),
    ]
    
    # ==========
    # EXTERNAL SYSTEMS
    # ==========
    external_systems = [
        Component(
            component_id="ext_openai_api",
            component_kind="ExternalSystem",
            name="OpenAI API",
            description="GPT-4o LLM provider",
            contact_type="http",
            base_url="https://api.openai.com"
        ),
        Component(
            component_id="ext_anthropic_api",
            component_kind="ExternalSystem",
            name="Anthropic API",
            description="Claude LLM provider",
            contact_type="http",
            base_url="https://api.anthropic.com"
        ),
        Component(
            component_id="ext_gemini_api",
            component_kind="ExternalSystem",
            name="Google Gemini API",
            description="Gemini LLM provider",
            contact_type="http",
            base_url="https://generativelanguage.googleapis.com"
        ),
        Component(
            component_id="ext_deepseek_api",
            component_kind="ExternalSystem",
            name="DeepSeek API",
            description="DeepSeek LLM provider",
            contact_type="http",
            base_url="https://api.deepseek.com"
        ),
    ]
    
    # ==========
    # RELATIONSHIPS
    # ==========
    relationships = [
        # Services expose endpoints
        Relationship("svc_pdf_converter", "ep_pdf_upload", "EXPOSES"),
        Relationship("svc_metadata_extractor", "ep_extract_metadata", "EXPOSES"),
        Relationship("svc_metadata_enricher", "ep_enrich_metadata", "EXPOSES"),
        Relationship("svc_guideline_generator", "ep_generate_guideline", "EXPOSES"),
        Relationship("svc_llm_enhancer", "ep_enhance_guideline", "EXPOSES"),
        
        # Services write to databases
        Relationship("svc_pdf_converter", "db_document_store", "WRITES_TO"),
        Relationship("svc_metadata_extractor", "db_metadata_store", "WRITES_TO"),
        Relationship("svc_taxonomy_builder", "db_taxonomy_store", "WRITES_TO"),
        Relationship("svc_guideline_generator", "db_guideline_store", "WRITES_TO"),
        Relationship("svc_llm_enhancer", "db_llm_cache", "WRITES_TO"),
        
        # Services read from databases
        Relationship("svc_metadata_extractor", "db_document_store", "READS_FROM"),
        Relationship("svc_metadata_enricher", "db_metadata_store", "READS_FROM"),
        Relationship("svc_metadata_enricher", "db_taxonomy_store", "READS_FROM"),
        Relationship("svc_guideline_generator", "db_metadata_store", "READS_FROM"),
        Relationship("svc_llm_enhancer", "db_llm_cache", "READS_FROM"),
        
        # LLM enhancer integrates with external APIs
        Relationship("svc_llm_enhancer", "ext_openai_api", "INTEGRATES_WITH"),
        Relationship("svc_llm_enhancer", "ext_anthropic_api", "INTEGRATES_WITH"),
        Relationship("svc_llm_enhancer", "ext_gemini_api", "INTEGRATES_WITH"),
        Relationship("svc_llm_enhancer", "ext_deepseek_api", "INTEGRATES_WITH"),
    ]
    
    # ==========
    # DOMAIN ENTITIES
    # ==========
    entities = [
        EntityDefinition(
            entity_id="entity_pdf_document",
            name="PDF Document",
            description="Source PDF file for processing",
            states=["uploaded", "processing", "converted", "failed"],
            primary_key="document_id"
        ),
        EntityDefinition(
            entity_id="entity_json_text",
            name="JSON Text",
            description="Extracted text from PDF in JSON format",
            states=["pending", "extracted", "validated"],
            primary_key="json_id"
        ),
        EntityDefinition(
            entity_id="entity_chapter_segments",
            name="Chapter Segments",
            description="Identified chapter boundaries with page ranges",
            states=["detected", "validated"],
            primary_key="segment_id"
        ),
        EntityDefinition(
            entity_id="entity_book_metadata",
            name="Book Metadata",
            description="Extracted keywords, concepts, summaries per chapter",
            states=["pending", "extracted", "validated"],
            primary_key="metadata_id"
        ),
        EntityDefinition(
            entity_id="entity_taxonomy",
            name="Taxonomy",
            description="Hierarchical classification of topics and concepts",
            states=["pending", "built", "validated"],
            primary_key="taxonomy_id"
        ),
        EntityDefinition(
            entity_id="entity_enriched_metadata",
            name="Enriched Metadata",
            description="Metadata with cross-book references and topic clusters",
            states=["pending", "enriched", "validated"],
            primary_key="enriched_id"
        ),
        EntityDefinition(
            entity_id="entity_base_guideline",
            name="Base Guideline",
            description="Generated guideline document before LLM enhancement",
            states=["pending", "generated", "validated"],
            primary_key="guideline_id"
        ),
        EntityDefinition(
            entity_id="entity_enhanced_guideline",
            name="Enhanced Guideline",
            description="LLM-enhanced guideline document",
            states=["pending", "enhanced", "validated", "failed"],
            primary_key="enhanced_id"
        ),
        EntityDefinition(
            entity_id="entity_aggregate",
            name="Evaluation Aggregate",
            description="Aggregated extraction metrics for LLM evaluation",
            states=["pending", "created", "validated"],
            primary_key="aggregate_id"
        ),
    ]
    
    # ==========
    # BUSINESS PROCESSES
    # ==========
    processes = [
        ProcessDefinition(
            process_id="proc_document_ingestion",
            name="Document Ingestion",
            description="Ingest PDF document and convert to structured JSON",
            trigger_type="user_action",
            trigger_source="frontend_app",
            success_criteria="JSON text created with chapter segments",
            failure_criteria="PDF conversion fails or no chapters detected"
        ),
        ProcessDefinition(
            process_id="proc_metadata_extraction",
            name="Metadata Extraction",
            description="Extract keywords, concepts, summaries from document",
            trigger_type="internal_event",
            trigger_source="document_ingestion",
            success_criteria="Metadata JSON created with keywords and concepts",
            failure_criteria="Extraction produces empty results"
        ),
        ProcessDefinition(
            process_id="proc_taxonomy_building",
            name="Taxonomy Building",
            description="Build hierarchical taxonomy from metadata",
            trigger_type="internal_event",
            trigger_source="metadata_extraction",
            success_criteria="Taxonomy JSON with valid tier structure",
            failure_criteria="Taxonomy generation fails"
        ),
        ProcessDefinition(
            process_id="proc_enrichment",
            name="Metadata Enrichment",
            description="Enrich metadata with cross-book references",
            trigger_type="internal_event",
            trigger_source="taxonomy_building",
            success_criteria="Enriched metadata with related chapters",
            failure_criteria="Enrichment produces no cross-references"
        ),
        ProcessDefinition(
            process_id="proc_guideline_generation",
            name="Guideline Generation",
            description="Full pipeline from metadata to enhanced guideline",
            trigger_type="user_action",
            trigger_source="frontend_app",
            success_criteria="Enhanced guideline document created",
            failure_criteria="Any pipeline step fails"
        ),
        ProcessDefinition(
            process_id="proc_extraction_evaluation",
            name="Extraction Evaluation",
            description="Run 4-profile extraction test with LLM evaluation",
            trigger_type="user_action",
            trigger_source="observability_runner",
            success_criteria="All 4 aggregates created and LLMs evaluate",
            failure_criteria="Profile extraction fails or LLM calls error"
        ),
    ]
    
    return {
        "services": services,
        "endpoints": endpoints,
        "databases": databases,
        "external_systems": external_systems,
        "relationships": relationships,
        "entities": entities,
        "processes": processes,
    }


def get_runtime_context() -> Dict[str, Any]:
    """
    Get current runtime/infrastructure context.
    
    Returns info about the host machine, Python environment, etc.
    """
    return {
        "component_id": f"node_{socket.gethostname().replace('.', '_').lower()}",
        "component_kind": "InfraNode",
        "provider": "local",
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "cwd": str(Path.cwd()),
        "user": os.environ.get("USER", "unknown"),
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }


def log_architecture_context() -> int:
    """
    Log all architecture context records to JSONL.
    
    This includes services, endpoints, databases, entities, processes, etc.
    Should be called once at the start of a run.
    
    Returns:
        Number of records logged
    """
    from .jsonl_logger import log_records, now_iso, SCHEMA_VERSION, GENERATOR_ID
    
    print("\n📐 Logging architecture context...")
    
    context = get_architecture_context()
    runtime = get_runtime_context()
    
    records = []
    
    # Meta record
    records.append({
        "record_type": "meta",
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATOR_ID,
        "created_at": now_iso(),
    })
    
    # Runtime context
    records.append({
        "record_type": "component",
        **runtime,
    })
    
    # Components (services, endpoints, databases, external systems)
    for component_list_name in ["services", "endpoints", "databases", "external_systems"]:
        for component in context[component_list_name]:
            record = {"record_type": "component"}
            record.update({k: v for k, v in asdict(component).items() if v is not None})
            records.append(record)
    
    # Relationships
    for rel in context["relationships"]:
        records.append({
            "record_type": "relationship",
            "from_id": rel.from_id,
            "to_id": rel.to_id,
            "relationship_type": rel.relationship_type,
        })
    
    # Entity definitions
    for entity in context["entities"]:
        record = {"record_type": "entity_definition"}
        record.update({k: v for k, v in asdict(entity).items() if v is not None})
        records.append(record)
    
    # Process definitions
    for process in context["processes"]:
        record = {"record_type": "process_definition"}
        record.update({k: v for k, v in asdict(process).items() if v is not None})
        records.append(record)
    
    # Write all records
    log_records(records)
    
    print(f"  ✅ Logged {len(records)} architecture records")
    
    return len(records)
