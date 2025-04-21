Feature: Land Registry AI Agent for Property Analytics
  As a land registry analyst or property market researcher
  I want an AI assistant that can analyze transaction data by location and time
  So that I can gain insights into property market trends and make informed decisions

  Scenario: Retrieve all property transactions in a specific postcode
    Given the user requests property transactions for postcode "SW1A 1AA"
    When the AI agent queries the land registry database
    Then the agent should return a list of all transactions in that postcode
    And include property addresses, sale prices, and transaction dates

  Scenario: Calculate average property price by postcode and timeframe
    Given the user specifies postcode "N1 9GU" and timeframe "January 2022 to December 2022"
    When the AI agent analyzes the transaction data
    Then the agent should calculate and display the average property price
    And provide a breakdown by property type (detached, semi-detached, terraced, flat)

  Scenario: Generate price trend analysis for a location
    Given the user requests price trends for area "Manchester" over the past "5 years"
    When the AI agent processes historical transaction data
    Then the agent should generate a time-series analysis of price changes
    And identify significant market shifts with percentage increases or decreases

  Scenario: Compare property values across neighboring postcodes
    Given the user selects a primary postcode "BS1 4TR" and radius "3 miles"
    When the AI agent identifies neighboring postcodes within the radius
    Then the agent should compare average property values across all postcodes
    And highlight areas with highest appreciation rates over the last 12 months
