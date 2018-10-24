@unit
Feature: command line processing

  Scenario: no arguments
    Given no arguments
    Then we exit with 2
    And we start printing error "usage: abaqus2dyna "

  Scenario: version
    Given arguments "--version"
    Then we exit with 0
    And we start printing "abaqus2dyna "

  Scenario: help
    Given arguments "--help"
    Then we exit with 0
    And we start printing "usage: abaqus2dyna "
    Given arguments "-h"
    Then we exit with 0

