#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: MIT
#

"""Chunker implementation with improved heading breadcrumb support."""

from __future__ import annotations

import logging
import re
from typing import Any, ClassVar, Final, Iterator, Literal, Optional

from pydantic import ConfigDict, Field, StringConstraints, field_validator
from typing_extensions import Annotated, override

from docling_core.experimental.serializer.base import (
    BaseDocSerializer,
    BaseSerializerProvider,
    BaseTableSerializer,
    SerializationResult,
)
from docling_core.experimental.serializer.common import create_ser_result
from docling_core.experimental.serializer.markdown import (
    MarkdownDocSerializer,
    MarkdownParams,
)
from docling_core.search.package import VERSION_PATTERN
from docling_core.transforms.chunker import BaseChunk, BaseChunker, BaseMeta
from docling_core.types import DoclingDocument as DLDocument
from docling_core.types.doc.base import ImageRefMode
from docling_core.types.doc.document import (
    DocItem,
    DoclingDocument,
    DocumentOrigin,
    InlineGroup,
    LevelNumber,
    OrderedList,
    SectionHeaderItem,
    TableItem,
    TitleItem,
    UnorderedList,
    PictureItem,
)

_VERSION: Final = "1.0.0"

_KEY_SCHEMA_NAME = "schema_name"
_KEY_VERSION = "version"
_KEY_DOC_ITEMS = "doc_items"
_KEY_HEADINGS = "headings"
_KEY_CAPTIONS = "captions"
_KEY_ORIGIN = "origin"

_logger = logging.getLogger(__name__)


class DocMeta(BaseMeta):
    """Data model for Hierarchical Chunker chunk metadata."""

    schema_name: Literal["docling_core.transforms.chunker.DocMeta"] = Field(
        default="docling_core.transforms.chunker.DocMeta",
        alias=_KEY_SCHEMA_NAME,
    )
    version: Annotated[str, StringConstraints(pattern=VERSION_PATTERN, strict=True)] = (
        Field(
            default=_VERSION,
            alias=_KEY_VERSION,
        )
    )
    doc_items: list[DocItem] = Field(
        alias=_KEY_DOC_ITEMS,
        min_length=1,
    )
    headings: Optional[str] = Field(
        default=None,
        alias=_KEY_HEADINGS,
    )
    chunk_type: Literal["text", "image", "table"] = Field(
        default="text", 
        description="Type of content in the chunk."
    )
    image_path: Optional[str] = Field(
        default=None, 
        description="Relative path to the image file, if chunk_type is 'image'."
    )
    captions: Optional[list[str]] = Field(  # deprecated
        deprecated=True,
        default=None,
        alias=_KEY_CAPTIONS,
        min_length=1,
    )
    origin: Optional[DocumentOrigin] = Field(
        default=None,
        alias=_KEY_ORIGIN,
    )

    excluded_embed: ClassVar[list[str]] = [
        _KEY_SCHEMA_NAME,
        _KEY_VERSION,
        _KEY_DOC_ITEMS,
        _KEY_ORIGIN,
        # Exclude new fields if they shouldn't be in embeddings
        "chunk_type", 
        "image_path", 
    ]
    excluded_llm: ClassVar[list[str]] = [
        _KEY_SCHEMA_NAME,
        _KEY_VERSION,
        _KEY_DOC_ITEMS,
        _KEY_ORIGIN,
        # Exclude new fields from LLM context if desired
        "chunk_type", 
        "image_path",
    ]

    @field_validator(_KEY_VERSION)
    @classmethod
    def check_version_is_compatible(cls, v: str) -> str:
        """Check if this meta item version is compatible with current version."""
        current_match = re.match(VERSION_PATTERN, _VERSION)
        doc_match = re.match(VERSION_PATTERN, v)
        if (
            doc_match is None
            or current_match is None
            or doc_match["major"] != current_match["major"]
            or doc_match["minor"] > current_match["minor"]
        ):
            raise ValueError(f"incompatible version {v} with schema version {_VERSION}")
        else:
            return _VERSION


class DocChunk(BaseChunk):
    """Data model for document chunks."""

    meta: DocMeta


class TripletTableSerializer(BaseTableSerializer):
    """Triplet-based table item serializer."""

    @override
    def serialize(
        self,
        *,
        item: TableItem,
        doc_serializer: BaseDocSerializer,
        doc: DoclingDocument,
        **kwargs,
    ) -> SerializationResult:
        """Serializes the passed item."""
        parts: list[SerializationResult] = []

        cap_res = doc_serializer.serialize_captions(
            item=item,
            **kwargs,
        )
        if cap_res.text:
            parts.append(cap_res)

        if item.self_ref not in doc_serializer.get_excluded_refs(**kwargs):
            table_df = item.export_to_dataframe()
            if table_df.shape[0] >= 1 and table_df.shape[1] >= 2:

                # copy header as first row and shift all rows by one
                table_df.loc[-1] = table_df.columns  # type: ignore[call-overload]
                table_df.index = table_df.index + 1
                table_df = table_df.sort_index()

                rows = [str(item).strip() for item in table_df.iloc[:, 0].to_list()]
                cols = [str(item).strip() for item in table_df.iloc[0, :].to_list()]

                nrows = table_df.shape[0]
                ncols = table_df.shape[1]
                table_text_parts = [
                    f"{rows[i]}, {cols[j]} = {str(table_df.iloc[i, j]).strip()}"
                    for i in range(1, nrows)
                    for j in range(1, ncols)
                ]
                table_text = ". ".join(table_text_parts)
                parts.append(create_ser_result(text=table_text, span_source=item))

        text_res = "\n\n".join([r.text for r in parts])

        return create_ser_result(text=text_res, span_source=parts)


class ChunkingDocSerializer(MarkdownDocSerializer):
    """Doc serializer used for chunking purposes."""

    table_serializer: BaseTableSerializer = TripletTableSerializer()
    params: MarkdownParams = MarkdownParams(
        image_mode=ImageRefMode.PLACEHOLDER,
        image_placeholder="",
        escape_underscores=False,
        escape_html=False,
    )


class ChunkingSerializerProvider(BaseSerializerProvider):
    """Serializer provider used for chunking purposes."""

    @override
    def get_serializer(self, doc: DoclingDocument) -> BaseDocSerializer:
        """Get the associated serializer."""
        return ChunkingDocSerializer(doc=doc)


class BreadcrumbChunker(BaseChunker):
    r"""Chunker implementation leveraging the document layout with improved breadcrumb support.

    This chunker creates complete breadcrumb paths for all headings, properly handling
    both numbered and unnumbered headings to maintain the correct hierarchical structure.

    Args:
        merge_list_items (bool): Whether to merge successive list items.
            Defaults to True.
        delim (str): Delimiter to use for merging text. Defaults to "\n".
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    serializer_provider: BaseSerializerProvider = ChunkingSerializerProvider()

    # deprecated:
    merge_list_items: Annotated[bool, Field(deprecated=True)] = True
    
    @staticmethod
    def _extract_heading_level(heading_text: str) -> tuple[int, bool]:
        """
        Extract the numeric level from a heading text based on its numbering pattern.
        
        Args:
            heading_text: The text of the heading
            
        Returns:
            tuple: (numeric_level, is_numbered) where numeric_level is an integer 
                   representation of the heading's depth and is_numbered indicates 
                   if it has explicit numbering
        """
        # Try to extract section number (e.g., "3.2.1." or "3.2" or just "3")
        match = re.match(r'^(\d+(?:\.\d+)*)\.?', heading_text)
        if match:
            # Count the depth based on number of dot separators + 1
            section_number = match.group(1)
            level = section_number.count('.') + 1
            return level, True
        
        # Not a numbered heading
        return 0, False

    def chunk(
        self,
        dl_doc: DLDocument,
        image_ref_map: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Iterator[BaseChunk]:
        r"""Chunk the provided document.

        Args:
            dl_doc (DLDocument): document to chunk
            image_ref_map (Optional[dict[str, str]]): A map where keys are image item 
                self_refs (#/pictures/X) and values are their relative output paths.

        Yields:
            Iterator[Chunk]: iterator over extracted chunks
        """
        my_doc_ser = self.serializer_provider.get_serializer(doc=dl_doc)
        heading_by_level: dict[LevelNumber, str] = {}
        last_significant_heading_level = -1
        last_significant_heading = ""
        visited: set[str] = set()
        excluded_refs = my_doc_ser.get_excluded_refs(**kwargs)
        _image_ref_map = image_ref_map if image_ref_map is not None else {}

        for item, _ in dl_doc.iterate_items(with_groups=True):
            if item.self_ref in excluded_refs or item.self_ref in visited:
                continue

            # --- 1. Handle Headings & Update Context --- 
            if isinstance(item, (TitleItem, SectionHeaderItem)):
                # First get the level from the document structure
                doc_level = item.level if isinstance(item, SectionHeaderItem) else 0
                
                # Also check if there's a numeric section identifier in the heading text
                numeric_level, is_numbered = self._extract_heading_level(item.text)
                
                # Determine if this is a simple unnumbered heading (like "Shall")
                is_simple_heading = not is_numbered and len(item.text.split()) <= 2
                
                if is_simple_heading and last_significant_heading:
                    # This is a simple heading - nest it under the last significant heading
                    parent_path = heading_by_level.get(last_significant_heading_level, "")
                    
                    # Create full breadcrumb
                    current_path = f"{parent_path} > {item.text}" if parent_path else item.text
                    
                    # Use a synthetic level deeper than the parent
                    synthetic_level = last_significant_heading_level + 1
                    heading_by_level[synthetic_level] = current_path
                elif is_numbered:
                    # This is a numbered heading - properly place it in the hierarchy
                    
                    # Find the appropriate parent level based on the numeric pattern
                    # For example, "3.2.1" has a level of 3, and its parent should be "3.2" with level 2
                    parent_level = numeric_level - 1
                    
                    # Get the parent path if it exists
                    parent_path = heading_by_level.get(parent_level, "")
                    
                    # Create the full breadcrumb path
                    current_path = f"{parent_path} > {item.text}" if parent_path else item.text
                    
                    # Store the breadcrumb
                    heading_by_level[numeric_level] = current_path
                    
                    # Remove any headings at deeper levels as they're now out of scope
                    keys_to_del = [k for k in heading_by_level if k > numeric_level]
                    for k in keys_to_del:
                        heading_by_level.pop(k, None)
                    
                    # Remember this heading for later unnumbered headings
                    last_significant_heading_level = numeric_level
                    last_significant_heading = item.text
                else:
                    # This is a regular non-numeric heading
                    # Handle it similar to numbered headings but use the document level
                    parent_level = doc_level - 1
                    parent_path = heading_by_level.get(parent_level, "")
                    current_path = f"{parent_path} > {item.text}" if parent_path else item.text
                    heading_by_level[doc_level] = current_path
                    
                    # Remove deeper headings
                    keys_to_del = [k for k in heading_by_level if k > doc_level]
                    for k in keys_to_del:
                        heading_by_level.pop(k, None)
                    
                    # Remember this as a significant heading
                    last_significant_heading_level = doc_level
                    last_significant_heading = item.text
                
                visited.add(item.self_ref) # Mark heading as visited
                continue # Process next item
            
            # --- 2. Get Current Breadcrumb Context --- 
            breadcrumb_path = None
            if heading_by_level:
                deepest_level = max(heading_by_level.keys())
                breadcrumb_path = heading_by_level.get(deepest_level)
            
            # --- 3. Handle Specific Item Types (Image, Table) --- 
            chunk_generated = False
            if isinstance(item, PictureItem):
                image_rel_path = _image_ref_map.get(item.self_ref)
                if image_rel_path:
                    caption_res = my_doc_ser.serialize_captions(item=item)
                    c = DocChunk(
                        text=caption_res.text or "",
                        meta=DocMeta(
                            doc_items=[item], headings=breadcrumb_path,
                            origin=dl_doc.origin, chunk_type="image",
                            image_path=image_rel_path
                        ),
                    )
                    yield c
                    visited.add(item.self_ref)
                    chunk_generated = True # Mark that we handled this item
                else:
                     _logger.warning(f"Image path not found in map for {item.self_ref}")
                     visited.add(item.self_ref) # Mark as visited even if path missing
                     chunk_generated = True # Prevent reprocessing
            
            elif isinstance(item, TableItem):
                caption_res = my_doc_ser.serialize_captions(item=item)
                table_content_ser = ChunkingDocSerializer(doc=dl_doc)
                table_text_res = table_content_ser.serialize(item=item, exclude_captions=True)
                combined_text = f"{caption_res.text}\n\n{table_text_res.text}" if caption_res.text else table_text_res.text
                
                c = DocChunk(
                    text=combined_text.strip(),
                    meta=DocMeta(
                        doc_items=[item], headings=breadcrumb_path,
                        origin=dl_doc.origin, chunk_type="table"
                    ),
                )
                yield c
                visited.add(item.self_ref)
                chunk_generated = True # Mark that we handled this item

            # --- 4. Handle General Text Content (if not already processed) --- 
            if not chunk_generated and isinstance(item, (OrderedList, UnorderedList, InlineGroup, DocItem)):
                # Serialize the item, importantly passing visited to prevent reprocessing parts of tables/images
                ser_res = my_doc_ser.serialize(item=item, visited=visited) 
                if ser_res.text:
                    chunk_doc_items = [span.item for span in ser_res.spans if hasattr(span, 'item')]
                    if chunk_doc_items:
                        c = DocChunk(
                           text=ser_res.text,
                           meta=DocMeta(
                               doc_items=chunk_doc_items, headings=breadcrumb_path,
                               origin=dl_doc.origin, chunk_type="text"
                           ),
                       )
                        yield c
                    # visited is updated within serialize
            elif not chunk_generated:
                # If it's not a heading, image, table, or standard text container, mark visited to avoid infinite loops? Or log?
                # For now, let's just ensure non-chunked items are marked visited if they weren't containers.
                 if not isinstance(item, (OrderedList, UnorderedList, InlineGroup)): # Avoid marking containers as fully visited yet
                      visited.add(item.self_ref) 