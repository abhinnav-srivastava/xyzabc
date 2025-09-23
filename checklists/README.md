# CodeCritique Checklists

This directory contains the checklist files for CodeCritique organized in two formats:

## Folder Structure

```
checklists/
├── excel/           # Excel source files (.xlsx)
│   ├── self/
│   ├── peer/
│   ├── techlead/
│   ├── fo/
│   └── architect/
└── markdown/        # Markdown files used by the application (.md)
    ├── self/
    ├── peer/
    ├── techlead/
    ├── fo/
    └── architect/
```

## Workflow

1. **Edit Excel Files**: Modify the Excel files in the `excel/` folder to update checklists
2. **Convert to Markdown**: Use the conversion script to generate markdown files
3. **Application Uses Markdown**: The CodeCritique application reads from the `markdown/` folder

## Converting Excel to Markdown

Use the conversion script to convert Excel files to markdown format:

```bash
# Convert all Excel files to markdown
python convert_excel_to_markdown.py --all

# Convert a specific file
python convert_excel_to_markdown.py --excel checklists/excel/self/correctness.xlsx

# Convert with custom output path
python convert_excel_to_markdown.py --excel checklists/excel/peer/style.xlsx --markdown checklists/markdown/peer/style.md
```

## Excel File Format

Each Excel file should have the following columns:

- **Item Text**: The main checklist item text
- **Item Type**: MUST, GOOD, or OPTIONAL
- **Details**: Semicolon-separated details (optional)
- **Description**: Additional description (optional)

## Sample Excel Content

| Item Text | Item Type | Details | Description |
|-----------|-----------|---------|-------------|
| Code compiles without errors or warnings (MUST) | MUST | All syntax errors resolved; Compiler warnings addressed; Dependencies properly configured | Ensure the code compiles cleanly without any errors or warnings |
| Handles edge cases and invalid inputs (GOOD) | GOOD | Empty inputs handled gracefully; Boundary conditions tested; Invalid data types rejected appropriately | Code should handle edge cases and invalid inputs gracefully |

## Roles and Categories

### Self Review
- **correctness**: Code correctness and error handling
- **readability**: Code readability and documentation
- **tests**: Test coverage and quality

### Peer Review
- **functionality**: Functional requirements and implementation
- **style**: Code style and naming conventions

### Tech Lead Review
- **design**: Design patterns and architecture
- **architecture**: System architecture and scalability

### FO Review
- **ops**: Operational readiness and deployment

### Architect Review
- **architecture**: Enterprise architecture principles

## Notes

- The application configuration (`config/roles.json`) points to the markdown files
- Excel files are the source of truth for checklist content
- Always run the conversion script after modifying Excel files
- The conversion script preserves the hierarchical structure of checklist items
