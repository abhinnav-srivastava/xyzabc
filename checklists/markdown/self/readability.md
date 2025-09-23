# Readability Review

- Verify code is well-commented and self-documenting (MUST)
  - **Description:** Ensure complex logic is explained, function purposes are documented, and business rules are clarified for future maintainers.
  - **Technical Details:** Code should be easy to understand for future maintainers
  - **How to Measure:** Code review and documentation analysis

- Check variable and function names are descriptive (MUST)
  - **Description:** Ensure all variable and function names reflect their purpose, avoid abbreviations, and follow consistent naming conventions.
  - **Technical Details:** All identifiers should clearly indicate their purpose
  - **How to Measure:** Code review and static analysis tools

- Verify functions are focused and not too long (MUST)
  - **Description:** Ensure functions follow single responsibility principle, have reasonable length, and have clear input/output.
  - **Technical Details:** Functions should be focused on a single task
  - **How to Measure:** Code metrics analysis and review

- Check code formatting follows project standards (MUST)
  - **Description:** Ensure consistent indentation, proper spacing, and line length limits are respected according to project standards.
  - **Technical Details:** Code should be consistently formatted according to project standards
  - **How to Measure:** Run formatter and check for violations
