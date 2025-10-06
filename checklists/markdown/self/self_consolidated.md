# Self Review

## Code Correctness

- **MUST:** Variable Naming
  - **How to Measure:** Variables should have meaningful names that describe their purpose
  - **How to Measure:** Review variable names for clarity and purpose
  - **Rule Reference:** CLEAN-001
  - **Additional Info:** Use camelCase for variables

- **GOOD:** Function Length
  - **How to Measure:** Functions should be concise and focused on a single responsibility
  - **How to Measure:** Count lines of code in functions
  - **Rule Reference:** CLEAN-002
  - **Additional Info:** Maximum 50 lines per function

- **MUST:** Error Handling
  - **How to Measure:** Proper error handling should be implemented
  - **How to Measure:** Check for try-catch blocks and error messages
  - **Rule Reference:** CLEAN-003
  - **Additional Info:** Use specific exception types

## Correctness Review

- **GOOD:** Verify code compiles without errors
  - **How to Measure:** Ensure the code compiles cleanly without any compilation errors or warnings.
  - **How to Measure:** Build the project and check for compilation errors

- **GOOD:** Check for runtime exceptions
  - **How to Measure:** Verify that common user paths don't throw unexpected runtime exceptions.
  - **How to Measure:** Test main user flows and edge cases

- **GOOD:** Validate input handling
  - **How to Measure:** Ensure the code properly handles edge cases and invalid inputs gracefully.
  - **How to Measure:** Test with invalid inputs and boundary conditions

## Maintainability Review

- **GOOD:** Check for runtime exceptions
  - **How to Measure:** Ensure the code compiles cleanly without any compilation errors or warnings.
  - **How to Measure:** Build the project and check for compilation errors

- **GOOD:** Verify code compiles without errors
  - **How to Measure:** Verify that common user paths don't throw unexpected runtime exceptions.
  - **How to Measure:** Test main user flows and edge cases

- **GOOD:** Validate input handling
  - **How to Measure:** Ensure the code properly handles edge cases and invalid inputs gracefully.
  - **How to Measure:** Test with invalid inputs and boundary conditions

## Readability Review

- **GOOD:** Verify code is well-commented and self-documenting
  - **How to Measure:** Ensure complex logic is explained, function purposes are documented, and business rules are clarified for future maintainers.
  - **How to Measure:** Code review and documentation analysis

- **GOOD:** Check variable and function names are descriptive
  - **How to Measure:** Ensure all variable and function names reflect their purpose, avoid abbreviations, and follow consistent naming conventions.
  - **How to Measure:** Code review and static analysis tools

- **GOOD:** Verify functions are focused and not too long
  - **How to Measure:** Ensure functions follow single responsibility principle, have reasonable length, and have clear input/output.
  - **How to Measure:** Code metrics analysis and review

- **GOOD:** Check code formatting follows project standards
  - **How to Measure:** Ensure consistent indentation, proper spacing, and line length limits are respected according to project standards.
  - **How to Measure:** Run formatter and check for violations

## Test Review

- **GOOD:** Verify unit tests cover critical business logic
  - **How to Measure:** Ensure core algorithms are tested, edge cases are covered, and test data is realistic for essential business logic.
  - **How to Measure:** Test coverage analysis and code review

- **GOOD:** Check integration tests verify component interactions
  - **How to Measure:** Ensure API endpoints are tested, database interactions are verified, and external service mocks are properly implemented.
  - **How to Measure:** Run integration test suite and review test results

- **GOOD:** Verify test coverage meets project requirements
  - **How to Measure:** Ensure minimum coverage threshold is met, critical paths are covered, and coverage reports are reviewed.
  - **How to Measure:** Generate and review coverage reports
