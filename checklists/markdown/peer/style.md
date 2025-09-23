# Code Review Checklist

- Follows project style guide and linters (MUST)
  - Check ktlint, detekt, or other project-specific linters
  - Verify code formatting matches team standards
  - Ensure naming conventions are consistent
  <!-- Code should pass all linting checks and follow style guidelines -->

- Consistent naming and file structure (GOOD)
  - Use descriptive variable and function names
  - Follow project directory structure conventions
  - Maintain consistent file naming patterns
  <!-- Naming and structure should be consistent throughout the codebase -->

- Avoids duplication; common logic extracted (GOOD)
  - Look for repeated code blocks
  - Extract common functionality into reusable functions
  - Use inheritance or composition appropriately
  <!-- Code should avoid duplication and promote reusability -->
