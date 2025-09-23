# Design Compliance Review

- Verify project structure is logically separated (MUST)
  - **Description:** Ensure the project is organized into distinct packages like model, view, fragment to maintain clear separation of concern as per design.
  - **Technical Details:** Follows SOLID principles
  - **How to Measure:** Run ArchUnit tests

- Check for proper dependency injection (MUST)
  - **Description:** Verify that dependencies are properly injected and not hard-coded, following dependency inversion principle.
  - **Technical Details:** Uses DI framework (Dagger/Hilt) correctly
  - **How to Measure:** Review dependency graph and check for circular dependencies

- Validate architectural patterns (MUST)
  - **Description:** Ensure the code follows established architectural patterns like MVP, MVVM, or Clean Architecture.
  - **Technical Details:** Implements chosen architecture consistently
  - **How to Measure:** Code review and static analysis tools

- Check for proper error handling (MUST)
  - **Description:** Verify that error handling is implemented consistently across the application with proper error boundaries.
  - **Technical Details:** Uses Result/Either pattern or proper exception handling
  - **How to Measure:** Test error scenarios and review error handling code
