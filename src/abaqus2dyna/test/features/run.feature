Feature: full test

  Scenario: example.inp
    Given example.inp
    When we convert it
    Then we expect an output file with 69722 lines

