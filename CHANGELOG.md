# Wit4java Changelog



## Wit4java 3.0
This release had alot of changes surrounding the design of wit4java internally,
as well as repository structure.
- Implemented validation of `String` types.
- Removed mockito dependency to mediate complex static mocking cases.
- Codebase refactor to aid readability and maintainability.
- CI/CD pipeline configured.
## Wit4java 2.0
This release involved improving the validation ability to deal with programs dealing
with iteration and recursion based programs. 
- Added static mocking of `Verifier` class to return multiple values at a given position.
## Wit4java 1.0
This was the first stable iteration of wit4java. It involved extracting witness values
and creating a new program by directly baking values into the code to create a new program.
- Implemented the validation of primitive types in iteration and recursion free programs.