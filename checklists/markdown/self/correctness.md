# Code Review Checklist

- Code compiles without errors or warnings (MUST)
  - All syntax errors resolved
  - Compiler warnings addressed
  - Dependencies properly configured
  <!-- Ensure the code compiles cleanly without any errors or warnings -->

- No obvious runtime exceptions in common paths (MUST)
  - Test main user flows
  - Verify error handling works correctly
  - Check for null pointer exceptions
  <!-- Verify that common user paths don't throw unexpected exceptions -->

- Handles edge cases and invalid inputs (GOOD)
  - Empty inputs handled gracefully
  - Boundary conditions tested
  - Invalid data types rejected appropriately
  <!-- Code should handle edge cases and invalid inputs gracefully -->

- Follows language and project standards for error handling (GOOD)
  - Use appropriate exception types
  - Provide meaningful error messages
  - Log errors appropriately
  <!-- Error handling should follow established patterns and standards -->

- No hard-coded secrets or credentials (MUST)
  - API keys in environment variables
  - Database credentials in config files
  - No passwords in source code
  <!-- All sensitive information should be externalized and not hard-coded -->
