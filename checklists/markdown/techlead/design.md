# Design

- **RECOMMENDED:** Ensure the project is organized into distinct packages like model, view, fragment to maintain clear separation of concern as per design.
  - **How to Measure:** Run ArchUnit tests

- **RECOMMENDED:** Verify that dependencies are properly injected and not hard-coded, following dependency inversion principle.
  - **How to Measure:** Review dependency graph and check for circular dependencies

- **RECOMMENDED:** Ensure the code follows established architectural patterns like MVP, MVVM, or Clean Architecture.
  - **How to Measure:** Code review and static analysis tools

- **RECOMMENDED:** Verify that error handling is implemented consistently across the application with proper error boundaries.
  - **How to Measure:** Test error scenarios and review error handling code

