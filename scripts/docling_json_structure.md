Following is the structure of the provided DoclingDocument JSON schema version 1.3.0. This description follows the hierarchy of the JSON.

**Root Object:**

The JSON document itself is a single root object `{}`. It contains several top-level keys that describe the document's metadata, structure, and content.

1.  **`schema_name` (String):** Identifies the type of schema being used.
    *   Example: `"DoclingDocument"`

2.  **`version` (String):** Specifies the version number of the schema.
    *   Example: `"1.3.0"`

3.  **`name` (String):** A user-defined or generated name for this specific document instance.
    *   Example: `"SBW_AI sample page10-11"`

4.  **`origin` (Object):** Contains metadata about the original source file from which this JSON was generated.
    *   `mimetype` (String): The MIME type of the source file (e.g., `"application/pdf"`).
    *   `binary_hash` (Number): A hash value representing the binary content of the source file.
    *   `filename` (String): The original filename of the source document.

5.  **`furniture` (Object):** Represents the root node for elements considered "furniture" – content typically not part of the main document flow, like headers, footers, or page numbers.
    *   `self_ref` (String): A JSON Pointer reference to this object itself (e.g., `#/furniture`).
    *   `children` (Array): An array, often empty at this level. Furniture items are usually listed directly under `body` but identified by their `content_layer`.
    *   `content_layer` (String): Indicates the layer ("furniture").
    *   `name` (String): Name of the node (e.g., `_root_`).
    *   `label` (String): Semantic label (e.g., `unspecified`).

6.  **`body` (Object):** Represents the root node for the main content of the document.
    *   `self_ref` (String): A JSON Pointer reference to this object itself (e.g., `#/body`).
    *   `children` (Array): **Crucially**, this array defines the *ordered sequence* of the document's content elements. Each item in the array is an object containing a `$ref` key, which holds a JSON Pointer string referencing a specific element within the `texts`, `tables`, `pictures`, or `groups` arrays.
    *   `content_layer` (String): Indicates the layer ("body").
    *   `name` (String): Name of the node (e.g., `_root_`).
    *   `label` (String): Semantic label (e.g., `unspecified`).

7.  **`groups` (Array):** An array containing objects, where each object represents a logical grouping of other elements (like lists).
    *   Each **Group Object** has:
        *   `self_ref` (String): Reference to this specific group object (e.g., `#/groups/0`).
        *   `parent` (Object): An object with a `$ref` key pointing to the parent element (usually `#/body`).
        *   `children` (Array): An array of reference objects (`$ref`) pointing to the elements (usually `texts`) that belong to this group (e.g., the list items).
        *   `content_layer` (String): Layer ("body").
        *   `name` (String): Type of group (e.g., `"list"`).
        *   `label` (String): Semantic label (e.g., `"list"`).

8.  **`texts` (Array):** An array containing objects, where each object represents a block of text identified in the document.
    *   Each **Text Object** has:
        *   `self_ref` (String): Reference to this specific text object (e.g., `#/texts/1`).
        *   `parent` (Object): An object with a `$ref` pointing to the parent element (could be `#/body`, `#/groups/0`, `#/pictures/0`, etc.).
        *   `children` (Array): Usually empty for basic text blocks.
        *   `content_layer` (String): The layer this text belongs to ("body" or "furniture").
        *   `label` (String): **Important semantic classification** of the text block (e.g., `"text"`, `"section_header"`, `"list_item"`, `"page_header"`, `"page_footer"`).
        *   `prov` (Array): Provenance information. An array containing one or more objects detailing where this text block was found in the source document. Each provenance object contains:
            *   `page_no` (Number): The page number (1-based).
            *   `bbox` (Object): The bounding box coordinates (`l`, `t`, `r`, `b`) of the text on the page. Note the `coord_origin` (e.g., `"BOTTOMLEFT"`) indicating the coordinate system's origin.
            *   `charspan` (Array): A two-element array `[start, end]` indicating the character indices within the `orig` string covered by this specific provenance instance.
        *   `orig` (String): The original text extracted by OCR, potentially with noise.
        *   `text` (String): The potentially cleaned or normalized text content.
        *   `level` (Number, Optional): Indicates the hierarchical level, often used for `section_header`.
        *   `enumerated` (Boolean, Optional): For `list_item`, indicates if the list is enumerated (true) or bulleted (false).
        *   `marker` (String, Optional): For `list_item`, shows the marker character (e.g., `-`, `*`, `1.`).

9.  **`pictures` (Array):** An array containing objects, where each object represents an image or figure found in the document.
    *   Each **Picture Object** has:
        *   `self_ref` (String): Reference to this picture object (e.g., `#/pictures/0`).
        *   `parent` (Object): A `$ref` pointing to the parent (usually `#/body`).
        *   `children` (Array): Array of `$ref` objects pointing to `texts` elements that are considered *part of* the picture (e.g., text overlaid on the image during OCR).
        *   `content_layer` (String): Layer ("body").
        *   `label` (String): Semantic label ("picture").
        *   `prov` (Array): Provenance information (similar structure to `texts.prov`, `charspan` is often `[0, 0]`).
        *   `captions` (Array): Array of `$ref` objects pointing to `texts` elements identified as captions for this picture.
        *   `references` (Array): (Likely for cross-references, empty here).
        *   `footnotes` (Array): (Empty here).
        *   `image` (Object): Contains details about the image data.
            *   `mimetype` (String): Image format (e.g., `"image/png"`).
            *   `dpi` (Number): Dots per inch resolution.
            *   `size` (Object): Dimensions (`width`, `height`) in pixels.
            *   `uri` (String): The image data, often as a base64 encoded data URI.
        *   `annotations` (Array): (Empty here).

10. **`tables` (Array):** An array containing objects, where each object represents a table found in the document.
    *   Each **Table Object** has:
        *   `self_ref` (String): Reference to this table object (e.g., `#/tables/0`).
        *   `parent` (Object): A `$ref` pointing to the parent (usually `#/body`).
        *   `children` (Array): Usually empty. Table content is in the `data` field.
        *   `content_layer` (String): Layer ("body").
        *   `label` (String): Semantic label ("table").
        *   `prov` (Array): Provenance information for the *entire table's* bounding box (similar structure to `texts.prov`, `charspan` is often `[0, 0]`).
        *   `captions` (Array): Array of `$ref` objects pointing to `texts` elements identified as captions.
        *   `references` (Array): (Empty here).
        *   `footnotes` (Array): (Empty here).
        *   `data` (Object): Contains the structured data of the table cells.
            *   `table_cells` (Array): A flat list of all cell objects within the table. Each **Cell Object** contains:
                *   `bbox` (Object): Bounding box of the *cell*. Note: `coord_origin` here is typically `"TOPLEFT"`.
                *   `row_span` (Number): Number of rows spanned by the cell (1 if not spanned).
                *   `col_span` (Number): Number of columns spanned by the cell (1 if not spanned).
                *   `start_row_offset_idx`, `end_row_offset_idx` (Number): 0-based row index range (inclusive start, exclusive end).
                *   `start_col_offset_idx`, `end_col_offset_idx` (Number): 0-based column index range (inclusive start, exclusive end).
                *   `text` (String): Text content of the cell.
                *   `column_header`, `row_header`, `row_section` (Boolean): Flags indicating the semantic role of the cell (e.g., if it's a header).
            *   `num_rows` (Number): Total number of rows in the table grid.
            *   `num_cols` (Number): Total number of columns in the table grid.
            *   `grid` (Array): A 2D array (list of lists) representing the table's logical grid structure. Each element `grid[row][col]` contains the *cell object* that occupies or spans that grid position.

11. **`key_value_items` (Array):** An array intended to hold identified key-value pairs (e.g., from forms). Empty in this example.

12. **`form_items` (Array):** An array intended to hold identified form elements. Empty in this example.

13. **`pages` (Object):** An object where each key is a page number (as a string, e.g., `"1"`, `"2"`) and the value is an object describing that page.
    *   Each **Page Object** (e.g., `pages["1"]`) has:
        *   `size` (Object): Dimensions of the page (`width`, `height`) in points or pixels.
        *   `image` (Object): Information about the rendered image of the entire page (similar structure to `pictures.image`).
        *   `page_no` (Number): The page number (integer).

**Hierarchy Summary:**

*   The root contains metadata (`schema_name`, `version`, `name`, `origin`), structural roots (`furniture`, `body`), content arrays (`groups`, `texts`, `pictures`, `tables`, `key_value_items`, `form_items`), and page descriptions (`pages`).
*   The `body.children` array dictates the flow/order of content by referencing items in the content arrays.
*   `groups`, `texts`, `pictures`, and `tables` store the actual content elements, each with provenance (`prov`) linking back to the source page and location.
*   Labels (`label`) within content elements provide semantic meaning (header, footer, list item, paragraph, etc.).
*   Tables have a nested `data` structure containing `table_cells` and a `grid` representation.
*   References (`$ref`) are used extensively to link related parts (parent-child, group items, body sequence).

This structure allows for representing both the sequential flow and the semantic classification of document elements, along with their source location and associated data (like images or table cells).